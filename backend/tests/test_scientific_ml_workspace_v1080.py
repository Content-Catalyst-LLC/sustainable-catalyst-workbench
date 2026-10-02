import importlib
import pytest

def _module(tmp_path, monkeypatch):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path))
    import app.v1080 as v1080
    return importlib.reload(v1080)

def _request(v):
    return v.StudyRequest(
        projectKey="p1",
        studyKey="surrogate-1",
        title="Simulation surrogate",
        scientificMLKind="surrogate-model",
        taskKind="regression",
        datasetRecordHash="a"*64,
        representationHash="b"*64,
        variables=[
            {"key":"temperature","role":"feature","units":"K","physicalQuantity":"temperature"},
            {"key":"pressure","role":"feature","units":"Pa","physicalQuantity":"pressure"},
            {"key":"yield","role":"target","units":"kg"},
        ],
        simulations=[
            {
                "simulationRecordHash":"c"*64,
                "simulatorName":"test-sim",
                "simulatorVersion":"1.0",
                "sampleCount":100,
            }
        ],
        trainingPlan={"runtime":"external-scientific-ml-runtime","randomSeed":7},
    )

def test_manifest():
    import app.v1080 as v
    m=v.manifest()
    assert m["version"]=="10.8.0"
    assert m["capabilities"]["simulationToMLLineage"] is True
    assert m["boundaries"]["automaticModelTraining"] is False

def test_compose_deterministic(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    req=_request(v)
    a=v.compose_study(req)
    b=v.compose_study(req)
    assert a["studyHash"]==b["studyHash"]
    assert a["studyReady"] is True
    assert any(i["code"]=="scientific-ml-not-physical-proof" for i in a["issues"])

def test_save_result_compare(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    saved=v.save_study(_request(v))
    assert saved["idempotent"] is False
    assert v.save_study(_request(v))["idempotent"] is True

    hashes=[]
    for runtime,rmse,r2 in [("r1",0.2,0.90),("r2",0.15,0.93)]:
        row=v.record_result(v.ResultRequest(
            projectKey="p1",
            studyHash=saved["studyHash"],
            runtime=runtime,
            trainedModelRecordHash="d"*64,
            metrics=[
                {"name":"rmse","value":rmse},
                {"name":"r2","value":r2},
            ],
            constraintChecks=[
                {"kind":"range","passed":True,"details":"within supported range"}
            ],
        ))
        assert row["result"]["physicalValidityCertified"] is False
        hashes.append(row["resultHash"])

    comp=v.compare_results(v.ComparisonRequest(
        projectKey="p1",
        resultHashes=hashes,
        comparisonKey="cmp",
        title="Surrogate comparison",
    ))
    assert comp["comparison"]["automaticWinnerSelection"] is False
    assert len(comp["comparison"]["metricComparison"])==2

def test_surrogate_requires_simulation():
    import app.v1080 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",
            studyKey="s",
            title="Bad surrogate",
            scientificMLKind="surrogate-model",
            taskKind="regression",
            datasetRecordHash="a"*64,
            variables=[{"key":"x","role":"feature"}],
        )

def test_hybrid_requires_mechanistic_model():
    import app.v1080 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",
            studyKey="h",
            title="Hybrid",
            scientificMLKind="hybrid-mechanistic-ml",
            taskKind="regression",
            datasetRecordHash="a"*64,
            variables=[{"key":"x","role":"feature"}],
        )

def test_physics_informed_requires_constraint():
    import app.v1080 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",
            studyKey="pinn",
            title="PINN contract",
            scientificMLKind="physics-informed-contract",
            taskKind="field-prediction",
            datasetRecordHash="a"*64,
            variables=[{"key":"x","role":"coordinate"}],
        )

def test_constraint_reference_validation():
    import app.v1080 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",
            studyKey="c",
            title="Bad constraint",
            scientificMLKind="constraint-aware-contract",
            taskKind="regression",
            datasetRecordHash="a"*64,
            variables=[{"key":"x","role":"feature"}],
            constraints=[
                {"kind":"range","variableKeys":["y"],"lower":0.0}
            ],
        )
