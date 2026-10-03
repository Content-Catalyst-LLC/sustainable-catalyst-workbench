from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def test_status():
    d=client.get("/v1190/status").json()
    assert d["version"]=="11.9.0" and d["engine"]=="mpmath"

def test_high_precision_pi():
    d=client.post("/calculation-engine/v1/precision",json={
        "operation":"constant","constant":"pi","precisionDigits":80}).json()
    assert d["result"]["value"].startswith("3.14159265358979323846264338327950288419716939937510")

def test_high_precision_eval():
    d=client.post("/calculation-engine/v1/precision",json={
        "operation":"evaluate","expression":"sqrt(2)","precisionDigits":70}).json()
    assert d["result"]["value"].startswith("1.414213562373095048801688724209698078")

def test_interval_add():
    d=client.post("/calculation-engine/v1/precision",json={
        "operation":"interval-add","precisionDigits":40,
        "interval":{"lower":"1","upper":"2"},
        "intervalB":{"lower":"3","upper":"4"}}).json()
    assert "4.0" in d["result"]["interval"] and "6.0" in d["result"]["interval"]

def test_interval_contains():
    d=client.post("/calculation-engine/v1/precision",json={
        "operation":"interval-contains","interval":{"lower":"1","upper":"2"},"value":"1.5"}).json()
    assert d["result"] is True

def test_interval_function():
    d=client.post("/calculation-engine/v1/precision",json={
        "operation":"interval-function","function":"sin",
        "interval":{"lower":"0","upper":"1.5707963267948966"}}).json()
    assert "0.0" in d["result"]["interval"]

def test_calculation_object():
    payload={"calculationObjectRequest":{"calculation":{"operation":"evaluate","expression":"1"},
      "requestedResultType":"numeric"},
      "precisionArithmetic":{"operation":"constant","constant":"pi","precisionDigits":60}}
    d=client.post("/calculation-engine/v1/precision/calculation-object",json=payload).json()
    assert d["ok"] is True
    assert d["executionPlan"]["precisionArithmetic"]["precisionDigits"]==60
    assert d["provenance"]["precisionArithmeticResultHash"]
