"""SC-SIM-01 G7: the governed Workspace execution adapter calls existing Workbench calculations only."""
import os

import pytest
from fastapi.testclient import TestClient

from app import workspace_adapter as wa
from app.main import app
from app.v11150 import UncertaintyRequest, execute_uncertainty

client = TestClient(app)
TOKEN = "adapter-test-token"
AUTH = {"Authorization": f"Bearer {TOKEN}"}
MC = {"operation": "monte-carlo", "expression": "a*b + 2", "samples": 2000, "seed": 7,
      "inputs": [{"name": "a", "mean": 1.0, "standardDeviation": 0.1}, {"name": "b", "mean": 3.0, "standardDeviation": 0.2}]}
SS = {"simulationKind": "linear-state-space",
      "model": {"matrix_a": [[0, 1], [-2, -0.3]], "initial_state": [1, 0], "input_vector": [0, 0], "dt": 0.01, "steps": 500}}


def envelope(operation, payload, **over):
    return {"schema": wa.ENVELOPE_SCHEMA, "language": "workbench", "operation": operation, "payload": payload,
            "requestFingerprint": "f" * 64, "arbitraryCodeExecution": False, **over}


@pytest.fixture(autouse=True)
def token(monkeypatch):
    monkeypatch.setenv(wa.TOKEN_ENV, TOKEN)


def test_uncertainty_is_the_existing_workbench_calculation_with_the_seed_echoed():
    r = client.post("/v1/workspace/execute", headers=AUTH, json=envelope("workspace.workbench.uncertainty-propagation", MC))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["schema"] == wa.RESULT_SCHEMA and body["arbitraryCodeExecution"] is False
    direct = execute_uncertainty(UncertaintyRequest.model_validate(MC))
    assert body["result"]["result"] == direct["result"] and body["result"]["seed"] == 7
    assert body["numericalLibraries"]["numpy"] and body["numericalLibraries"]["runtime"].startswith("workbench ")


def test_dynamical_simulation_runs_the_v750_runtime():
    r = client.post("/v1/workspace/execute", headers=AUTH, json=envelope("workspace.workbench.dynamical-simulation", SS))
    assert r.status_code == 200, r.text
    result = r.json()["result"]
    assert result["schema"] == "sc-workbench-dynamical-simulation-result/1.0"
    assert set(result["trajectory"]["finalState"]) == {"x0", "x1"} and "seed" not in result


@pytest.mark.parametrize("headers,status", [({}, 401), ({"Authorization": "Bearer wrong"}, 401)])
def test_authentication_is_required(headers, status):
    r = client.post("/v1/workspace/execute", headers=headers, json=envelope("workspace.workbench.uncertainty-propagation", MC))
    assert r.status_code == status


def test_unconfigured_adapter_refuses(monkeypatch):
    monkeypatch.delenv(wa.TOKEN_ENV)
    r = client.post("/v1/workspace/execute", headers=AUTH, json=envelope("workspace.workbench.uncertainty-propagation", MC))
    assert r.status_code == 503
    assert client.get("/v1/workspace/adapter").json()["configured"] is False


@pytest.mark.parametrize("env,status", [
    ({"language": "julia"}, 400), ({"schema": "x"}, 400), ({"arbitraryCodeExecution": True}, 400),
    ({"operation": "workspace.workbench.digital-twin"}, 400), ({"payload": []}, 400),
])
def test_envelope_refusals(env, status):
    r = client.post("/v1/workspace/execute", headers=AUTH, json={**envelope("workspace.workbench.uncertainty-propagation", MC), **env})
    assert r.status_code == status


@pytest.mark.parametrize("expression", ["a.__class__", "exec(a)", "a[0]", "a; b", "open(a)", "a.evalf"])
def test_expressions_outside_the_governed_grammar_are_refused(expression):
    r = client.post("/v1/workspace/execute", headers=AUTH,
                    json=envelope("workspace.workbench.uncertainty-propagation", {**MC, "expression": expression}))
    assert r.status_code == 422


def test_digital_twin_and_invalid_requests_are_refused():
    twin = {**SS, "simulationKind": "digital-twin"}
    assert client.post("/v1/workspace/execute", headers=AUTH,
                       json=envelope("workspace.workbench.dynamical-simulation", twin)).status_code == 422
    assert client.post("/v1/workspace/execute", headers=AUTH,
                       json=envelope("workspace.workbench.uncertainty-propagation", {**MC, "samples": 5})).status_code == 422
