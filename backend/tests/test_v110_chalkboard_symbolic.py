from app.engines.symbolic_engine import symbolic_math_analyzer, chalkboard_preview, parse_symbolic_input


def test_chalkboard_preview_keyboard_power():
    assert "²" in chalkboard_preview("x^2 + 3x - 4")


def test_symbolic_translation_latex_and_sympy():
    out = symbolic_math_analyzer({"input": "x^2 + 3x - 4", "action": "factor", "variable": "x"})
    assert out["ok"] is True
    assert "latex" in out["values"]
    assert "sympy_code" in out["values"]
    assert out["values"]["variables"] == ["x"]


def test_symbolic_solve_quadratic():
    out = symbolic_math_analyzer({"input": "x^2 + 3x - 4 = 0", "action": "solve", "variable": "x"})
    assert out["ok"] is True
    assert set(out["values"]["symbolic_result"]) == {"-4", "1"}


def test_symbolic_derivative():
    out = symbolic_math_analyzer({"input": "sin(x) + x^2", "action": "differentiate", "variable": "x"})
    assert out["ok"] is True
    assert "2*x" in out["values"]["symbolic_result"]


def test_symbolic_graph_generates_svg():
    out = symbolic_math_analyzer({"input": "y = sin(x)", "action": "graph", "variable": "x", "x_min": -3.14, "x_max": 3.14})
    assert out["ok"] is True
    assert out["graphs"]
    assert "<svg" in out["graphs"][0]["svg"]
