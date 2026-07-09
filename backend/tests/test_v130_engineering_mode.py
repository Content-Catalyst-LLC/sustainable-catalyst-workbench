from fastapi.testclient import TestClient
from app.main import app
from app.engines.engineering_mode_engine import engineering_mode_analyzer

client = TestClient(app)


def test_engineering_mode_unit_aware_force_note():
    res = engineering_mode_analyzer({"input": "F = m*a\nm = 12 kg\na = 3.5 m/s^2"})
    assert res["ok"] is True
    assert res["tool"] == "Engineering Mode"
    assert "engineering_note" in res["values"]
    assert res["values"]["unit_analysis"]["target"] == "F"
    assert any(token in res["values"]["unit_analysis"]["quantity"] for token in ["kilogram", "kg"])
    assert res["engineering_mode"]["calculation_note_sections"]


def test_engineering_mode_api_endpoint():
    response = client.post("/engineering/analyze", json={"input": "sigma = F/A\nF = 1000 N\nA = 0.02 m^2"})
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["tool"] == "Engineering Mode"
    assert data["values"]["formula_summary"]["target"] == "sigma"
    assert data["values"]["variables"]
