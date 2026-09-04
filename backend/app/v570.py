"""Workbench v5.7.0 — Signals, Systems & Control Mathematics.

Bounded signal analysis, digital filter design, continuous-time transfer-function
and state-space analysis, root-locus construction, convolution, and PID closed-
loop simulation. Inputs are numeric arrays and bounded method selectors only.
No Python eval/exec, shell execution, arbitrary callable upload, or device
execution is exposed.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

import numpy as np
import scipy
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from scipy import signal as scipy_signal

from app.v510 import content_hash

VERSION = "5.7.0"
SCHEMA = "sc-workbench-signals-controls-object/1.0"
MAX_SIGNAL_SAMPLES = 8192
MAX_CONV_SAMPLES = 4096
MAX_COEFFICIENTS = 32
MAX_FILTER_ORDER = 12
MAX_STATE_DIM = 8
MAX_RESPONSE_POINTS = 1201
MAX_ROOT_LOCUS_POINTS = 121
MAX_SPECTRUM_POINTS = 1025

router = APIRouter(prefix="/v570", tags=["workbench-v570-signals-systems-controls"])


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite.")
    return number


def _finite_list(values: Sequence[float], label: str, minimum: int = 1) -> List[float]:
    if len(values) < minimum:
        raise ValueError(f"{label} requires at least {minimum} value(s).")
    return [_finite(value, f"{label}[{idx}]") for idx, value in enumerate(values)]


def _clean_poly(values: Sequence[float], label: str) -> np.ndarray:
    coeffs = np.asarray(_finite_list(values, label), dtype=float)
    if len(coeffs) > MAX_COEFFICIENTS:
        raise ValueError(f"{label} is limited to {MAX_COEFFICIENTS} coefficients.")
    nz = np.flatnonzero(np.abs(coeffs) > 1e-15)
    if len(nz) == 0:
        raise ValueError(f"{label} cannot be the zero polynomial.")
    return coeffs[int(nz[0]):]


def _complex_record(value: complex) -> Dict[str, float]:
    return {
        "real": round(float(np.real(value)), 12),
        "imag": round(float(np.imag(value)), 12),
    }


def _record(kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema": SCHEMA,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "deviceExecutionAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
    }
    value["signalsControlObjectHash"] = content_hash(value)
    return value


def _series(x: Sequence[float], y: Sequence[float], x_key: str = "x", y_key: str = "y", cap: int = MAX_RESPONSE_POINTS) -> List[Dict[str, float]]:
    count = min(len(x), len(y))
    if count == 0:
        return []
    stride = max(1, math.ceil(count / cap))
    points = []
    for idx in range(0, count, stride):
        xv = float(x[idx])
        yv = float(y[idx])
        if math.isfinite(xv) and math.isfinite(yv):
            points.append({x_key: round(xv, 12), y_key: round(yv, 12)})
    if points and (count - 1) % stride != 0:
        xv = float(x[count - 1])
        yv = float(y[count - 1])
        if math.isfinite(xv) and math.isfinite(yv):
            points.append({x_key: round(xv, 12), y_key: round(yv, 12)})
    return points


def _tf(num: Sequence[float], den: Sequence[float]):
    numerator = _clean_poly(num, "numerator")
    denominator = _clean_poly(den, "denominator")
    system = scipy_signal.TransferFunction(numerator, denominator)
    return numerator, denominator, system


def _stability_from_poles(poles: Sequence[complex], discrete: bool = False) -> bool:
    if discrete:
        return all(abs(complex(pole)) < 1.0 - 1e-12 for pole in poles)
    return all(float(np.real(pole)) < -1e-12 for pole in poles)


class SpectrumInput(BaseModel):
    values: List[float] = Field(min_length=8, max_length=MAX_SIGNAL_SAMPLES)
    sampleRateHz: float = Field(gt=0, le=1e9)
    window: Literal["hann", "hamming", "blackman", "rectangular"] = "hann"
    detrend: Literal["none", "constant", "linear"] = "constant"
    peakCount: int = Field(default=5, ge=1, le=12)

    @model_validator(mode="after")
    def validate_values(self):
        _finite_list(self.values, "values", 8)
        return self


class ConvolutionInput(BaseModel):
    signal: List[float] = Field(min_length=1, max_length=MAX_CONV_SAMPLES)
    kernel: List[float] = Field(min_length=1, max_length=MAX_CONV_SAMPLES)
    mode: Literal["full", "same", "valid"] = "full"
    normalizeKernel: bool = False

    @model_validator(mode="after")
    def validate_convolution(self):
        _finite_list(self.signal, "signal")
        kernel = _finite_list(self.kernel, "kernel")
        if self.normalizeKernel and abs(sum(kernel)) < 1e-15:
            raise ValueError("Kernel sum must be non-zero when normalizeKernel is enabled.")
        return self


class FilterDesignInput(BaseModel):
    family: Literal["butterworth", "chebyshev1"] = "butterworth"
    response: Literal["lowpass", "highpass", "bandpass", "bandstop"] = "lowpass"
    order: int = Field(default=4, ge=1, le=MAX_FILTER_ORDER)
    sampleRateHz: float = Field(default=1000.0, gt=0, le=1e9)
    cutoffHz: List[float] = Field(default_factory=lambda: [100.0], min_length=1, max_length=2)
    rippleDb: float = Field(default=1.0, gt=0, le=20)
    responsePoints: int = Field(default=401, ge=64, le=MAX_RESPONSE_POINTS)

    @model_validator(mode="after")
    def validate_filter(self):
        cuts = sorted(_finite_list(self.cutoffHz, "cutoffHz"))
        nyquist = self.sampleRateHz / 2.0
        if self.response in {"lowpass", "highpass"} and len(cuts) != 1:
            raise ValueError(f"{self.response} requires exactly one cutoff frequency.")
        if self.response in {"bandpass", "bandstop"} and len(cuts) != 2:
            raise ValueError(f"{self.response} requires two cutoff frequencies.")
        if any(cut <= 0 or cut >= nyquist for cut in cuts):
            raise ValueError("Every cutoff frequency must lie strictly between 0 and Nyquist.")
        if len(cuts) == 2 and cuts[0] >= cuts[1]:
            raise ValueError("Band cutoff frequencies must be strictly increasing.")
        return self


class TransferFunctionInput(BaseModel):
    numerator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    denominator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    frequencyMinHz: float = Field(default=0.01, gt=0, le=1e9)
    frequencyMaxHz: float = Field(default=100.0, gt=0, le=1e9)
    frequencyPoints: int = Field(default=401, ge=32, le=MAX_RESPONSE_POINTS)
    timeDurationS: float = Field(default=10.0, gt=0, le=10000)
    timeSamples: int = Field(default=501, ge=32, le=MAX_RESPONSE_POINTS)
    includeImpulse: bool = False

    @model_validator(mode="after")
    def validate_tf(self):
        _clean_poly(self.numerator, "numerator")
        _clean_poly(self.denominator, "denominator")
        if self.frequencyMinHz >= self.frequencyMaxHz:
            raise ValueError("frequencyMinHz must be less than frequencyMaxHz.")
        return self


class StateSpaceInput(BaseModel):
    A: List[List[float]] = Field(min_length=1, max_length=MAX_STATE_DIM)
    B: List[float] = Field(min_length=1, max_length=MAX_STATE_DIM)
    C: List[float] = Field(min_length=1, max_length=MAX_STATE_DIM)
    D: float = 0.0
    durationS: float = Field(default=10.0, gt=0, le=10000)
    samples: int = Field(default=501, ge=32, le=MAX_RESPONSE_POINTS)

    @model_validator(mode="after")
    def validate_state_space(self):
        n = len(self.A)
        if n > MAX_STATE_DIM:
            raise ValueError(f"State dimension is limited to {MAX_STATE_DIM}.")
        if any(len(row) != n for row in self.A):
            raise ValueError("A must be square.")
        if len(self.B) != n or len(self.C) != n:
            raise ValueError("B and C must contain one value per state.")
        for row in self.A:
            _finite_list(row, "A row")
        _finite_list(self.B, "B")
        _finite_list(self.C, "C")
        _finite(self.D, "D")
        return self


class PIDInput(BaseModel):
    plantNumerator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    plantDenominator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    kp: float = Field(default=1.0, ge=0, le=1e9)
    ki: float = Field(default=0.0, ge=0, le=1e9)
    kd: float = Field(default=0.0, ge=0, le=1e9)
    setpoint: float = 1.0
    durationS: float = Field(default=10.0, gt=0, le=10000)
    samples: int = Field(default=601, ge=64, le=MAX_RESPONSE_POINTS)
    settlingBandPercent: float = Field(default=2.0, gt=0, le=20)

    @model_validator(mode="after")
    def validate_pid(self):
        _clean_poly(self.plantNumerator, "plantNumerator")
        _clean_poly(self.plantDenominator, "plantDenominator")
        if self.kp == 0 and self.ki == 0 and self.kd == 0:
            raise ValueError("At least one PID gain must be non-zero.")
        _finite(self.setpoint, "setpoint")
        return self


class RootLocusInput(BaseModel):
    numerator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    denominator: List[float] = Field(min_length=1, max_length=MAX_COEFFICIENTS)
    gainMin: float = Field(default=0.0, ge=0, le=1e9)
    gainMax: float = Field(default=100.0, gt=0, le=1e9)
    gainPoints: int = Field(default=61, ge=2, le=MAX_ROOT_LOCUS_POINTS)

    @model_validator(mode="after")
    def validate_root_locus(self):
        _clean_poly(self.numerator, "numerator")
        _clean_poly(self.denominator, "denominator")
        if self.gainMin >= self.gainMax:
            raise ValueError("gainMin must be less than gainMax.")
        return self


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-signals-systems-controls-status/1.0",
        "version": VERSION,
        "engine": "NumPy + SciPy Signal",
        "numpyVersion": np.__version__,
        "scipyVersion": scipy.__version__,
        "capabilities": [
            "fft-spectrum-analysis",
            "window-functions",
            "power-spectral-density",
            "harmonic-analysis",
            "discrete-convolution",
            "digital-filter-design",
            "filter-frequency-response",
            "continuous-transfer-functions",
            "bode-response",
            "step-and-impulse-response",
            "pole-zero-analysis",
            "root-locus",
            "state-space-analysis",
            "controllability-observability",
            "pid-closed-loop-simulation",
            "control-performance-metrics",
            "canonical-signals-control-objects",
        ],
        "limits": {
            "maxSignalSamples": MAX_SIGNAL_SAMPLES,
            "maxFilterOrder": MAX_FILTER_ORDER,
            "maxStateDimension": MAX_STATE_DIM,
            "maxResponsePoints": MAX_RESPONSE_POINTS,
            "maxRootLocusPoints": MAX_ROOT_LOCUS_POINTS,
        },
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "deviceExecutionAuthorized": False,
    }


def spectrum_object(payload: SpectrumInput) -> Dict[str, Any]:
    values = np.asarray(payload.values, dtype=float)
    sample_rate = float(payload.sampleRateHz)
    if payload.detrend == "none":
        processed = values.copy()
    else:
        processed = scipy_signal.detrend(values, type=payload.detrend)
    window_name = "boxcar" if payload.window == "rectangular" else payload.window
    window = scipy_signal.get_window(window_name, len(processed), fftbins=True)
    windowed = processed * window
    spectrum = np.fft.rfft(windowed)
    frequencies = np.fft.rfftfreq(len(windowed), d=1.0 / sample_rate)
    coherent_gain = float(np.sum(window))
    amplitudes = np.abs(spectrum) / max(coherent_gain, 1e-15)
    if len(amplitudes) > 1:
        amplitudes[1:-1 if len(processed) % 2 == 0 else None] *= 2.0
    power = (np.abs(spectrum) ** 2) / max(sample_rate * float(np.sum(window ** 2)), 1e-15)
    if len(power) > 1:
        power[1:-1 if len(processed) % 2 == 0 else None] *= 2.0
    phase = np.angle(spectrum)

    candidate = np.arange(1, len(amplitudes))
    if len(candidate):
        local_peaks, _ = scipy_signal.find_peaks(amplitudes[1:])
        peak_indices = local_peaks + 1
        if len(peak_indices) == 0:
            peak_indices = candidate
        peak_indices = peak_indices[np.argsort(amplitudes[peak_indices])[::-1]][: payload.peakCount]
    else:
        peak_indices = np.asarray([], dtype=int)
    peaks = [
        {
            "frequencyHz": round(float(frequencies[idx]), 12),
            "amplitude": round(float(amplitudes[idx]), 12),
            "phaseRad": round(float(phase[idx]), 12),
        }
        for idx in peak_indices
    ]

    thd = None
    fundamental_hz = None
    if len(peak_indices):
        fundamental_idx = int(peak_indices[0])
        fundamental_amp = float(amplitudes[fundamental_idx])
        fundamental_hz = float(frequencies[fundamental_idx])
        if fundamental_amp > 1e-15 and fundamental_hz > 0:
            harmonic_sq = 0.0
            for harmonic in range(2, 6):
                target = fundamental_hz * harmonic
                if target > sample_rate / 2:
                    break
                idx = int(np.argmin(np.abs(frequencies - target)))
                harmonic_sq += float(amplitudes[idx]) ** 2
            thd = math.sqrt(harmonic_sq) / fundamental_amp

    stride = max(1, math.ceil(len(frequencies) / MAX_SPECTRUM_POINTS))
    points = []
    for idx in range(0, len(frequencies), stride):
        points.append({
            "frequencyHz": round(float(frequencies[idx]), 12),
            "amplitude": round(float(amplitudes[idx]), 12),
            "powerSpectralDensity": round(float(power[idx]), 16),
            "phaseRad": round(float(phase[idx]), 12),
        })
    rms = float(np.sqrt(np.mean(values ** 2)))
    result = _record(
        "spectrum",
        payload.model_dump(),
        {
            "sampleCount": int(len(values)),
            "sampleRateHz": sample_rate,
            "nyquistHz": sample_rate / 2.0,
            "rms": round(rms, 12),
            "window": payload.window,
            "detrend": payload.detrend,
            "fundamentalHz": None if fundamental_hz is None else round(fundamental_hz, 12),
            "totalHarmonicDistortionRatio": None if thd is None else round(thd, 12),
            "peaks": peaks,
            "spectrum": points,
        },
    )
    return {"ok": True, "result": result}


def convolution_object(payload: ConvolutionInput) -> Dict[str, Any]:
    source = np.asarray(payload.signal, dtype=float)
    kernel = np.asarray(payload.kernel, dtype=float)
    if payload.normalizeKernel:
        kernel = kernel / float(np.sum(kernel))
    output = np.convolve(source, kernel, mode=payload.mode)
    result = _record(
        "convolution",
        payload.model_dump(),
        {
            "mode": payload.mode,
            "normalizedKernel": bool(payload.normalizeKernel),
            "kernelUsed": kernel.round(12).tolist(),
            "output": output.round(12).tolist(),
            "inputEnergy": round(float(np.sum(source ** 2)), 12),
            "outputEnergy": round(float(np.sum(output ** 2)), 12),
        },
    )
    return {"ok": True, "result": result}


def filter_design_object(payload: FilterDesignInput) -> Dict[str, Any]:
    cuts = sorted(float(value) for value in payload.cutoffHz)
    btype = payload.response
    if payload.family == "butterworth":
        sos = scipy_signal.butter(payload.order, cuts if len(cuts) == 2 else cuts[0], btype=btype, output="sos", fs=payload.sampleRateHz)
    else:
        sos = scipy_signal.cheby1(payload.order, payload.rippleDb, cuts if len(cuts) == 2 else cuts[0], btype=btype, output="sos", fs=payload.sampleRateHz)
    frequencies, response = scipy_signal.sosfreqz(sos, worN=payload.responsePoints, fs=payload.sampleRateHz)
    magnitude = 20 * np.log10(np.maximum(np.abs(response), 1e-15))
    phase = np.degrees(np.unwrap(np.angle(response)))
    zeros, poles, gain = scipy_signal.sos2zpk(sos)
    response_points = [
        {
            "frequencyHz": round(float(f), 12),
            "magnitudeDb": round(float(m), 12),
            "phaseDeg": round(float(p), 12),
        }
        for f, m, p in zip(frequencies, magnitude, phase)
    ]
    result = _record(
        "filter-design",
        payload.model_dump(),
        {
            "family": payload.family,
            "responseType": payload.response,
            "order": payload.order,
            "sampleRateHz": float(payload.sampleRateHz),
            "nyquistHz": float(payload.sampleRateHz) / 2.0,
            "cutoffHz": cuts,
            "secondOrderSections": np.asarray(sos).round(14).tolist(),
            "zeros": [_complex_record(value) for value in zeros],
            "poles": [_complex_record(value) for value in poles],
            "gain": round(float(np.real(gain)), 14),
            "stable": _stability_from_poles(poles, discrete=True),
            "frequencyResponse": response_points,
        },
    )
    return {"ok": True, "result": result}


def transfer_function_object(payload: TransferFunctionInput) -> Dict[str, Any]:
    numerator, denominator, system = _tf(payload.numerator, payload.denominator)
    zeros, poles, gain = scipy_signal.tf2zpk(numerator, denominator)
    frequencies = np.logspace(math.log10(payload.frequencyMinHz), math.log10(payload.frequencyMaxHz), payload.frequencyPoints)
    _, response = scipy_signal.freqresp(system, w=2 * math.pi * frequencies)
    magnitude = 20 * np.log10(np.maximum(np.abs(response), 1e-15))
    phase = np.degrees(np.unwrap(np.angle(response)))
    bode = [
        {
            "frequencyHz": round(float(f), 12),
            "magnitudeDb": round(float(m), 12),
            "phaseDeg": round(float(p), 12),
        }
        for f, m, p in zip(frequencies, magnitude, phase)
    ]
    t = np.linspace(0.0, payload.timeDurationS, payload.timeSamples)
    step_t, step_y = scipy_signal.step(system, T=t)
    impulse = []
    if payload.includeImpulse:
        imp_t, imp_y = scipy_signal.impulse(system, T=t)
        impulse = _series(imp_t, imp_y, "timeS", "value")
    dc_gain = None
    if abs(float(denominator[-1])) > 1e-15:
        dc_gain = float(numerator[-1]) / float(denominator[-1])
    result = _record(
        "transfer-function",
        payload.model_dump(),
        {
            "numerator": numerator.round(14).tolist(),
            "denominator": denominator.round(14).tolist(),
            "zeros": [_complex_record(value) for value in zeros],
            "poles": [_complex_record(value) for value in poles],
            "gain": round(float(np.real(gain)), 14),
            "stable": _stability_from_poles(poles),
            "dcGain": None if dc_gain is None or not math.isfinite(dc_gain) else round(dc_gain, 14),
            "bode": bode,
            "step": _series(step_t, step_y, "timeS", "value"),
            "impulse": impulse,
        },
    )
    return {"ok": True, "result": result}


def state_space_object(payload: StateSpaceInput) -> Dict[str, Any]:
    A = np.asarray(payload.A, dtype=float)
    B = np.asarray(payload.B, dtype=float).reshape(-1, 1)
    C = np.asarray(payload.C, dtype=float).reshape(1, -1)
    D = np.asarray([[float(payload.D)]], dtype=float)
    n = A.shape[0]
    controllability = np.hstack([np.linalg.matrix_power(A, power) @ B for power in range(n)])
    observability = np.vstack([C @ np.linalg.matrix_power(A, power) for power in range(n)])
    controllability_rank = int(np.linalg.matrix_rank(controllability))
    observability_rank = int(np.linalg.matrix_rank(observability))
    eigenvalues = np.linalg.eigvals(A)
    system = scipy_signal.StateSpace(A, B, C, D)
    t = np.linspace(0.0, payload.durationS, payload.samples)
    step_t, step_y = scipy_signal.step(system, T=t)
    step_y = np.asarray(step_y, dtype=float).reshape(-1)
    result = _record(
        "state-space",
        payload.model_dump(),
        {
            "stateDimension": int(n),
            "eigenvalues": [_complex_record(value) for value in eigenvalues],
            "stable": _stability_from_poles(eigenvalues),
            "controllabilityRank": controllability_rank,
            "observabilityRank": observability_rank,
            "fullyControllable": controllability_rank == n,
            "fullyObservable": observability_rank == n,
            "controllabilityMatrix": controllability.round(12).tolist(),
            "observabilityMatrix": observability.round(12).tolist(),
            "step": _series(step_t, step_y, "timeS", "value"),
        },
    )
    return {"ok": True, "result": result}


def _time_metrics(t: np.ndarray, y: np.ndarray, target: float, settling_band_percent: float) -> Dict[str, Any]:
    if len(t) == 0 or len(y) == 0:
        return {}
    final_value = float(y[-1])
    reference = abs(target) if abs(target) > 1e-12 else max(abs(final_value), 1.0)
    peak = float(np.max(y)) if target >= 0 else float(np.min(y))
    overshoot = max(0.0, ((peak - target) / reference) * 100.0) if target >= 0 else max(0.0, ((target - peak) / reference) * 100.0)
    low = target * 0.1
    high = target * 0.9
    if target < 0:
        low, high = high, low
    rise_start = None
    rise_end = None
    for idx, value in enumerate(y):
        if rise_start is None and ((target >= 0 and value >= low) or (target < 0 and value <= low)):
            rise_start = float(t[idx])
        if rise_end is None and ((target >= 0 and value >= high) or (target < 0 and value <= high)):
            rise_end = float(t[idx])
            break
    rise_time = None if rise_start is None or rise_end is None else max(0.0, rise_end - rise_start)
    band = reference * settling_band_percent / 100.0
    settling_time = None
    outside = np.where(np.abs(y - target) > band)[0]
    if len(outside) == 0:
        settling_time = 0.0
    elif int(outside[-1]) < len(t) - 1:
        settling_time = float(t[int(outside[-1]) + 1])
    error = target - y
    iae = float(np.trapezoid(np.abs(error), t))
    return {
        "finalValue": round(final_value, 12),
        "steadyStateError": round(float(target - final_value), 12),
        "peakValue": round(peak, 12),
        "overshootPercent": round(overshoot, 8),
        "riseTime10To90S": None if rise_time is None else round(rise_time, 12),
        "settlingTimeS": None if settling_time is None else round(settling_time, 12),
        "integralAbsoluteError": round(iae, 12),
    }


def pid_object(payload: PIDInput) -> Dict[str, Any]:
    plant_num = _clean_poly(payload.plantNumerator, "plantNumerator")
    plant_den = _clean_poly(payload.plantDenominator, "plantDenominator")
    controller_num = _clean_poly([payload.kd, payload.kp, payload.ki], "PID numerator")
    controller_den = np.asarray([1.0, 0.0], dtype=float)
    open_num = np.polymul(controller_num, plant_num)
    open_den = np.polymul(controller_den, plant_den)
    closed_den = np.polyadd(open_den, open_num)
    closed_num = open_num
    system = scipy_signal.TransferFunction(closed_num, closed_den)
    t = np.linspace(0.0, payload.durationS, payload.samples)
    step_t, unit_y = scipy_signal.step(system, T=t)
    y = np.asarray(unit_y, dtype=float) * float(payload.setpoint)
    poles = np.roots(_clean_poly(closed_den, "closed-loop denominator"))
    metrics = _time_metrics(np.asarray(step_t, dtype=float), y, float(payload.setpoint), payload.settlingBandPercent)
    result = _record(
        "pid-closed-loop",
        payload.model_dump(),
        {
            "controller": {"kp": payload.kp, "ki": payload.ki, "kd": payload.kd},
            "controllerNumerator": controller_num.round(14).tolist(),
            "controllerDenominator": controller_den.tolist(),
            "openLoopNumerator": np.asarray(open_num).round(14).tolist(),
            "openLoopDenominator": np.asarray(open_den).round(14).tolist(),
            "closedLoopNumerator": np.asarray(closed_num).round(14).tolist(),
            "closedLoopDenominator": np.asarray(closed_den).round(14).tolist(),
            "closedLoopPoles": [_complex_record(value) for value in poles],
            "stable": _stability_from_poles(poles),
            "metrics": metrics,
            "step": _series(step_t, y, "timeS", "value"),
        },
    )
    return {"ok": True, "result": result}


def root_locus_object(payload: RootLocusInput) -> Dict[str, Any]:
    numerator = _clean_poly(payload.numerator, "numerator")
    denominator = _clean_poly(payload.denominator, "denominator")
    gains = np.linspace(payload.gainMin, payload.gainMax, payload.gainPoints)
    locus = []
    first_stable_gain = None
    for gain in gains:
        closed_den = np.polyadd(denominator, float(gain) * numerator)
        poles = np.roots(_clean_poly(closed_den, "root-locus denominator"))
        stable = _stability_from_poles(poles)
        if stable and first_stable_gain is None:
            first_stable_gain = float(gain)
        locus.append({
            "gain": round(float(gain), 12),
            "stable": stable,
            "poles": [_complex_record(value) for value in poles],
        })
    result = _record(
        "root-locus",
        payload.model_dump(),
        {
            "numerator": numerator.round(14).tolist(),
            "denominator": denominator.round(14).tolist(),
            "gainRange": [payload.gainMin, payload.gainMax],
            "firstStableSampledGain": None if first_stable_gain is None else round(first_stable_gain, 12),
            "locus": locus,
        },
    )
    return {"ok": True, "result": result}


def _guard(callable_):
    try:
        return callable_()
    except (ValueError, TypeError, ZeroDivisionError, np.linalg.LinAlgError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Signals/control engine could not complete the operation: {exc}") from exc


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/spectrum")
def spectrum_endpoint(payload: SpectrumInput) -> Dict[str, Any]:
    return _guard(lambda: spectrum_object(payload))


@router.post("/convolve")
def convolve_endpoint(payload: ConvolutionInput) -> Dict[str, Any]:
    return _guard(lambda: convolution_object(payload))


@router.post("/filter-design")
def filter_design_endpoint(payload: FilterDesignInput) -> Dict[str, Any]:
    return _guard(lambda: filter_design_object(payload))


@router.post("/transfer-function")
def transfer_function_endpoint(payload: TransferFunctionInput) -> Dict[str, Any]:
    return _guard(lambda: transfer_function_object(payload))


@router.post("/state-space")
def state_space_endpoint(payload: StateSpaceInput) -> Dict[str, Any]:
    return _guard(lambda: state_space_object(payload))


@router.post("/pid")
def pid_endpoint(payload: PIDInput) -> Dict[str, Any]:
    return _guard(lambda: pid_object(payload))


@router.post("/root-locus")
def root_locus_endpoint(payload: RootLocusInput) -> Dict[str, Any]:
    return _guard(lambda: root_locus_object(payload))
