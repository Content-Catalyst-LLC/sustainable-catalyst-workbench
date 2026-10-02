import importlib
import pytest

def _module(tmp_path, monkeypatch):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path))
    import app.v1060 as v1060
    return importlib.reload(v1060)

def _request(v):
    return v.ExplanationRequest(
        projectKey="p1", explanationKey="perm-1", title="Permutation importance",
        modelRecordHash="a"*64, datasetRecordHash="b"*64, representationHash="c"*64,
        explainerKind="permutation-importance", scope="global",
        target={"outputKey":"y","outputKind":"scalar"},
        parameters={"repeats":10,"randomSeed":7,"featureKeys":["x1","x2"]},
    )

def test_manifest():
    import app.v1060 as v
    m=v.manifest()
    assert m["version"]=="10.6.0"
    assert m["capabilities"]["shapCompatibleContracts"] is True
    assert m["boundaries"]["causalInferenceFromAttribution"] is False

def test_compose_is_deterministic(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch); req=_request(v)
    a=v.compose_explanation(req); b=v.compose_explanation(req)
    assert a["explanationHash"]==b["explanationHash"]
    assert any(i["code"]=="explanation-not-causation" for i in a["issues"])

def test_save_result_and_compare(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    saved=v.save_explanation(_request(v))
    assert saved["idempotent"] is False
    assert v.save_explanation(_request(v))["idempotent"] is True
    hashes=[]
    for runtime,a,b in [("r1",0.4,0.1),("r2",0.3,0.2)]:
        row=v.record_result(v.ExplanationResultRequest(
            projectKey="p1", explanationHash=saved["explanationHash"], runtime=runtime,
            attributions=[{"featureKey":"x1","value":a},{"featureKey":"x2","value":b}],
        ))
        hashes.append(row["resultHash"])
        assert row["result"]["causalInterpretationAllowed"] is False
    comp=v.compare_results(v.ComparisonRequest(projectKey="p1",resultHashes=hashes,comparisonKey="c1",title="Compare"))
    assert len(comp["comparison"]["featureComparison"])==2
    assert comp["comparison"]["causalInterpretationAllowed"] is False

def test_local_requires_instances():
    import app.v1060 as v
    with pytest.raises(Exception):
        v.ExplanationRequest(projectKey="p1", explanationKey="local", title="Local",
            modelRecordHash="a"*64,datasetRecordHash="b"*64,explainerKind="permutation-importance",
            scope="local",target={"outputKey":"y","outputKind":"scalar"})

def test_shap_requires_background():
    import app.v1060 as v
    with pytest.raises(Exception):
        v.ExplanationRequest(projectKey="p1",explanationKey="shap",title="SHAP",
            modelRecordHash="a"*64,datasetRecordHash="b"*64,explainerKind="shap-compatible",
            scope="global",target={"outputKey":"y","outputKind":"scalar"})
