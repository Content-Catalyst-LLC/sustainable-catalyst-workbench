from copy import deepcopy
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

BASE={
    "calculation":{
        "operation":"evaluate",
        "expression":"2+3*4"
    },
    "requestedResultType":"numeric",
    "requireVerification":True,
    "requireProvenance":True
}

def test_status():
    d=client.get("/v11170/status").json()
    assert d["version"]=="11.17.0"
    assert d["capabilities"]["deterministicReplay"] is True
    assert d["capabilities"]["structuredDivergenceReporting"] is True

def test_runtime_manifest():
    d=client.get("/calculation-engine/v1/reproducibility/runtime-manifest").json()
    assert d["ok"] is True
    m=d["runtimeManifest"]
    assert m["workbenchVersion"]=="11.17.0"
    assert m["manifestHash"]

def test_capture_and_replay_strict():
    capture=client.post("/calculation-engine/v1/reproducibility/capture",json={
        "calculationRequest":BASE,
        "label":"canonical arithmetic replay"
    }).json()
    assert capture["ok"] is True
    env=capture["envelope"]
    assert env["requestHash"]
    assert env["sourceResultHash"]
    assert env["envelopeHash"]

    replay=client.post("/calculation-engine/v1/reproducibility/replay",json={
        "envelope":env,
        "comparisonMode":"strict"
    }).json()
    assert replay["ok"] is True
    cert=replay["certificate"]
    assert cert["envelopeIntegrity"] is True
    assert cert["requestIntegrity"] is True
    assert cert["reproducible"] is True
    assert cert["divergences"]==[]

def test_result_only_comparison_detects_divergence():
    a=client.post("/calculation-engine/v1/compute",json=BASE).json()
    b=deepcopy(a)
    b["result"]["value"]=999
    b["result"]["resultHash"]="tampered-result-hash"

    d=client.post("/calculation-engine/v1/reproducibility/compare",json={
        "expected":a,
        "observed":b,
        "comparisonMode":"result-only"
    }).json()
    assert d["reproducible"] is False
    assert d["divergences"][0]["field"]=="resultHash"

def test_calculation_object_extension():
    d=client.post("/calculation-engine/v1/reproducibility/calculation-object",json={
        "calculationRequest":BASE
    }).json()
    assert d["ok"] is True
    assert d["extensions"]["replay"]["schema"]=="sc-workbench-calculation-replay-envelope/1.0"
    assert d["reproducibility"]["replaySupported"] is True
    assert d["reproducibility"]["replayEnvelopeHash"]
    assert d["provenance"]["runtimeManifestHash"]
