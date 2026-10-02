import math
import pytest


def test_manifest_and_decoupling():
    import app.v10100 as v
    m = v.capabilities()
    assert m["version"] == "10.10.0"
    assert m["backendFirst"] is True
    assert m["wordpressRequired"] is False
    assert m["capabilities"]["exactArithmetic"] is True
    c = v.standalone_contract()
    assert c["architecture"] == "backend-first-decoupled"
    assert c["migration"]["frontendMayMoveOffWordPressWithoutChangingCalculationContracts"] is True


def test_exact_arithmetic_and_symbolic():
    import app.v10100 as v
    out = v.execute(v.CalculationRequest(operation="exact", expression="1/3 + 1/6"))
    assert out["result"]["exact"] == "1/2"
    d = v.execute(v.CalculationRequest(operation="differentiate", expression="x**3 + 2*x", variable="x"))
    assert d["result"]["expression"] == "3*x**2 + 2"


def test_root_and_numeric_integration():
    import app.v10100 as v
    root = v.execute(v.CalculationRequest(operation="root", expression="x**2 - 2", variable="x", bracket=[1,2]))
    assert root["result"]["converged"] is True
    assert abs(root["result"]["root"] - math.sqrt(2)) < 1e-8
    integ = v.execute(v.CalculationRequest(operation="integrate-numeric", expression="x**2", variable="x", domain=[0,1]))
    assert abs(integ["result"]["value"] - 1/3) < 1e-9


def test_matrix_svd_and_conditioning():
    import app.v10100 as v
    out = v.execute(v.CalculationRequest(operation="matrix", matrix=[[1,0],[0,2]], matrixOperation="svd"))
    assert sorted(out["result"]["singularValues"]) == [1.0,2.0]
    assert out["result"]["conditionNumber"] == pytest.approx(2.0)


def test_units_when_available():
    import app.v10100 as v
    if v.pint is None:
        pytest.skip("Pint not installed")
    out = v.execute(v.CalculationRequest(operation="units", unitExpression="12 kilogram * 3 meter / second**2", targetUnit="newton"))
    assert out["result"]["magnitude"] == pytest.approx(36.0)
    assert out["result"]["units"] == "newton"
