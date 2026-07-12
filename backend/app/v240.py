"""Workbench v2.4.0 instrumentation, data acquisition, and signal analysis routes."""
from __future__ import annotations

from datetime import datetime, timezone
from math import cos, hypot, log10, pi, sqrt
from statistics import mean, stdev
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "2.4.0"
router = APIRouter(prefix="/api/v2.4", tags=["workbench-v2.4"])


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return sum((value - m) ** 2 for value in values) / (len(values) - 1)


def linear_fit(x: list[float], y: list[float]) -> dict[str, object]:
    if len(x) != len(y) or len(x) < 2:
        raise ValueError("at least two paired values are required")
    mx, my = mean(x), mean(y)
    sxx = sum((value - mx) ** 2 for value in x)
    sxy = sum((xv - mx) * (yv - my) for xv, yv in zip(x, y))
    syy = sum((value - my) ** 2 for value in y)
    if sxx <= 0:
        raise ValueError("independent values must vary")
    slope = sxy / sxx
    intercept = my - slope * mx
    residuals = [yv - (slope * xv + intercept) for xv, yv in zip(x, y)]
    sse = sum(value * value for value in residuals)
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": 1.0 - sse / syy if syy > 0 else 1.0,
        "rmse": sqrt(sse / len(x)),
        "residuals": residuals,
    }


class InstrumentationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    units: str = Field(default="", max_length=40)
    range_min: float
    range_max: float
    accuracy_percent_full_scale: float = Field(ge=0)
    resolution_bits: int = Field(ge=4, le=32)
    bandwidth_hz: float = Field(gt=0)
    expected_min: float
    expected_max: float
    interface: str = Field(default="", max_length=120)
    isolation_required: bool = False


class AcquisitionRequest(BaseModel):
    channels: int = Field(ge=1, le=256)
    sample_rate_hz: float = Field(gt=0)
    duration_s: float = Field(gt=0, le=86400)
    bit_depth: int = Field(ge=8, le=32)
    overhead_percent: float = Field(default=0, ge=0, le=500)
    expected_max_frequency_hz: float = Field(ge=0)
    buffer_seconds: float = Field(default=1, ge=0, le=3600)
    available_storage_mb: float = Field(default=0, ge=0)
    multiplexed: bool = False


class SignalRequest(BaseModel):
    sample_rate_hz: float = Field(gt=0)
    values: list[float] = Field(min_length=4, max_length=200000)
    times: list[float] | None = None
    detrend: Literal["none", "mean", "linear"] = "mean"
    moving_average_window: int = Field(default=1, ge=1, le=100000)


class FrequencyRequest(BaseModel):
    sample_rate_hz: float = Field(gt=0)
    values: list[float] = Field(min_length=8, max_length=4096)
    window: Literal["hann", "hamming", "rectangular"] = "hann"
    expected_max_frequency_hz: float = Field(default=0, ge=0)


class UncertaintyComponent(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    value: float = Field(ge=0)
    distribution: Literal["standard", "uniform", "triangular"] = "standard"


class CalibrationRequest(BaseModel):
    reference: list[float] = Field(min_length=3, max_length=10000)
    observed: list[float] = Field(min_length=3, max_length=10000)
    direction: Literal["observed_to_reference", "reference_to_observed"] = "observed_to_reference"
    uncertainty_components: list[UncertaintyComponent] = Field(default_factory=list)
    coverage_factor: float = Field(default=2, ge=0, le=10)
    acceptance_rmse: float | None = Field(default=None, ge=0)


class MeasurementRequest(BaseModel):
    times: list[float] = Field(min_length=2, max_length=200000)
    channels: dict[str, list[float | None]] = Field(default_factory=dict)
    expected_sample_rate_hz: float = Field(gt=0)
    sample_rate_tolerance_percent: float = Field(default=2, ge=0, le=100)
    maximum_jitter_percent: float = Field(default=10, ge=0)
    minimum_samples: int = Field(default=8, ge=2)
    campaign_notes: str = Field(default="", max_length=5000)


@router.get("/status")
def status() -> dict[str, object]:
    return {
        "ok": True,
        "version": VERSION,
        "studio": "Instrumentation, Data Acquisition, and Signal Analysis",
        "capabilities": [
            "instrument-range-resolution-review",
            "acquisition-throughput-storage-planning",
            "time-domain-signal-statistics",
            "windowed-frequency-spectrum",
            "calibration-regression-and-uncertainty",
            "measurement-timing-and-completeness-validation",
        ],
    }


@router.post("/instrumentation/review")
def instrumentation(req: InstrumentationRequest) -> dict[str, object]:
    span = req.range_max - req.range_min
    if span <= 0:
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "invalid-range"}]}
    expected_span = req.expected_max - req.expected_min
    step = span / ((2**req.resolution_bits) - 1)
    findings: list[dict[str, object]] = []
    if req.expected_min < req.range_min or req.expected_max > req.range_max:
        findings.append({"severity": "error", "code": "range-exceeded"})
    utilization = expected_span / span * 100 if expected_span > 0 else 0.0
    if utilization < 10:
        findings.append({"severity": "warning", "code": "low-range-utilization", "valuePercent": utilization})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-instrumentation-review/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "fullScaleSpan": span,
        "quantizationStep": step,
        "accuracyAllowance": span * req.accuracy_percent_full_scale / 100,
        "expectedSpanUtilizationPercent": utilization,
        "recommendedMinimumSampleRateHz": 2.5 * req.bandwidth_hz,
        "expectedCodes": expected_span / step if expected_span > 0 else 0,
        "findings": findings,
        "instrument": req.model_dump(),
    }


