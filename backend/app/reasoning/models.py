from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str = Field(description="Short identifier, e.g. 'step_1'")
    description: str = Field(description="What this step must compute or establish")
    expected_outcome: str = Field(
        default="", description="What a correct solution to this step looks like"
    )


class Plan(BaseModel):
    steps: list[PlanStep]


class VerificationSchema(BaseModel):
    verdict: Literal["correct", "needs_review", "incorrect"]
    notes: list[str] = []


class FinalAnswer(BaseModel):
    final_answer: str
    explanation: str


class ToolCallInfo(BaseModel):
    name: str = ""
    args: dict | None = None
    output: str | None = None


class ReasoningStep(BaseModel):
    id: str
    description: str
    solution: str = ""
    tool_calls: list[ToolCallInfo] = []
    confidence: float | None = None


class Verification(BaseModel):
    verdict: Literal["correct", "needs_review", "incorrect"]
    notes: list[str] = []


class ReasonResponse(BaseModel):
    problem: str
    steps: list[ReasoningStep]
    verification: Verification
    final_answer: str
    explanation: str
    model: str
    duration_ms: int