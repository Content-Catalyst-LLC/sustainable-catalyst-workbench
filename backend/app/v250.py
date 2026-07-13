"""Workbench v2.5.0 simulation, digital-twin, and systems-modeling routes."""
from __future__ import annotations

from datetime import datetime, timezone
from math import cos, log, pi, sqrt
from random import Random
from statistics import mean, stdev
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.5.0"
router = APIRouter(prefix="/v250", tags=["workbench-v250"])


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    center = mean(values)
    return sum((value - center) ** 2 for value in values) / (len(values) - 1)


def quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return float("nan")
    index = (len(ordered) - 1) * probability
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = index - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def linear_fit(x: list[float], y: list[float]) -> dict[str, object]:
    count = min(len(x), len(y))
    if count < 2:
        return {"slope": None, "intercept": None, "r2": None, "rmse": None, "residuals": []}
    x = x[:count]
    y = y[:count]
    mx = mean(x)
    my = mean(y)
    sxx = sum((value - mx) ** 2 for value in x)
    syy = sum((value - my) ** 2 for value in y)
    sxy = sum((x[index] - mx) * (y[index] - my) for index in range(count))
    slope = sxy / sxx if sxx else 0.0
    intercept = my - slope * mx
    residuals = [y[index] - (slope * x[index] + intercept) for index in range(count)]
    sse = sum(value * value for value in residuals)
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": 1 - sse / syy if syy else 1.0,
        "rmse": sqrt(sse / count),
        "residuals": residuals,
    }


class SimulationRequest(BaseModel):
    model_type: Literal["first_order", "logistic", "damped"] = "first_order"
    solver: Literal["euler", "rk4"] = "rk4"
    initial_state: float = 0.0
    input_value: float = 10.0
    gain: float = 1.5
    time_constant: float = Field(default=4.0, gt=0)
    capacity: float = 100.0
    time_step: float = Field(default=0.1, gt=0)
    duration: float = Field(default=30.0, gt=0)


class TwinSample(BaseModel):
    time: float
    input: float
    observed: float


class TwinRequest(BaseModel):
    name: str = "Digital twin"
    initial_state: float
    gain: float
    time_constant: float = Field(gt=0)
    search_percent: float = Field(default=40.0, ge=0, le=90)
    samples: list[TwinSample]


class SystemsRequest(BaseModel):
    matrix_a: list[list[float]]
    initial_state: list[float]
    input_vector: list[float]
    state_names: list[str] = []
    solver: Literal["euler", "rk4"] = "rk4"
    time_step: float = Field(default=0.1, gt=0)
    duration: float = Field(default=30.0, gt=0)


class SweepRequest(BaseModel):
    model_type: Literal["first_order", "logistic", "linear"] = "first_order"
    parameter: Literal["gain", "time_constant", "input_value", "capacity", "coefficient"] = "gain"
    minimum: float
    maximum: float
    steps: int = Field(default=21, ge=2, le=501)
    input_value: float = 10.0
    gain: float = 1.5
    time_constant: float = Field(default=4.0, gt=0)
    capacity: float = 100.0
    duration: float = Field(default=30.0, gt=0)


class UncertainVariable(BaseModel):
    name: str
    mean: float
    standard_deviation: float = Field(ge=0)
    minimum: float
    maximum: float
    distribution: Literal["normal", "uniform", "triangular"] = "normal"


class MonteCarloRequest(BaseModel):
    runs: int = Field(default=5000, ge=100, le=100000)
    seed: int = 2026
    intercept: float = 0.0
    threshold: float = 0.0
    variables: list[UncertainVariable]
    coefficients: dict[str, float]


class ValidationRequest(BaseModel):
    observed: list[float]
    predicted: list[float]
    maximum_rmse: float = Field(gt=0)
    maximum_absolute_bias: float = Field(ge=0)
    minimum_r2: float = Field(default=0.95, ge=-1, le=1)
    maximum_mape_percent: float = Field(default=10.0, ge=0)
    fit_linear_correction: bool = True


def derivative(model_type: str, state: tuple[float, float], request: SimulationRequest) -> tuple[float, float]:
    x, velocity = state
    if model_type == "logistic":
        return request.gain * x * (1 - x / max(request.capacity, 1e-12)), 0.0
    if model_type == "damped":
        return velocity, request.input_value - 2 * max(request.time_constant, 0) * velocity - request.capacity**2 * x
    return (request.gain * request.input_value - x) / request.time_constant, 0.0


