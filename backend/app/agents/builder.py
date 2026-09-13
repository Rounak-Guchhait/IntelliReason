from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool


def build_solver_agent(
    llm: BaseChatModel, tools: list[BaseTool], system_prompt: str
) -> Any:
    """Build a LangGraph-backed ReAct agent (LangChain 1.x `create_agent`).

    The agent decides when to call a tool, observes the sandboxed tool output,
    and continues reasoning until it produces a final answer.
    """
    return create_agent(
        llm,
        tools,
        system_prompt=system_prompt,
    )