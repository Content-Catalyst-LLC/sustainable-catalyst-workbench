import importlib
import os
from pathlib import Path

import pytest


def _module(tmp_path, monkeypatch):
    monkeypatch.setenv("SCWB_RESEARCH_ENVIRONMENT_STORE", str(tmp_path))
    import app.v1050 as v1050
    return importlib.reload(v1050)


def _request(v):
    return v.RepresentationRequest(
        projectKey="p1",
        representationKey="baseline",
        title="Baseline representation",
        datasetRecordHash="a" * 64,
        fields=[
            {"fieldKey": "age", "sourcePath": "age", "kind": "numeric", "role": "feature"},
            {"fieldKey": "region", "sourcePath": "region", "kind": "categorical", "role": "feature"},
            {"fieldKey": "target", "sourcePath": "target", "kind": "numeric", "role": "target"},
        ],
        transforms=[
            {"stepKey": "age-impute", "kind": "impute-median", "inputs": ["age"], "outputKey": "age_i", "fitScope": "train-only"},
            {"stepKey": "age-scale", "kind": "standardize", "inputs": ["age_i"], "outputKey": "age_z", "fitScope": "train-only"},
            {"stepKey": "region-onehot", "kind": "one-hot", "inputs": ["region"], "outputKey": "region_oh", "fitScope": "train-only"},
        ],
        outputKeys=["age_z", "region_oh"],
    )


def test_manifest(v1050_module=None):
    import app.v1050 as v
    m = v.manifest()
    assert m["version"] == "10.5.0"
    assert m["capabilities"]["contentAddressedRepresentations"] is True
    assert m["boundaries"]["automaticTransformFitting"] is False


def test_compose_is_deterministic(tmp_path, monkeypatch):
    v = _module(tmp_path, monkeypatch)
    req = _request(v)
    a = v.compose_representation(req)
    b = v.compose_representation(req)
    assert a["representationHash"] == b["representationHash"]
    assert a["representationReady"] is True


def test_save_and_plan(tmp_path, monkeypatch):
    v = _module(tmp_path, monkeypatch)
    req = _request(v)
    saved = v.save_representation(req)
    assert saved["idempotent"] is False
    saved2 = v.save_representation(req)
    assert saved2["idempotent"] is True
    plan = v.materialization_plan(v.MaterializationPlanRequest(
        projectKey="p1", representationHash=saved["representationHash"], splitName="train"
    ))
    assert plan["plan"]["fitRequired"] is True
    assert plan["plan"]["orderedSteps"][0]["stepKey"] == "age-impute"


def test_target_leakage_warning(tmp_path, monkeypatch):
    v = _module(tmp_path, monkeypatch)
    req = v.RepresentationRequest(
        projectKey="p1", representationKey="leaky", title="Leaky", datasetRecordHash="b" * 64,
        fields=[{"fieldKey": "y", "sourcePath": "y", "kind": "numeric", "role": "target"}],
        transforms=[{"stepKey": "copy-y", "kind": "passthrough", "inputs": ["y"], "outputKey": "y_copy", "fitScope": "stateless"}],
    )
    row = v.compose_representation(req)
    assert any(i["code"] == "target-used-as-feature-input" for i in row["issues"])


def test_prefitted_requires_state_hash():
    import app.v1050 as v
    with pytest.raises(Exception):
        v.TransformStep(stepKey="scale", kind="standardize", inputs=["x"], outputKey="x_z", fitScope="pre-fitted")
