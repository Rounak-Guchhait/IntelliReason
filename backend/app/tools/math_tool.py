from __future__ import annotations

import re

import sympy as sp
from langchain_core.tools import tool


def _namespace() -> dict:
    ns = {name: getattr(sp, name) for name in dir(sp) if not name.startswith("_")}
    symbols = sp.symbols("x y z t a b c n")
    ns.update({str(s): s for s in symbols})
    return ns


@tool
def symbolic_math(call: str) -> str:
    """Run a SymPy symbolic math operation and return its result.

    Provide a function call using bare symbols (x, y, z, t, a, b, c, n —
    no quotes needed). Examples:
      - simplify(x**2 + 2*x + 1)
      - expand((x + 1)**3)
      - factor(x**2 - 9)
      - solve(x**2 - 4, x)
      - diff(x**3 - x, x)
      - integrate(x**2, x)
      - limit(sin(x)/x, x, 0)
      - evalf(pi)
    Return the symbolic result as a string. Only symbolic math is allowed."""
    m = re.match(r"\s*([A-Za-z_]\w*)\s*\((.*)\)\s*$", call.strip(), re.DOTALL)
    if not m:
        return "ERROR: expected format like: solve(x**2 - 4, x)"
    name, argstr = m.group(1), m.group(2)
    func = getattr(sp, name, None)
    if func is None:
        return f"ERROR: unknown SymPy function {name!r}"
    ns = _namespace()
    try:
        args = eval(argstr, {"__builtins__": {}}, ns)
        if not isinstance(args, tuple):
            args = (args,)
        return str(func(*args))
    except Exception as e:  # noqa: BLE001
        return f"ERROR: {e}"