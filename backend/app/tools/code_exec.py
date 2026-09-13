from __future__ import annotations

import httpx
from langchain_core.tools import tool

from app.config import get_settings


@tool
def run_python_code(code: str) -> str:
    """Execute Python 3 code inside a remote, sandboxed environment and return
    its stdout/stderr output. Use this tool whenever the problem needs actual
    computation: arithmetic, algebra verification, simulations, data analysis,
    or generating numeric results. Write plain Python that prints its result."""
    settings = get_settings()
    engine = settings.code_engine.lower().strip()

    if engine == "judge0" and settings.judge0_url:
        return _run_judge0(code, settings)
    return _run_piston(code, settings)


def _run_piston(code: str, settings) -> str:
    url = settings.piston_url.rstrip("/") + "/execute"
    payload = {
        "language": "python",
        "version": "3.10.0",
        "files": [{"name": "main.py", "content": code}],
    }
    try:
        resp = httpx.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        run = data.get("run") or {}
        comp = data.get("compile") or {}
        parts = []
        if comp.get("stderr"):
            parts.append(f"COMPILE_STDERR:\n{comp['stderr']}")
        if run.get("output"):
            parts.append(f"STDOUT:\n{run['output']}")
        if run.get("stderr"):
            parts.append(f"STDERR:\n{run['stderr']}")
        if not parts:
            parts.append("(no output produced)")
        return "\n\n".join(parts)
    except Exception as e:  # noqa: BLE001
        return f"ERROR: could not reach the code sandbox: {e}"


def _run_judge0(code: str, settings) -> str:
    url = settings.judge0_url.rstrip("/") + "/submissions?base64_encoded=false&wait=true"
    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": settings.judge0_api_key or "",
        "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com",
    }
    payload = {"language_id": 71, "source_code": code, "stdin": ""}
    try:
        resp = httpx.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        out = data.get("stdout") or ""
        err = data.get("stderr") or ""
        status = (data.get("status") or {}).get("description", "?")
        parts = [f"STATUS: {status}"]
        if out:
            parts.append(f"STDOUT:\n{out}")
        if err:
            parts.append(f"STDERR:\n{err}")
        return "\n\n".join(parts)
    except Exception as e:  # noqa: BLE001
        return f"ERROR: could not reach Judge0: {e}"