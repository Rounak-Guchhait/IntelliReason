from __future__ import annotations

import json
import logging
import queue
import threading

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.api.schemas import (
    HealthResponse,
    IngestResponse,
    KnowledgeListResponse,
    ReasonRequest,
)
from app.config import get_settings
from app.reasoning.engine import ReasoningEngine
from app.reasoning.models import ReasonResponse
from app.vectorstore.store import get_vector_store, ingest_directory

logger = logging.getLogger(__name__)

router = APIRouter()

_engine: ReasoningEngine | None = None


def get_engine() -> ReasoningEngine:
    global _engine
    if _engine is None:
        _engine = ReasoningEngine()
    return _engine


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health() -> HealthResponse:
    s = get_settings()
    return HealthResponse(
        status="ok",
        app=s.app_name,
        environment=s.app_env,
        provider=s.llm_provider,
        model=s.llm_model,
        vector_store=s.vector_store,
        code_engine=s.code_engine,
    )


@router.post("/reason", response_model=ReasonResponse, tags=["reasoning"])
def reason(request: ReasonRequest) -> ReasonResponse:
    """Run the full reasoning pipeline and return the structured result."""
    try:
        return get_engine().reason(
            request.question, history=[m.model_dump() for m in request.history]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Reasoning failed")
        raise HTTPException(status_code=502, detail=f"Reasoning failed: {exc}") from exc


@router.post("/stream-reason", tags=["reasoning"])
def stream_reason(request: ReasonRequest) -> StreamingResponse:
    """Stream the reasoning pipeline as Server-Sent Events.

    Event payloads (JSON under `data:`):
      start, plan, plan_error, step_start, step_done, step_error,
      verification, done, error
    """
    try:
        engine = get_engine()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Engine init failed: {exc}") from exc

    incoming = [m.model_dump() for m in request.history]
    events: queue.Queue = queue.Queue()

    def emit(event: dict) -> None:
        events.put(event)

    def run_pipeline() -> None:
        try:
            engine.reason(request.question, history=incoming, emit=emit)
        except Exception as exc:
            logger.exception("Streaming reasoning failed")
            events.put({"type": "error", "error": str(exc)})
        finally:
            events.put(None)

    def event_stream():
        handler = threading.Thread(target=run_pipeline, daemon=True)
        handler.start()
        while True:
            event = events.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False, default=str)}\n\n"
            if event.get("type") == "done":
                continue  # let the thread terminate naturally
        handler.join()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/knowledge", response_model=KnowledgeListResponse, tags=["knowledge"])
def list_knowledge() -> KnowledgeListResponse:
    store = get_vector_store()
    docs = store.list_docs()
    return KnowledgeListResponse(count=len(docs), documents=docs)


@router.post("/knowledge/ingest", response_model=IngestResponse, tags=["knowledge"])
def ingest_knowledge() -> IngestResponse:
    """Re-scan the INGESTION_DIR and index new/updated documents."""
    added = ingest_directory()
    return IngestResponse(ingested=added)