def integrate(request: SimulationRequest) -> dict[str, list[float]]:
    steps = min(20000, max(1, int(request.duration / request.time_step + 0.999999)))
    x = request.initial_state
    velocity = 0.0
    times = [0.0]
    values = [x]
    velocities = [velocity]
    for index in range(steps):
        dt = request.time_step
        if request.solver == "euler":
            dx, dv = derivative(request.model_type, (x, velocity), request)
            x += dt * dx
            velocity += dt * dv
        else:
            k1 = derivative(request.model_type, (x, velocity), request)
            k2 = derivative(request.model_type, (x + dt * k1[0] / 2, velocity + dt * k1[1] / 2), request)
            k3 = derivative(request.model_type, (x + dt * k2[0] / 2, velocity + dt * k2[1] / 2), request)
            k4 = derivative(request.model_type, (x + dt * k3[0], velocity + dt * k3[1]), request)
            x += dt * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]) / 6
            velocity += dt * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]) / 6
        times.append(min(request.duration, (index + 1) * dt))
        values.append(x)
        velocities.append(velocity)
        if abs(x) > 1e12:
            break
    return {"time": times, "values": values, "velocity": velocities}


@router.post("/simulation/run")
def run_simulation(request: SimulationRequest) -> dict[str, object]:
    series = integrate(request)
    findings: list[dict[str, object]] = []
    if request.model_type == "logistic" and request.capacity <= 0:
        findings.append({"severity": "error", "code": "invalid-capacity"})
    if request.solver == "euler" and request.time_step > request.time_constant / 2:
        findings.append({"severity": "warning", "code": "euler-step-large"})
    if abs(series["values"][-1]) > 1e11:
        findings.append({"severity": "error", "code": "diverged"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-dynamic-simulation/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "modelType": request.model_type,
        "solver": request.solver,
        "series": series,
        "metrics": {
            "steps": len(series["values"]) - 1,
            "finalState": series["values"][-1],
            "minimum": min(series["values"]),
            "maximum": max(series["values"]),
        },
        "findings": findings,
    }


def simulate_twin(samples: list[TwinSample], initial: float, gain: float, time_constant: float) -> list[float]:
    state = initial
    predicted = [state]
    for previous, current in zip(samples, samples[1:]):
        dt = max(current.time - previous.time, 1e-9)
        state += dt * ((gain * previous.input - state) / max(time_constant, 1e-9))
        predicted.append(state)
    return predicted


@router.post("/digital-twin/evaluate")
def evaluate_twin(request: TwinRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    if len(request.samples) < 3:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "insufficient-data"}]}
    for previous, current in zip(request.samples, request.samples[1:]):
        if current.time <= previous.time:
            findings.append({"severity": "error", "code": "non-monotonic-time"})
    observed = [sample.observed for sample in request.samples]
    span = request.search_percent / 100
    best: dict[str, object] | None = None
    for gain_index in range(21):
        gain = request.gain * (1 - span + 2 * span * gain_index / 20)
        for tau_index in range(21):
            tau = max(1e-6, request.time_constant * (1 - span + 2 * span * tau_index / 20))
            predicted = simulate_twin(request.samples, request.initial_state, gain, tau)
            residuals = [observed[index] - predicted[index] for index in range(len(observed))]
            rmse = sqrt(mean([value * value for value in residuals]))
            if best is None or rmse < float(best["rmse"]):
                fit = linear_fit(observed, predicted)
                best = {
                    "gain": gain,
                    "timeConstant": tau,
                    "predicted": predicted,
                    "residuals": residuals,
                    "rmse": rmse,
                    "mae": mean([abs(value) for value in residuals]),
                    "bias": mean(residuals),
                    "r2": fit["r2"],
                }
    assert best is not None
    if float(best["r2"] or 0) < 0.8:
        findings.append({"severity": "warning", "code": "low-r2"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-digital-twin-evaluation/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "name": request.name,
        "calibrated": {"gain": best["gain"], "timeConstant": best["timeConstant"]},
        "metrics": {key: best[key] for key in ("rmse", "mae", "bias", "r2")},
        "series": {"time": [sample.time for sample in request.samples], "observed": observed, "predicted": best["predicted"]},
        "findings": findings,
    }


def matrix_vector(matrix: list[list[float]], vector: list[float]) -> list[float]:
    return [sum(value * vector[index] for index, value in enumerate(row)) for row in matrix]


def vector_add(left: list[float], right: list[float], scale: float = 1.0) -> list[float]:
    return [value + scale * right[index] for index, value in enumerate(left)]


@router.post("/systems/simulate")
def simulate_system(request: SystemsRequest) -> dict[str, object]:
    count = len(request.initial_state)
    findings: list[dict[str, object]] = []
    if not count or len(request.matrix_a) != count or any(len(row) != count for row in request.matrix_a):
        findings.append({"severity": "error", "code": "matrix-dimension-mismatch"})
    if len(request.input_vector) != count:
        findings.append({"severity": "error", "code": "input-dimension-mismatch"})
    if findings:
        return {"ok": False, "version": VERSION, "findings": findings}
    state = list(request.initial_state)
    series = [[value] for value in state]
    steps = min(20000, max(1, int(request.duration / request.time_step + 0.999999)))

    def derivative(values: list[float]) -> list[float]:
        return vector_add(matrix_vector(request.matrix_a, values), request.input_vector)

    for _ in range(steps):
        dt = request.time_step
        if request.solver == "euler":
            state = vector_add(state, derivative(state), dt)
        else:
            k1 = derivative(state)
            k2 = derivative(vector_add(state, k1, dt / 2))
            k3 = derivative(vector_add(state, k2, dt / 2))
            k4 = derivative(vector_add(state, k3, dt))
            state = [state[index] + dt * (k1[index] + 2 * k2[index] + 2 * k3[index] + k4[index]) / 6 for index in range(count)]
        for index, value in enumerate(state):
            series[index].append(value)
        if any(abs(value) > 1e12 for value in state):
            findings.append({"severity": "error", "code": "diverged"})
            break
    right_bounds = [request.matrix_a[index][index] + sum(abs(value) for column, value in enumerate(row) if column != index) for index, row in enumerate(request.matrix_a)]
    if any(value > 0 for value in right_bounds):
        findings.append({"severity": "warning", "code": "stability-not-established", "gershgorinRightBounds": right_bounds})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-linear-systems-model/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "stateNames": request.state_names,
        "series": series,
        "finalState": state,
        "gershgorinRightBounds": right_bounds,
        "findings": findings,
    }


