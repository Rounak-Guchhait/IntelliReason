import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tools.math_tool import symbolic_math


def test_solve_quadratic():
    assert "2" in symbolic_math.invoke("solve(x**2 - 4, x)")
    assert "-2" in symbolic_math.invoke("solve(x**2 - 4, x)")


def test_expand():
    assert "x**2" in symbolic_math.invoke("expand((x + 1)**2)")


def test_integrate():
    out = symbolic_math.invoke("integrate(x**2, x)")
    assert "x**3/3" in out


def test_bad_call():
    out = symbolic_math.invoke("not_a_real_function(3)")
    assert out.startswith("ERROR")