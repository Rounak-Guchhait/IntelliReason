from __future__ import annotations

from langchain_core.tools import BaseTool

from app.tools.code_exec import run_python_code
from app.tools.math_tool import symbolic_math
from app.tools.retrieval import search_knowledge_base


def build_tools() -> list[BaseTool]:
    """The tool set made available to the reasoning agents."""
    return [run_python_code, symbolic_math, search_knowledge_base]