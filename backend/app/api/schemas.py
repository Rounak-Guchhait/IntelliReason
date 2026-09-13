from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ReasonRequest(BaseModel):
    question: str = Field(min_length=1, description="The problem to reason about")
    history: list[ChatMessage] = Field(
        default_factory=list, description="Optional prior conversation turns"
    )


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    provider: str
    model: str
    vector_store: str
    code_engine: str


class KnowledgeListResponse(BaseModel):
    count: int
    documents: list[dict]


class IngestResponse(BaseModel):
    ingested: int


StreamEvent = dict