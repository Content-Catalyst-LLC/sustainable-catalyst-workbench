from app.routers.equations import analyze_equation, EquationAnalyzeRequest


def test_equation_analyzer_recommends_systems_tools():
    res = analyze_equation(EquationAnalyzeRequest(equation="S_{t+1}=S_t+I_t-O_t", context="stock flow limits to growth"))
    assert res["ok"] is True
    assert "limits-to-growth-system-dynamics-tool" in [t["id"] for t in res["recommended_tools"]]
    assert "graphability" in res["values"]


def test_equation_analyzer_recommends_electrical_tools():
    res = analyze_equation(EquationAnalyzeRequest(equation="Z = R + j\\omega L", context="impedance rf circuit"))
    assert res["ok"] is True
    ids = [t["id"] for t in res["recommended_tools"]]
    assert "electronics-engineering-calculator" in ids
    assert "rf-and-antenna-calculator" in ids