@router.post("/acquisition/plan")
def acquisition(req: AcquisitionRequest) -> dict[str, object]:
    bytes_per_sample = (req.bit_depth + 7) // 8
    samples_per_channel = req.sample_rate_hz * req.duration_s
    total_samples = samples_per_channel * req.channels
    factor = 1 + req.overhead_percent / 100
    total_bytes = total_samples * bytes_per_sample * factor
    throughput = req.sample_rate_hz * req.channels * bytes_per_sample * factor
    nyquist = req.sample_rate_hz / 2
    findings: list[dict[str, object]] = []
    if req.sample_rate_hz < 2.5 * req.expected_max_frequency_hz:
        findings.append({"severity": "error", "code": "alias-risk"})
    if req.available_storage_mb and total_bytes > req.available_storage_mb * 1024 * 1024:
        findings.append({"severity": "error", "code": "storage-exceeded"})
    if req.multiplexed and req.channels > 1:
        findings.append({"severity": "warning", "code": "inter-channel-skew-review"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-acquisition-plan/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "samplesPerChannel": samples_per_channel,
        "totalSamples": total_samples,
        "nyquistHz": nyquist,
        "bytesPerSample": bytes_per_sample,
        "estimatedBytes": total_bytes,
        "throughputBytesPerSecond": throughput,
        "bufferBytes": throughput * req.buffer_seconds,
        "findings": findings,
        "request": req.model_dump(),
    }


def detrended_values(times: list[float], values: list[float], mode: str) -> list[float]:
    if mode == "none":
        return values[:]
    if mode == "linear":
        fit = linear_fit(times, values)
        return [value - (float(fit["slope"]) * time + float(fit["intercept"])) for time, value in zip(times, values)]
    m = mean(values)
    return [value - m for value in values]


def moving_average(values: list[float], width: int) -> list[float]:
    width = max(1, width)
    output: list[float] = []
    running = 0.0
    for index, value in enumerate(values):
        running += value
        if index >= width:
            running -= values[index - width]
        output.append(running / min(width, index + 1))
    return output


@router.post("/signals/analyze")
def signals(req: SignalRequest) -> dict[str, object]:
    times = req.times or [index / req.sample_rate_hz for index in range(len(req.values))]
    if len(times) != len(req.values):
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "time-value-length-mismatch"}]}
    fit = linear_fit(times, req.values)
    centered = detrended_values(times, req.values, req.detrend)
    filtered = moving_average(centered, req.moving_average_window)
    differences = [value - req.values[index] for index, value in enumerate(req.values[1:])]
    noise = sqrt(variance(differences)) / sqrt(2) if differences else 0.0
    signal_rms = sqrt(mean(value * value for value in req.values))
    centered_rms = sqrt(mean(value * value for value in centered))
    snr = 20 * log10(centered_rms / noise) if noise > 0 and centered_rms > 0 else None
    return {
        "ok": True,
        "schema": "sc-workbench-time-domain-signal/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "sampleCount": len(req.values),
        "mean": mean(req.values),
        "rms": signal_rms,
        "standardDeviation": sqrt(variance(req.values)),
        "minimum": min(req.values),
        "maximum": max(req.values),
        "peakToPeak": max(req.values) - min(req.values),
        "crestFactor": max(abs(value) for value in req.values) / signal_rms if signal_rms else None,
        "driftSlopePerSecond": fit["slope"],
        "estimatedNoise": noise,
        "estimatedSnrDb": snr,
        "filtered": filtered[:10000],
    }


def window_coefficient(kind: str, index: int, count: int) -> float:
    if count <= 1 or kind == "rectangular":
        return 1.0
    if kind == "hamming":
        return 0.54 - 0.46 * cos(2 * pi * index / (count - 1))
    return 0.5 * (1 - cos(2 * pi * index / (count - 1)))


