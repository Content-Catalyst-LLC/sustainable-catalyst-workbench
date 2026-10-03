from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1180_status():
    d = client.get("/v1180/status").json()
    assert d["ok"] is True
    assert d["version"] == "11.8.0"
    assert d["engine"] == "scipy-numpy"
    assert "normal" in d["distributions"]
    assert d["capabilities"]["linearRegression"] is True


def test_descriptive_statistics():
    d = client.post("/calculation-engine/v1/statistics", json={
        "operation": "describe",
        "data": [1, 2, 3, 4, 5]
    }).json()
    assert d["result"]["count"] == 5
    assert d["result"]["mean"] == 3.0
    assert d["result"]["median"] == 3.0
    assert d["result"]["varianceSample"] == 2.5


def test_normal_distribution_probability_and_quantile():
    cdf = client.post("/calculation-engine/v1/statistics", json={
        "operation": "distribution-cdf",
        "distribution": "normal",
        "x": 0
    }).json()
    assert cdf["result"] == 0.5

    q = client.post("/calculation-engine/v1/statistics", json={
        "operation": "distribution-quantile",
        "distribution": "normal",
        "probability": 0.975
    }).json()
    assert abs(q["result"] - 1.95996398454) < 1e-8


def test_binomial_pmf():
    d = client.post("/calculation-engine/v1/statistics", json={
        "operation": "distribution-pmf",
        "distribution": "binomial",
        "parameters": {"n": 10, "p": 0.5},
        "x": 5
    }).json()
    assert abs(d["result"] - 0.24609375) < 1e-12


def test_seeded_sampling_is_reproducible():
    payload = {
        "operation": "random-sample",
        "distribution": "normal",
        "sampleSize": 5,
        "seed": 42
    }
    a = client.post("/calculation-engine/v1/statistics", json=payload).json()
    b = client.post("/calculation-engine/v1/statistics", json=payload).json()
    assert a["result"] == b["result"]
    assert a["verification"]["deterministicWhenSeeded"] is True


def test_confidence_interval_and_t_test():
    ci = client.post("/calculation-engine/v1/statistics", json={
        "operation": "confidence-interval-mean",
        "data": [2, 4, 4, 4, 5, 5, 7, 9],
        "confidenceLevel": 0.95
    }).json()
    assert ci["result"]["mean"] == 5.0
    assert ci["result"]["lower"] < 5.0 < ci["result"]["upper"]

    test = client.post("/calculation-engine/v1/statistics", json={
        "operation": "one-sample-t-test",
        "data": [2, 4, 4, 4, 5, 5, 7, 9],
        "hypothesizedMean": 5.0
    }).json()
    assert abs(test["result"]["statistic"]) < 1e-12
    assert abs(test["result"]["pValueTwoSided"] - 1.0) < 1e-12


def test_correlation_covariance_and_regression():
    pearson = client.post("/calculation-engine/v1/statistics", json={
        "operation": "pearson-correlation",
        "data": [1, 2, 3, 4],
        "dataB": [2, 4, 6, 8]
    }).json()
    assert abs(pearson["result"]["correlation"] - 1.0) < 1e-12

    cov = client.post("/calculation-engine/v1/statistics", json={
        "operation": "covariance",
        "data": [1, 2, 3],
        "dataB": [2, 4, 6]
    }).json()
    assert abs(cov["result"]["covarianceSample"] - 2.0) < 1e-12

    reg = client.post("/calculation-engine/v1/statistics", json={
        "operation": "linear-regression",
        "data": [1, 2, 3, 4],
        "dataB": [3, 5, 7, 9]
    }).json()
    assert abs(reg["result"]["slope"] - 2.0) < 1e-12
    assert abs(reg["result"]["intercept"] - 1.0) < 1e-12
    assert abs(reg["result"]["rSquared"] - 1.0) < 1e-12


def test_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "evaluate",
                "expression": "1"
            },
            "requestedResultType": "numeric"
        },
        "statistics": {
            "operation": "describe",
            "data": [1, 2, 3, 4, 5]
        }
    }
    d = client.post(
        "/calculation-engine/v1/statistics/calculation-object",
        json=payload
    ).json()
    assert d["ok"] is True
    assert d["extensions"]["probabilityStatistics"]["engine"] == "scipy-numpy"
    assert d["result"]["probabilityStatistics"]["mean"] == 3.0
    assert d["executionPlan"]["probabilityStatistics"]["operation"] == "describe"
    assert d["provenance"]["probabilityStatisticsResultHash"]
    assert d["calculationObjectHash"]
