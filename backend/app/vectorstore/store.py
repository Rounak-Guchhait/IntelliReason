from functools import lru_cache

from app.config import get_settings

from .base import BaseVectorStore
from .memory import InMemoryVectorStore
from .pgvector import PgVectorStore


@lru_cache
def get_vector_store() -> BaseVectorStore:
    """Return the configured vector store (singleton per process)."""
    settings = get_settings()
    kind = settings.vector_store.lower().strip()

    if kind == "pgvector":
        if not settings.database_url:
            raise ValueError("VECTOR_STORE=pgvector requires DATABASE_URL to be set")
        return PgVectorStore(settings.database_url)

    return InMemoryVectorStore(
        persist_path=".vector-store/knowledge.json"
        if settings.app_env != "test"
        else None
    )


def ingest_directory(path: str | None = None) -> int:
    """Read all .txt/.md files under the ingestion directory into the store."""
    settings = get_settings()
    root = path or settings.ingestion_dir
    store = get_vector_store()
    count = 0
    import os

    if not os.path.isdir(root):
        return 0
    for fname in sorted(os.listdir(root)):
        if not fname.endswith((".txt", ".md")):
            continue
        with open(os.path.join(root, fname), "r", encoding="utf-8") as fh:
            text = fh.read().strip()
        if not text:
            continue
        store.upsert(fname, text, {"source": root, "file": fname})
        count += 1
    return count