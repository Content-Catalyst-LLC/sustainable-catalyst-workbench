from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_v1140_status():
    data = client.get("/v1140/status").json()
    assert data["ok"] is True
    assert data["version"] == "11.4.0"
    assert data["engines"]["symbolicExact"] == "sympy"
    assert data["engines"]["numericalTensor"] == "numpy"
    assert data["wordpressRequired"] is False


def test_exact_determinant_and_inverse():
    det = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "determinant",
        "matrix": [[1, 2], [3, 4]],
        "exact": True
    }).json()
    assert det["result"] == "-2"

    inv = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "inverse",
        "matrix": [[1, 2], [3, 4]],
        "exact": True
    }).json()
    assert inv["result"] == [["-2", "1"], ["3/2", "-1/2"]]
    assert inv["verification"]["identityResidualZero"] is True


def test_rank_rref_nullspace():
    rank = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "rank",
        "matrix": [[1, 2, 3], [2, 4, 6]],
        "exact": True
    }).json()
    assert rank["result"] == 1

    rref = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "rref",
        "matrix": [[1, 2, 3], [2, 4, 6]]
    }).json()
    assert rref["details"]["pivots"] == [0]

    nullspace = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "nullspace",
        "matrix": [[1, 2, 3], [2, 4, 6]]
    }).json()
    assert nullspace["details"]["dimension"] == 2


def test_eigen_and_characteristic_polynomial():
    eig = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "eigenvalues",
        "matrix": [[2, 0], [0, 3]],
        "exact": True
    }).json()
    values = {x["value"]: x["multiplicity"] for x in eig["result"]}
    assert values == {"2": 1, "3": 1}

    char = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "characteristic-polynomial",
        "matrix": [[2, 0], [0, 3]]
    }).json()
    assert char["result"] == "lambda**2 - 5*lambda + 6"


def test_exact_linear_system():
    data = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "solve-linear-system",
        "matrix": [[2, 1], [1, -1]],
        "vector": [5, 1],
        "exact": True
    }).json()
    assert data["result"] == [["2"], ["1"]]
    assert data["verification"]["residualZero"] is True


def test_matrix_and_kronecker_products():
    multiply = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "matrix-multiply",
        "matrix": [[1, 2], [3, 4]],
        "matrixB": [[2, 0], [1, 2]],
        "exact": True
    }).json()
    assert multiply["result"] == [["4", "4"], ["10", "8"]]

    kron = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "kronecker-product",
        "matrix": [[1, 2]],
        "matrixB": [[3, 4]],
        "exact": True
    }).json()
    assert kron["result"] == [["3", "4", "6", "8"]]


def test_tensor_operations():
    contract = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "tensor-contract",
        "tensor": [[1, 2], [3, 4]],
        "tensorB": [[5, 6], [7, 8]],
        "axes": 1
    }).json()
    assert contract["engine"] == "numpy"
    assert contract["result"] == [[19.0, 22.0], [43.0, 50.0]]

    reshape = client.post("/calculation-engine/v1/linear-algebra", json={
        "operation": "tensor-reshape",
        "tensor": [[1, 2], [3, 4]],
        "shape": [4]
    }).json()
    assert reshape["result"] == [1.0, 2.0, 3.0, 4.0]


def test_calculation_object_extension():
    payload = {
        "calculationObjectRequest": {
            "calculation": {
                "operation": "matrix",
                "matrix": [[1, 2], [3, 4]],
                "matrixOperation": "det"
            },
            "requestedResultType": "matrix"
        },
        "linearAlgebra": {
            "operation": "determinant",
            "matrix": [[1, 2], [3, 4]],
            "exact": True
        }
    }
    data = client.post(
        "/calculation-engine/v1/linear-algebra/calculation-object",
        json=payload
    ).json()
    assert data["ok"] is True
    assert data["extensions"]["linearAlgebra"]["result"] == "-2"
    assert data["result"]["linearAlgebra"] == "-2"
    assert data["executionPlan"]["linearAlgebra"]["engine"] == "sympy"
    assert data["provenance"]["linearAlgebraResultHash"]
    assert data["calculationObjectHash"]
