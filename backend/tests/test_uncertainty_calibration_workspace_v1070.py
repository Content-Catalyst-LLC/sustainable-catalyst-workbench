import importlib
import pytest

def _module(tmp_path, monkeypatch):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path))
    import app.v1070 as v1070
    return importlib.reload(v1070)

def _request(v):
    return v.StudyRequest(
        projectKey="p1",
        studyKey="cal-1",
        title="Classification calibration",
        modelRecordHash="a"*64,
        datasetRecordHash="b"*64,
        representationHash="c"*64,
        taskKind="classification",
        uncertaintyKinds=["predictive"],
        calibrationKind="reliability-analysis",
        target={"outputKey":"probability"},
        splits=[
            {"datasetRecordHash":"b"*64,"splitName":"validation","role":"validation","sampleCount":100}
        ],
        parameters={"bins":10,"confidenceLevel":0.95},
    )

def test_manifest():
    import app.v1070 as v
    m=v.manifest()
    assert m["version"]=="10.7.0"
    assert m["capabilities"]["conformalContracts"] is True
    assert m["boundaries"]["automaticCalibrationExecution"] is False

def test_compose_is_deterministic(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch); req=_request(v)
    a=v.compose_study(req); b=v.compose_study(req)
    assert a["studyHash"]==b["studyHash"]
    assert a["studyReady"] is True
    assert any(i["code"]=="uncertainty-not-guarantee" for i in a["issues"])

def test_save_result_and_compare(tmp_path, monkeypatch):
    v=_module(tmp_path, monkeypatch)
    saved=v.save_study(_request(v))
    assert saved["idempotent"] is False
    assert v.save_study(_request(v))["idempotent"] is True
    hashes=[]
    for runtime,ece,brier in [("r1",0.05,0.18),("r2",0.04,0.17)]:
        row=v.record_result(v.ResultRequest(
            projectKey="p1",studyHash=saved["studyHash"],runtime=runtime,
            expectedCalibrationError=ece,brierScore=brier,
            reliabilityBins=[
                {"lowerBound":0.0,"upperBound":0.5,"meanConfidence":0.3,"observedFrequency":0.28,"count":50},
                {"lowerBound":0.5,"upperBound":1.0,"meanConfidence":0.8,"observedFrequency":0.76,"count":50},
            ],
        ))
        hashes.append(row["resultHash"])
    comp=v.compare_results(v.ComparisonRequest(
        projectKey="p1",resultHashes=hashes,comparisonKey="c1",title="Compare"
    ))
    assert comp["comparison"]["automaticWinnerSelection"] is False
    assert len(comp["comparison"]["metrics"])==5

def test_conformal_requires_calibration_split():
    import app.v1070 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",studyKey="conf",title="Conformal",
            modelRecordHash="a"*64,datasetRecordHash="b"*64,
            taskKind="regression",uncertaintyKinds=["conformal"],
            calibrationKind="conformal-calibration",
            target={"outputKey":"y"},
            splits=[{"datasetRecordHash":"b"*64,"splitName":"test","role":"test"}],
        )

def test_temperature_scaling_requires_calibration_split():
    import app.v1070 as v
    with pytest.raises(Exception):
        v.StudyRequest(
            projectKey="p1",studyKey="temp",title="Temperature",
            modelRecordHash="a"*64,datasetRecordHash="b"*64,
            taskKind="classification",uncertaintyKinds=["predictive"],
            calibrationKind="temperature-scaling-contract",
            target={"outputKey":"p"},
        )

def test_quantile_validation():
    import app.v1070 as v
    with pytest.raises(Exception):
        v.TargetBinding(outputKey="y",quantileLevels=[0.1,1.1])
