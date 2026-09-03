import pytest
import sympy as sp

from backend.app.v510 import (
    RestrictedSympyParser,
    ParseInput,
    ComputeInput,
    CalculusInput,
    SolveInput,
    SubstituteInput,
    status_record,
    parse_math,
    compute_math,
    calculus_math,
    solve_math,
    substitute_math,
)


def test_status_declares_secure_cas_foundation():
    result = status_record()
    assert result["version"] == "5.1.0"
    assert result["engine"] == "SymPy"
    assert result["parser"] == "restricted-ast"
    assert "equation-solving" in result["capabilities"]
    assert result["arbitraryCodeExecutionAuthorized"] is False
    assert result["pythonEvalAuthorized"] is False


def test_parser_preserves_exact_rational_math():
    parser = RestrictedSympyParser()
    assert parser.parse("1/3 + 1/6") == sp.Rational(1, 2)
    assert parser.parse("sqrt(8)") == 2 * sp.sqrt(2)


def test_parser_accepts_caret_and_standard_functions():
    parser = RestrictedSympyParser(["x"])
    assert sp.expand(parser.parse("(x+1)^2")) == sp.Symbol("x")**2 + 2*sp.Symbol("x") + 1
    assert parser.parse("sin(pi/2)") == 1


def test_parser_rejects_attribute_import_lambda_and_subscript():
    parser = RestrictedSympyParser()
    for expression in ["__import__('os')", "x.__class__", "(lambda x:x)(1)", "a[0]"]:
        with pytest.raises(ValueError):
            parser.parse(expression)


def test_parse_builds_canonical_equation_object():
    result = parse_math(ParseInput(expression="x^2 = 4"))["result"]
    assert result["kind"] == "equation"
    assert result["freeSymbols"] == ["x"]
    assert len(result["mathObjectHash"]) == 64
    assert result["pythonEvalAuthorized"] is False


def test_algebra_simplify_expand_factor_and_evaluate():
    simplified = compute_math(ComputeInput(expression="(x^2-1)/(x-1)", operation="simplify"))["result"]
    assert simplified["exactText"] == "x + 1"
    expanded = compute_math(ComputeInput(expression="(x+2)*(x-3)", operation="expand"))["result"]
    assert expanded["exactText"] == "x**2 - x - 6"
    factored = compute_math(ComputeInput(expression="x^2+4*x-12", operation="factor"))["result"]
    assert factored["exactText"] == "(x - 2)*(x + 6)"
    numeric = compute_math(ComputeInput(expression="pi", operation="evaluate", precision=30))["result"]
    assert numeric["decimalText"].startswith("3.141592653589793238462643383")


def test_solver_handles_quadratic_and_small_system():
    result = solve_math(SolveInput(equations=["x^2+4*x-12=0"], variables=["x"]))["result"]
    exact = sorted(item["x"]["exact"] for item in result["solutions"])
    assert exact == ["-6", "2"]
    system = solve_math(SolveInput(equations=["x+y=5", "x-y=1"], variables=["x", "y"]))["result"]
    assert system["solutions"][0]["x"]["exact"] == "3"
    assert system["solutions"][0]["y"]["exact"] == "2"


def test_calculus_derivative_integral_limit_and_series():
    derivative = calculus_math(CalculusInput(operation="differentiate", expression="x^3", variable="x"))["result"]
    assert derivative["exactText"] == "3*x**2"
    integral = calculus_math(CalculusInput(operation="integrate", expression="x^2", variable="x", lower="0", upper="3"))["result"]
    assert integral["exactText"] == "9"
    limit = calculus_math(CalculusInput(operation="limit", expression="sin(x)/x", variable="x", point="0"))["result"]
    assert limit["exactText"] == "1"
    series = calculus_math(CalculusInput(operation="series", expression="exp(x)", variable="x", point="0", seriesOrder=4))["result"]
    assert "O(x**4)" in series["exactText"]


def test_substitution_returns_exact_result():
    result = substitute_math(SubstituteInput(expression="a*x^2+b*x+c", substitutions={"a":"2","b":"3","c":"1","x":"4"}))["result"]
    assert result["exactText"] == "45"
    assert result["substitutions"]["x"] == "4"


def test_equation_parser_rejects_comparison_syntax():
    parser = RestrictedSympyParser()
    with pytest.raises(ValueError):
        parser.equation("x == 2")
