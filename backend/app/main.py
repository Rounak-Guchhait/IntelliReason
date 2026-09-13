import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.config import get_settings
from app.vectorstore.store import ingest_directory

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("intellireason")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        added = ingest_directory()
        if added:
            logger.info("Preloaded %s knowledge document(s)", added)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Knowledge preload skipped: %s", exc)
    logger.info(
        "IntelliReason up | provider=%s model=%s vector_store=%s",
        settings.llm_provider,
        settings.llm_model,
        settings.vector_store,
    )
    yield


app = FastAPI(
    title="IntelliReason API",
    description="An AI-powered smart reasoning system that decomposes problems, "
    "solves them step-by-step with tools, verifies and explains.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/", tags=["meta"])
def root():
    return {
        "name": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "reason": "/api/reason",
        "stream": "/api/stream-reason",
    }