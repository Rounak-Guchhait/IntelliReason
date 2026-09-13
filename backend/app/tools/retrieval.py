from __future__ import annotations

from langchain_core.tools import tool

from app.vectorstore.store import get_vector_store


@tool
def search_knowledge_base(query: str, k: int = 3) -> str:
    """Search the loaded knowledge base for passages relevant to the query.
    Use this when the question references documents, courses, articles or
    notes that were uploaded into the system. Returns up to k passages."""
    try:
        store = get_vector_store()
    except Exception:  # noqa: BLE001
        return "Knowledge base is not available."
    results = store.search(query, k=k)
    if not results:
        return "No relevant knowledge found in the knowledge base."
    return "\n\n".join(
        f"[{r.id} | score={r.score:.3f}]\n{r.text}" for r in results
    )