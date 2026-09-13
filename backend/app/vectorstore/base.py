from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)
    score: float = 0.0


class BaseVectorStore(ABC):
    @abstractmethod
    def add(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        """Index a document under a stable id."""

    @abstractmethod
    def upsert(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        """Index a document, replacing any existing version of doc_id."""

    @abstractmethod
    def search(self, query: str, k: int = 3) -> list[SearchResult]:
        """Return top-k documents most relevant to the query."""

    @abstractmethod
    def list_docs(self) -> list[dict]:
        """Return all indexed documents (id + metadata)."""


def embed(text: str, dim: int = 256, n: int = 3) -> list[float]:
    """Deterministic local text embedding using hashed character n-grams.

    Cheap, dependency-free and good enough for small knowledge bases.
    Production deployments can swap this for a real embedding model by
    plugging the pgvector adapter with a proper embedding provider.
    """
    import math

    vec = [0.0] * dim
    t = " ".join(text.lower().split())
    if t:
        for i in range(len(t) - n + 1):
            gram = t[i : i + n]
            h = int(gram.encode().hex(), 16) % dim
            vec[h] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
    return vec


def cosine_similarity(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))