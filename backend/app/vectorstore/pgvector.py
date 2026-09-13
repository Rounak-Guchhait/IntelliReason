from __future__ import annotations

from .base import BaseVectorStore, SearchResult, embed

DDL = """
CREATE TABLE IF NOT EXISTS ir_knowledge (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}',
    embedding vector(256)
);
CREATE INDEX IF NOT EXISTS ir_knowledge_embedding_idx
    ON ir_knowledge USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""


class PgVectorStore(BaseVectorStore):
    """Postgres + pgvector adapter. Use e.g. Supabase's free tier.

    Requires the `pgvector` extension to be enabled in the database
    (Supabase has it enabled by default) and DATABASE_URL set.
    """

    def __init__(self, database_url: str):
        import psycopg

        self._url = database_url
        self._conn = psycopg.connect(database_url, autocommit=True)
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(DDL)

    def _execute(self, sql: str, params: tuple = ()) -> None:
        with self._conn.cursor() as cur:
            cur.execute(sql, params)

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._execute(
            "INSERT INTO ir_knowledge (id, content, metadata, embedding) "
            "VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING",
            (doc_id, text, metadata or {}, embed(text)),
        )

    def upsert(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._execute(
            "INSERT INTO ir_knowledge (id, content, metadata, embedding) "
            "VALUES (%s, %s, %s, %s) "
            "ON CONFLICT (id) DO UPDATE SET content=EXCLUDED.content, "
            "metadata=EXCLUDED.metadata, embedding=EXCLUDED.embedding",
            (doc_id, text, metadata or {}, embed(text)),
        )

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT id, content, metadata, 1 - (embedding <=> %s) AS score "
                "FROM ir_knowledge ORDER BY embedding <=> %s LIMIT %s",
                (embed(query), embed(query), k),
            )
            rows = cur.fetchall()
        return [
            SearchResult(id=r[0], text=r[1], metadata=r[2] or {}, score=float(r[3]))
            for r in rows
        ]

    def list_docs(self) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute("SELECT id, metadata, content FROM ir_knowledge")
            rows = cur.fetchall()
        return [
            {"id": r[0], "metadata": r[1] or {}, "preview": (r[2] or "")[:120]}
            for r in rows
        ]