@router.post("/scenarios/sweep")
def sweep_scenarios(request: SweepRequest) -> dict[str, object]:
    if request.maximum <= request.minimum:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "invalid-range"}]}
    parameter_values: list[float] = []
    outcomes: list[float] = []
    for index in range(request.steps):
        value = request.minimum + (request.maximum - request.minimum) * index / (request.steps - 1)
        parameters = request.model_dump()
        parameters[request.parameter] = value
        if request.model_type == "linear":
            outcome = float(parameters.get("coefficient", request.gain)) * float(parameters["input_value"])
        else:
            simulation = SimulationRequest(
                model_type=request.model_type,
                solver="rk4",
                initial_state=1.0,
                input_value=float(parameters["input_value"]),
                gain=float(parameters["gain"]),
                time_constant=max(float(parameters["time_constant"]), 1e-6),
                capacity=float(parameters["capacity"]),
                time_step=0.05,
                duration=request.duration,
            )
            outcome = integrate(simulation)["values"][-1]
        parameter_values.append(value)
        outcomes.append(outcome)
    fit = linear_fit(parameter_values, outcomes)
    findings: list[dict[str, object]] = []
    if float(fit["r2"] or 0) < 0.8:
        findings.append({"severity": "warning", "code": "nonlinear-response"})
    return {
        "ok": True,
        "schema": "sc-workbench-scenario-sweep/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "parameter": request.parameter,
        "parameterValues": parameter_values,
        "outcomes": outcomes,
        "metrics": {
            "minimumOutcome": min(outcomes),
            "maximumOutcome": max(outcomes),
            "outcomeSpan": max(outcomes) - min(outcomes),
            "linearSensitivity": fit["slope"],
            "sweepR2": fit["r2"],
        },
        "findings": findings,
    }


