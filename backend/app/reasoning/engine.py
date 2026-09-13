from __future__ import annotations

import logging
import time
from collections.abc import Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from app.config import Settings, get_settings
from app.llm.client import create_llm
from app.llm.structured import invoke_structured
from app.reasoning.models import (
    FinalAnswer,
    Plan,
    PlanStep,
    ReasoningStep,
    ReasonResponse,
    ToolCallInfo,
    Verification,
    VerificationSchema,
)
from app.reasoning.prompts import (
    FINALIZER_SYSTEM_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    SOLVER_SYSTEM_PROMPT,
    VERIFIER_SYSTEM_PROMPT,
    format_history,
)
from app.tools.registry import build_tools

logger = logging.getLogger(__name__)

Emitter = Callable[[dict], None]


def _noop_emit(event: dict) -> None:  # pragma: no cover - trivial
    pass


class ReasoningEngine:
    """Orchestrates the decompose -> solve -> verify -> synthesize pipeline."""

    def __init__(self, settings: Settings | None = None, preload_knowledge: bool = True):
        self.settings = settings or get_settings()
        self.llm = create_llm(self.settings)
        self.tools = build_tools()
        self._solver = None
        self._history: list[dict] = []

        if preload_knowledge:
            self._preload_knowledge()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def reason(
        self,
        question: str,
        history: list[dict] | None = None,
        emit: Emitter | None = None,
    ) -> ReasonResponse:
        emit = emit or _noop_emit
        question = question.strip()
        if not question:
            raise ValueError("Empty question")

        started = time.monotonic()
        emit({"type": "start", "message": "Decomposing the problem into logical steps..."})

        recorded_history = list(history or self._history)
        hist_text = format_history(recorded_history)

        try:
            plan = self._plan(question, hist_text)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Planning failed: %s", exc)
            emit({"type": "plan_error", "error": str(exc)})
            plan = []

        steps_out: list[ReasoningStep] = []
        for idx, step in enumerate(plan):
            emit({"type": "step_start", "index": idx, "step": step.model_dump()})
            try:
                solution, tool_calls = self._solve_step(question, plan, idx, hist_text)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Solver failed on step %s: %s", step.id, exc)
                solution = f"(solver error: {exc})"
                tool_calls = []
                emit({"type": "step_error", "index": idx, "error": str(exc)})
            out = ReasoningStep(
                id=step.id or f"step_{idx + 1}",
                description=step.description,
                solution=solution,
                tool_calls=tool_calls,
            )
            steps_out.append(out)
            emit({"type": "step_done", "index": idx, "step": out.model_dump()})

        verification = self._verify(question, steps_out, hist_text)
        final = self._finalize(question, steps_out, verification, hist_text)

        duration_ms = int((time.monotonic() - started) * 1000)
        result = ReasonResponse(
            problem=question,
            steps=steps_out,
            verification=verification,
            final_answer=final.final_answer,
            explanation=final.explanation,
            model=self.settings.llm_model,
            duration_ms=duration_ms,
        )
        emit({"type": "done", "result": result.model_dump()})
        self._history = list(recorded_history)
        return result

    # ------------------------------------------------------------------
    # Pipeline stages
    # ------------------------------------------------------------------
    def _plan(self, question: str, hist_text: str) -> list[PlanStep]:
        user_content = f"Problem:\n{question}\n"
        if hist_text:
            user_content += "\nConversation so far:\n" + hist_text
        user_content += f"\nDefine at most {self.settings.max_steps} steps."
        plan: Plan = invoke_structured(
            self.llm,
            Plan,
            [SystemMessage(PLANNER_SYSTEM_PROMPT), HumanMessage(user_content)],
        )
        return (plan.steps or [])[: self.settings.max_steps]

    def _solve_step(
        self,
        question: str,
        plan: list[PlanStep],
        idx: int,
        hist_text: str,
    ) -> tuple[str, list[ToolCallInfo]]:
        context = self._build_step_context(question, plan, idx, hist_text)
        agent = self._solver_agent()
        try:
            result = agent.invoke({"messages": [HumanMessage(context)]})
        except Exception:  # noqa: BLE001
            # Fallback: answer the step without tool orchestration.
            result = {"messages": [self.llm.invoke([HumanMessage(context)])]}

        solution, tool_calls = self._extract_agent_result(result, idx)
        return solution, tool_calls

    def _verify(
        self,
        question: str,
        steps_out: list[ReasoningStep],
        hist_text: str,
    ) -> Verification:
        block = self._steps_block(question, steps_out, hist_text)
        verifier = invoke_structured(
            self.llm,
            VerificationSchema,
            [SystemMessage(VERIFIER_SYSTEM_PROMPT), HumanMessage(block)],
        )
        return Verification(verdict=verifier.verdict, notes=verifier.notes)

    def _finalize(
        self,
        question: str,
        steps_out: list[ReasoningStep],
        verification: Verification,
        hist_text: str,
    ) -> FinalAnswer:
        block = self._steps_block(question, steps_out, hist_text)
        block += (
            "\n\nVERIFIER REPORT:\n"
            f"verdict={verification.verdict}\nnotes=" + "; ".join(verification.notes)
        )
        final: FinalAnswer = invoke_structured(
            self.llm,
            FinalAnswer,
            [SystemMessage(FINALIZER_SYSTEM_PROMPT), HumanMessage(block)],
        )
        return final

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _solver_agent(self):
        if self._solver is None:
            from app.agents.builder import build_solver_agent

            self._solver = build_solver_agent(
                self.llm, self.tools, SOLVER_SYSTEM_PROMPT
            )
        return self._solver

    def _build_step_context(
        self,
        question: str,
        plan: list[PlanStep],
        idx: int,
        hist_text: str,
    ) -> str:
        step = plan[idx]
        prior = plan[:idx]
        lines = [
            f"ORIGINAL PROBLEM:\n{question}",
        ]
        if hist_text:
            lines.append(f"\nCONVERSATION SO FAR:\n{hist_text}")
        lines.append("\nPLAN:")
        for i, p in enumerate(plan):
            marker = "->" if i == idx else "  "
            lines.append(f"{marker} {p.id}. {p.description}")
        if prior:
            lines.append(
                "\nPREVIOUS STEPS (already solved — rely on these, do not redo them):\n"
                + "\n".join(f"- {p.id}: {p.description}" for p in prior)
            )
        lines.append(
            f"\nYOUR TASK — solve step {step.id}: \"{step.description}\"\n"
            "Show your reasoning, use tools where needed, and state the result for this step only."
        )
        return "\n".join(lines)

    @staticmethod
    def _extract_agent_result(result, idx: int) -> tuple[str, list[ToolCallInfo]]:
        messages = result.get("messages", []) if isinstance(result, dict) else []
        final_answer = ""
        tool_calls: list[ToolCallInfo] = []
        tool_outputs: dict[str, str] = {}

        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_outputs[msg.name] = str(msg.content)

        for msg in messages:
            if isinstance(msg, AIMessage):
                for tc in msg.tool_calls:
                    args = tc.get("args")
                    if isinstance(args, str):
                        import json as _json

                        try:
                            args = _json.loads(args)
                        except Exception:  # noqa: BLE001
                            args = {"raw": args}
                    tool_calls.append(
                        ToolCallInfo(
                            name=tc.get("name", ""),
                            args=args,
                            output=tool_outputs.get(tc.get("name", "")),
                        )
                    )
                if msg.content:
                    final_answer = msg.content

        if not final_answer:
            final_answer = "(no explicit answer produced)"
        return final_answer, tool_calls

    @staticmethod
    def _steps_block(
        question: str,
        steps_out: list[ReasoningStep],
        hist_text: str,
    ) -> str:
        lines = [f"PROBLEM:\n{question}"]
        if hist_text:
            lines.append(f"\nCONVERSATION SO FAR:\n{hist_text}")
        lines.append("\nSTEP-BY-STEP SOLUTION:")
        for step in steps_out:
            lines.append(f"\n### {step.id} — {step.description}")
            lines.append(step.solution)
            for tc in step.tool_calls:
                lines.append(f"\n[tool] {tc.name} -> {tc.output or '(no output)'}")
        return "\n".join(lines)

    def _preload_knowledge(self) -> None:
        try:
            from app.vectorstore.store import ingest_directory

            added = ingest_directory()
            if added:
                logger.info("Ingested %d knowledge document(s)", added)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Knowledge preload skipped: %s", exc)