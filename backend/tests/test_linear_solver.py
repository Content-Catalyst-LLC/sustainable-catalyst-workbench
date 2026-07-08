from app.engines.math.linear_system_solver import run


def test_linear_solver_direct_solution():
    output = run({"matrix": [[2, 1], [1, 3]], "vector": [1, 2]})
    assert output["result"]["consistent"] is True
    assert output["result"]["method"] == "direct_solve"
    assert output["result"]["residual_norm"] < 1e-9
