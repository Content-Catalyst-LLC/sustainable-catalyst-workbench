from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1170_status():
    d = client.get("/v1170/status").json()
    assert d["ok"] is True
    assert d["version"] == "11.7.0"
    assert d["engine"] == "pint"
    assert d["capabilities"]["dimensionConsistencyChecks"] is True


def test_conversion_preserves_dimension():
    d = client.post("/calculation-engine/v1/quantities", json={
        "operation": "convert",
        "expression": "100 kilometer",
        "targetUnit": "mile"
    }).json()
    assert d["verification"]["dimensionPreserved"] is True
    assert d["result"]["unit"] == "mile"
    assert abs(d["result"]["magnitude"] - 62.1371192237) < 1e-8


def test_dimensionality():
    d = client.post("/calculation-engine/v1/quantities", json={
        "operation": "dimensionality",
        "expression": "9.81 meter / second ** 2"
    }).json()
    assert d["result"]["dimensionality"]["[length]"] == 1.0
    assert d["result"]["dimensionality"]["[time]"] == -2.0


def test_unit_aware_arithmetic():
    d = client.post("/calculation-engine/v1/quantities", json={
        "operation": "add",
        "left": {"magnitude": 1, "unit": "meter"},
        "right": {"magnitude": 50, "unit": "centimeter"}
    }).json()
    assert d["result"]["unit"] == "meter"
    assert d["result"]["magnitude"] == 1.5
    assert d["verification"]["dimensionallyCompatible"] is True


def test_derived_quantity_energy():
    d = client.post("/calculation-engine/v1/quantities", json={
        "operation": "derive",
        "formula": "q1 * q2 ** 2",
        "operands": [
            {"magnitude": 2, "unit": "kilogram"},
            {"magnitude": 3, "unit": "meter / second"}
        ]
    }).json()
    base = d["result"]["baseUnits"]
    assert base["unit"] == "kilogram * meter ** 2 / second ** 2"
    assert base["magnitude"] == 18.0


def test_consistency_check():
    d = client.post("/calculation-engine/v1/quantities", json={
        "operation": "consistency-check",
        "operands": [
            {"magnitude": 1, "unit": "meter"},
            {"magnitude": 100, "unit": "centimeter"},
            {"magnitude": 0.001, "unit": "kilometer"}
        ]
    }).json()
    assert d["result"] is True
    assert d["verification"]["allSameDimension"] is True


def test_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "units",
                "unitExpression": "100 kilometer",
                "targetUnit": "mile"
            },
            "requestedResultType": "quantity"
        },
        "quantity": {
            "operation": "convert",
            "expression": "100 kilometer",
            "targetUnit": "mile"
        }
    }
    d = client.post(
        "/calculation-engine/v1/quantities/calculation-object",
        json=payload
    ).json()
    assert d["ok"] is True
    assert d["extensions"]["physicalQuantity"]["engine"] == "pint"
    assert d["units"]["engine"] == "pint"
    assert d["executionPlan"]["physicalQuantity"]["operation"] == "convert"
    assert d["provenance"]["physicalQuantityResultHash"]
    assert d["calculationObjectHash"]
