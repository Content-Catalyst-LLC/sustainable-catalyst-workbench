from backend.app.v250 import (
    MonteCarloRequest,
    SimulationRequest,
    SystemsRequest,
    UncertainVariable,
    ValidationRequest,
    run_monte_carlo,
    run_simulation,
    simulate_system,
    validate_model,
)


def test_first_order_simulation_converges():
    result = run_simulation(SimulationRequest(model_type="first_order", initial_state=0, input_value=10, gain=2, time_constant=4, duration=40, time_step=0.1))
    assert result["ok"] is True
    assert abs(result["metrics"]["finalState"] - 20) < 0.01


def test_linear_system_dimensions_and_state():
    result = simulate_system(SystemsRequest(matrix_a=[[-0.2, 0], [0.1, -0.3]], initial_state=[10, 0], input_vector=[0, 0], duration=2, time_step=0.05))
    assert result["ok"] is True
    assert len(result["series"]) == 2
    assert result["finalState"][0] < 10


def test_monte_carlo_is_seeded():
    request = MonteCarloRequest(
        runs=1000,
        seed=42,
        variables=[UncertainVariable(name="x", mean=10, standard_deviation=1, minimum=5, maximum=15)],
        coefficients={"x": 2},
        threshold=20,
    )
    first = run_monte_carlo(request)
    second = run_monte_carlo(request)
    assert first["metrics"] == second["metrics"]


def test_validation_acceptance():
    result = validate_model(ValidationRequest(observed=[1, 2, 3, 4], predicted=[1.01, 1.98, 3.02, 3.99], maximum_rmse=0.1, maximum_absolute_bias=0.1, minimum_r2=0.99, maximum_mape_percent=5))
    assert result["ok"] is True
