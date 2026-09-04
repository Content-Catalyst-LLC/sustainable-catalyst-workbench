import math

import pytest

from backend.app.v560 import (
    DifferentiationInput,
    IntegrationInput,
    InterpolationInput,
    LinearAlgebraInput,
    ODEInput,
    OptimizationInput,
    RootInput,
    differentiation_object,
    integration_object,
    interpolation_object,
    linear_algebra_object,
    ode_object,
    optimization_object,
    root_object,
    status_record,
)


def test_status_reports_numerical_capabilities_and_restricted_boundary():
    status = status_record()
    assert status['ok'] is True
    assert status['version'] == '5.6.0'
    assert 'numerical-root-finding' in status['capabilities']
    assert 'initial-value-ode-solving' in status['capabilities']
    assert 'bounded-multivariable-optimization' in status['capabilities']
    assert status['arbitraryCodeExecutionAuthorized'] is False
    assert status['pythonEvalAuthorized'] is False
    assert status['remoteShellAuthorized'] is False


def test_brent_root_finds_real_root_with_small_residual_and_hash():
    result = root_object(RootInput(expression='x^3-x-2', bracket=[1, 2], method='brentq'))['result']
    assert result['converged'] is True
    assert result['root'] == pytest.approx(1.5213797068, rel=1e-9)
    assert abs(result['residual']) < 1e-9
    assert len(result['numericalObjectHash']) == 64


def test_root_bracket_rejects_interval_without_sign_change():
    with pytest.raises(ValueError):
        root_object(RootInput(expression='x^2+1', bracket=[-2, 2], method='brentq'))


def test_adaptive_quadrature_integrates_sine_to_two():
    result = integration_object(IntegrationInput(expression='sin(x)', lower=0, upper=math.pi, method='adaptive'))['result']
    assert result['value'] == pytest.approx(2.0, abs=1e-10)
    assert result['estimatedAbsoluteError'] is not None
    assert len(result['curve']) > 20


def test_simpson_and_trapezoid_are_available_and_reasonable():
    simpson = integration_object(IntegrationInput(expression='x^2', lower=0, upper=3, method='simpson', samples=401))['result']
    trapezoid = integration_object(IntegrationInput(expression='x^2', lower=0, upper=3, method='trapezoid', samples=401))['result']
    assert simpson['value'] == pytest.approx(9.0, abs=1e-10)
    assert trapezoid['value'] == pytest.approx(9.0, rel=1e-4)


def test_five_point_finite_difference_matches_symbolic_derivative():
    result = differentiation_object(DifferentiationInput(expression='sin(x)', x=0.7, order=1, step=1e-4))['result']
    assert result['finiteDifferenceValue'] == pytest.approx(math.cos(0.7), rel=1e-8)
    assert result['symbolicValue'] == pytest.approx(math.cos(0.7), rel=1e-10)
    assert result['absoluteDifferenceFromSymbolic'] < 1e-8


def test_pchip_interpolation_preserves_source_points_and_samples_curve():
    payload = InterpolationInput(xValues=[0, 1, 2, 3], yValues=[0, 1, 0, 1], method='pchip', evaluateAt=[1.5], outputSamples=61)
    result = interpolation_object(payload)['result']
    assert result['method'] == 'pchip'
    assert len(result['inputPoints']) == 4
    assert len(result['curve']) == 61
    assert math.isfinite(result['evaluatedPoints'][0]['y'])
    assert len(result['numericalObjectHash']) == 64


def test_interpolation_rejects_duplicate_x_values():
    with pytest.raises(ValueError):
        InterpolationInput(xValues=[0, 1, 1], yValues=[0, 1, 2])


def test_ode_solver_matches_exponential_decay():
    payload = ODEInput(equations=['-0.5*y'], stateNames=['y'], initialValues=[2.0], tMin=0, tMax=4, samples=81, method='RK45')
    result = ode_object(payload)['result']
    assert result['successful'] is True
    assert result['finalState']['y'] == pytest.approx(2 * math.exp(-2), rel=2e-5)
    assert result['functionEvaluations'] > 0
    assert len(result['series'][0]['points']) == 81


def test_ode_rejects_unapproved_expression_function():
    with pytest.raises(Exception):
        ode_object(ODEInput(equations=['__import__(1)'], stateNames=['y'], initialValues=[1], tMin=0, tMax=1))


def test_linear_solve_reports_solution_rank_condition_and_residual():
    result = linear_algebra_object(LinearAlgebraInput(operation='solve', matrix=[[3, 2], [1, 2]], vector=[5, 5]))['result']
    assert result['solution'] == pytest.approx([0.0, 2.5])
    assert result['rank'] == 2
    assert result['residualNorm'] < 1e-12
    assert result['conditionNumber'] is not None


def test_eigen_and_svd_paths_return_canonical_results():
    eigen = linear_algebra_object(LinearAlgebraInput(operation='eigen', matrix=[[2, 0], [0, 3]]))['result']
    values = sorted(round(v['real'], 8) for v in eigen['eigenvalues'])
    assert values == [2.0, 3.0]
    svd = linear_algebra_object(LinearAlgebraInput(operation='svd', matrix=[[3, 0], [0, 2]]))['result']
    assert svd['singularValues'] == pytest.approx([3.0, 2.0])
    assert len(svd['numericalObjectHash']) == 64


def test_least_squares_reports_small_best_fit_residual():
    result = linear_algebra_object(LinearAlgebraInput(operation='least-squares', matrix=[[1, 0], [1, 1], [1, 2]], vector=[1, 2, 2.9]))['result']
    assert len(result['solution']) == 2
    assert result['leastSquaresRank'] == 2
    assert result['residualNorm'] < 0.1


def test_bounded_multivariable_optimization_finds_quadratic_minimum():
    payload = OptimizationInput(
        expression='(x-2)^2 + (y+1)^2',
        variables=['x', 'y'],
        initial=[0, 0],
        bounds=[[-5, 5], [-5, 5]],
        goal='minimize',
    )
    result = optimization_object(payload)['result']
    assert result['success'] is True
    assert result['point']['x'] == pytest.approx(2.0, abs=2e-5)
    assert result['point']['y'] == pytest.approx(-1.0, abs=2e-5)
    assert result['value'] == pytest.approx(0.0, abs=1e-9)


def test_optimization_rejects_unsafe_expression():
    with pytest.raises(Exception):
        optimization_object(OptimizationInput(expression='open(x)', variables=['x'], initial=[0], bounds=[[-1, 1]]))
