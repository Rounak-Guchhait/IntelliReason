import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.vectorstore.base import embed
from app.vectorstore.memory import InMemoryVectorStore


def test_embed_is_deterministic_and_normalized():
    v1 = embed("hello world")
    v2 = embed("hello world")
    assert v1 == v2
    norm = (sum(x * x for x in v1)) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_inmemory_store_roundtrip():
    store = InMemoryVectorStore()
    store.add("a", "The quick brown fox jumps over the lazy dog.")
    store.add("b", "SymPy integrates and differentiates symbolic expressions.")

    hits = store.search("symbolic differentiation", k=1)
    assert hits
    assert hits[0].id == "b"
    assert store.list_docs()
    store.upsert("a", "Totally different content about rockets.")
    hits2 = store.search("symbolic differentiation", k=1)
    assert hits2[0].id == "b"