@router.post("/frequency/analyze")
def frequency(req: FrequencyRequest) -> dict[str, object]:
    values = req.values
    count = len(values)
    m = mean(values)
    coefficients = [window_coefficient(req.window, index, count) for index in range(count)]
    weighted = [(value - m) * coefficients[index] for index, value in enumerate(values)]
    coherent_gain = mean(coefficients)
    bins: list[dict[str, float]] = []
    for k in range(count // 2 + 1):
        real = 0.0
        imag = 0.0
        for index, value in enumerate(weighted):
            angle = 2 * pi * k * index / count
            real += value * cos(angle)
            imag -= value * __import__("math").sin(angle)
        amplitude = 2 * hypot(real, imag) / (count * max(coherent_gain, 1e-12))
        if k == 0:
            amplitude /= 2
        bins.append({"bin": k, "frequencyHz": k * req.sample_rate_hz / count, "amplitude": amplitude})
    peaks = sorted(bins[1:], key=lambda item: item["amplitude"], reverse=True)[:5]
    findings: list[dict[str, object]] = []
    if req.expected_max_frequency_hz >= req.sample_rate_hz / 2:
        findings.append({"severity": "error", "code": "alias-risk"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-frequency-spectrum/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "sampleCount": count,
        "nyquistHz": req.sample_rate_hz / 2,
        "frequencyResolutionHz": req.sample_rate_hz / count,
        "dominantFrequencyHz": peaks[0]["frequencyHz"] if peaks else None,
        "dominantAmplitude": peaks[0]["amplitude"] if peaks else None,
        "topPeaks": peaks,
        "spectrum": bins,
        "findings": findings,
    }


@router.post("/calibration/fit")
def calibration(req: CalibrationRequest) -> dict[str, object]:
    if len(req.reference) != len(req.observed):
        return {"ok": False, "version": VERSION, "findings": [{"severity": "error", "code": "point-count-mismatch"}]}
    x = req.observed if req.direction == "observed_to_reference" else req.reference
    y = req.reference if req.direction == "observed_to_reference" else req.observed
    fit = linear_fit(x, y)
    standard_components = []
    for item in req.uncertainty_components:
        divisor = sqrt(3) if item.distribution == "uniform" else sqrt(6) if item.distribution == "triangular" else 1.0
        standard_components.append({**item.model_dump(), "standardUncertainty": item.value / divisor})
    combined = sqrt(sum(float(item["standardUncertainty"]) ** 2 for item in standard_components))
    findings: list[dict[str, object]] = []
    if req.acceptance_rmse is not None and float(fit["rmse"]) > req.acceptance_rmse:
        findings.append({"severity": "error", "code": "rmse-exceeded", "value": fit["rmse"]})
    if float(fit["r2"]) < 0.99:
        findings.append({"severity": "warning", "code": "low-r2", "value": fit["r2"]})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-calibration-uncertainty/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "fit": fit,
        "uncertaintyComponents": standard_components,
        "combinedStandardUncertainty": combined,
        "coverageFactor": req.coverage_factor,
        "expandedUncertainty": combined * req.coverage_factor,
        "findings": findings,
    }


@router.post("/measurements/validate")
def measurements(req: MeasurementRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    if len(req.times) < req.minimum_samples:
        findings.append({"severity": "error", "code": "insufficient-samples"})
    intervals: list[float] = []
    for previous, current in zip(req.times, req.times[1:]):
        if current <= previous:
            findings.append({"severity": "error", "code": "non-monotonic-time"})
        else:
            intervals.append(current - previous)
    mean_interval = mean(intervals) if intervals else 0.0
    observed_rate = 1 / mean_interval if mean_interval > 0 else 0.0
    jitter_percent = (stdev(intervals) / mean_interval * 100) if len(intervals) > 1 and mean_interval > 0 else 0.0
    tolerance = req.expected_sample_rate_hz * req.sample_rate_tolerance_percent / 100
    if abs(observed_rate - req.expected_sample_rate_hz) > tolerance:
        findings.append({"severity": "error", "code": "sample-rate-error", "value": observed_rate})
    if jitter_percent > req.maximum_jitter_percent:
        findings.append({"severity": "error", "code": "timing-jitter", "valuePercent": jitter_percent})
    channel_stats: dict[str, dict[str, object]] = {}
    for name, values in req.channels.items():
        valid = [value for value in values if value is not None]
        if len(values) != len(req.times):
            findings.append({"severity": "error", "code": "channel-length-mismatch", "channel": name})
        if len(valid) < len(values):
            findings.append({"severity": "warning", "code": "missing-channel-values", "channel": name})
        channel_stats[name] = {
            "count": len(valid),
            "mean": mean(valid) if valid else None,
            "standardDeviation": sqrt(variance(valid)) if valid else None,
            "minimum": min(valid) if valid else None,
            "maximum": max(valid) if valid else None,
        }
    if not req.campaign_notes.strip():
        findings.append({"severity": "warning", "code": "missing-provenance-notes"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-measurement-validation/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "sampleCount": len(req.times),
        "observedSampleRateHz": observed_rate,
        "meanIntervalS": mean_interval,
        "timingJitterPercent": jitter_percent,
        "channelStatistics": channel_stats,
        "findings": findings,
    }
