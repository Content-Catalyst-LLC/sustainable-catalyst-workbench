from app.engines.runner import run_tool

def test_energy_calculator():
    out = run_tool("energy-systems-calculator", {"mode":"electricity_cost_emissions", "inputs":"kwh=100;rate=0.2;kgco2_per_kwh=0.5"})
    assert out["ok"] is True
    assert out["values"]["cost"] == 20

def test_linear_solver():
    out = run_tool("linear-system-solver", {"A":"[[2,1],[1,3]]", "b":"[1,2]"})
    assert out["ok"] is True
    assert "solution" in out["values"]

def test_statistics_graph():
    out = run_tool("statistics-analyzer", {"data":"1,2,3,4,5"})
    assert out["ok"] is True
    assert out["graphs"] and "<svg" in out["graphs"][0]["svg"]

def test_visual_analytics_studio_line_graph():
    out = run_tool("visual-analytics-studio", {"chart_type":"line", "title":"Test trend", "x_values":"1,2,3", "y_values":"2,4,8"})
    assert out["ok"] is True
    assert out["values"]["chart_type"] == "line"
    assert out["graphs"] and "<svg" in out["graphs"][0]["svg"]