def sample_variable(random: Random, variable: UncertainVariable) -> float:
    if variable.distribution == "uniform":
        value = random.uniform(variable.minimum, variable.maximum)
    elif variable.distribution == "triangular":
        value = random.triangular(variable.minimum, variable.maximum, min(variable.maximum, max(variable.minimum, variable.mean)))
    else:
        value = random.gauss(variable.mean, variable.standard_deviation)
    return min(variable.maximum, max(variable.minimum, value))


@router.post("/monte-carlo/run")
def run_monte_carlo(request: MonteCarloRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    if not request.variables:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "no-variables"}]}
    for variable in request.variables:
        if variable.maximum <= variable.minimum:
            findings.append({"severity": "error", "code": "invalid-bounds", "variable": variable.name})
    if findings:
        return {"ok": False, "version": VERSION, "findings": findings}
    random = Random(request.seed)
    outputs: list[float] = []
    samples: dict[str, list[float]] = {variable.name: [] for variable in request.variables}
    for _ in range(request.runs):
        outcome = request.intercept
        for variable in request.variables:
            value = sample_variable(random, variable)
            samples[variable.name].append(value)
            outcome += request.coefficients.get(variable.name, 0.0) * value
        outputs.append(outcome)
    sensitivity = []
    for variable in request.variables:
        fit = linear_fit(samples[variable.name], outputs)
        sensitivity.append({"name": variable.name, "slope": fit["slope"], "r2": fit["r2"]})
    sensitivity.sort(key=lambda item: abs(float(item["r2"] or 0)), reverse=True)
    if request.runs < 1000:
        findings.append({"severity": "warning", "code": "low-run-count"})
    return {
        "ok": True,
        "schema": "sc-workbench-monte-carlo-uncertainty/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "runs": request.runs,
        "seed": request.seed,
        "metrics": {
            "mean": mean(outputs),
            "standardDeviation": stdev(outputs) if len(outputs) > 1 else 0.0,
            "p05": quantile(outputs, 0.05),
            "median": quantile(outputs, 0.5),
            "p95": quantile(outputs, 0.95),
            "thresholdExceedancePercent": sum(value >= request.threshold for value in outputs) / len(outputs) * 100,
        },
        "sensitivity": sensitivity,
        "findings": findings,
    }


@router.post("/models/validate")
def validate_model(request: ValidationRequest) -> dict[str, object]:
    if len(request.observed) != len(request.predicted) or len(request.observed) < 3:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "invalid-pair-count"}]}
    residuals = [request.observed[index] - request.predicted[index] for index in range(len(request.observed))]
    rmse = sqrt(mean([value * value for value in residuals]))
    mae = mean([abs(value) for value in residuals])
    bias = mean(residuals)
    nonzero_pairs = [(observed, predicted) for observed, predicted in zip(request.observed, request.predicted) if observed != 0]
    mape = mean([abs((observed - predicted) / observed) for observed, predicted in nonzero_pairs]) * 100 if nonzero_pairs else 0.0
    agreement = linear_fit(request.observed, request.predicted)
    correction = linear_fit(request.predicted, request.observed) if request.fit_linear_correction else None
    findings: list[dict[str, object]] = []
    if rmse > request.maximum_rmse:
        findings.append({"severity": "error", "code": "rmse-fail", "value": rmse})
    if abs(bias) > request.maximum_absolute_bias:
        findings.append({"severity": "error", "code": "bias-fail", "value": bias})
    if float(agreement["r2"] or 0) < request.minimum_r2:
        findings.append({"severity": "error", "code": "r2-fail", "value": agreement["r2"]})
    if mape > request.maximum_mape_percent:
        findings.append({"severity": "error", "code": "mape-fail", "value": mape})
    residual_trend = linear_fit(request.observed, residuals)
    if abs(float(residual_trend["r2"] or 0)) > 0.5:
        findings.append({"severity": "warning", "code": "residual-trend"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-model-validation/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "metrics": {"rmse": rmse, "mae": mae, "bias": bias, "mapePercent": mape, "r2": agreement["r2"]},
        "linearCorrection": correction,
        "residuals": residuals,
        "findings": findings,
    }
