from __future__ import annotations

import json
import logging
import os

logger = logging.getLogger(__name__)

from .base import BaseVectorStore, SearchResult, embed


class InMemoryVectorStore(BaseVectorStore):
    """Local, file-backed vector store. The default for development and
    the Render free tier (no external database needed)."""

    def __init__(self, persist_path: str | None = None):
        self._docs: dict[str, dict] = {}
        self._vecs: dict[str, list[float]] = {}
        self._persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            try:
                with open(persist_path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                for doc in data.get("documents", []):
                    self._docs[doc["id"]] = {
                        "text": doc["text"],
                        "metadata": doc.get("metadata", {}),
                    }
                    self._vecs[doc["id"]] = embed(doc["text"])
            except Exception as exc:  # noqa: BLE001
                logger.debug("Could not load persisted vector store: %s", exc)

    def _save(self) -> None:
        if not self._persist_path:
            return
        os.makedirs(os.path.dirname(self._persist_path) or ".", exist_ok=True)
        payload = {
            "documents": [
                {"id": did, "text": d["text"], "metadata": d.get("metadata", {})}
                for did, d in self._docs.items()
            ]
        }
        with open(self._persist_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)

    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._docs.setdefault(doc_id, {"text": text, "metadata": metadata or {}})
        self._vecs.setdefault(doc_id, embed(text))
        self._save()

    def upsert(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self._docs[doc_id] = {"text": text, "metadata": metadata or {}}
        self._vecs[doc_id] = embed(text)
        self._save()

    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        qv = embed(query)
        ranked = sorted(
            (
                SearchResult(
                    id=did,
                    text=d["text"],
                    metadata=d.get("metadata", {}),
                    score=sum(a * b for a, b in zip(qv, self._vecs[did])),
                )
                for did, d in self._docs.items()
                if self._vecs.get(did)
            ),
            key=lambda r: r.score,
            reverse=True,
        )
        return ranked[:k]

    def list_docs(self) -> list[dict]:
        return [
            {"id": did, "metadata": d.get("metadata", {}), "preview": d["text"][:120]}
            for did, d in self._docs.items()
        ]