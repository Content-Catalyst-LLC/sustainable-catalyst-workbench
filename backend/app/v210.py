"""Workbench v2.1.0 Raspberry Pi, TinyML, and embedded-device API routes."""
from __future__ import annotations

from datetime import datetime, timezone
from math import sqrt
from statistics import fmean
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/workbench/v2.1.0", tags=["workbench-v2.1.0"])
VERSION = "2.1.0"


class CalibrationPoint(BaseModel):
    reference: float
    measured: float


class CalibrationRequest(BaseModel):
    instrument: str = Field(min_length=1, max_length=120)
    unit: str = Field(default="", max_length=32)
    points: list[CalibrationPoint] = Field(min_length=3, max_length=5000)


class DatasetRequest(BaseModel):
    task: Literal["classification", "regression"]
    target: str = Field(min_length=1, max_length=120)
    records: list[dict[str, str | int | float]] = Field(min_length=3, max_length=10000)
    quantization: Literal["int8", "float16", "none"] = "int8"


class RaspberryPiProjectRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    board: Literal[
        "raspberry-pi-5",
        "raspberry-pi-4",
        "raspberry-pi-zero-2-w",
        "raspberry-pi-3",
    ]
    operating_profile: str = Field(min_length=1, max_length=80)
    interface: Literal["gpio", "i2c", "spi", "serial", "network", "camera"]
    peripheral: str = Field(min_length=1, max_length=160)
    sample_interval_seconds: float = Field(gt=0, le=86400)
    objective: str = Field(default="", max_length=4000)


class TinyMLProjectRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    task: Literal["classification", "regression"]
    target: str = Field(min_length=1, max_length=120)
    features: list[str] = Field(min_length=1, max_length=128)
    quantization: Literal["int8", "float16", "none"] = "int8"
    model_family: str = Field(default="baseline", max_length=120)

    @field_validator("features")
    @classmethod
    def unique_features(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("features must be unique")
        return values


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def linear_fit(x_values: list[float], y_values: list[float]) -> dict[str, object]:
    if len(x_values) != len(y_values) or len(x_values) < 2:
        raise ValueError("at least two paired values are required")
    mean_x = fmean(x_values)
    mean_y = fmean(y_values)
    denominator = sum((value - mean_x) ** 2 for value in x_values)
    if denominator == 0:
        raise ValueError("independent values must not all be identical")
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values)) / denominator
    intercept = mean_y - slope * mean_x
    predicted = [slope * value + intercept for value in x_values]
    residuals = [actual - estimate for actual, estimate in zip(y_values, predicted)]
    sse = sum(value**2 for value in residuals)
    sst = sum((value - mean_y) ** 2 for value in y_values)
    return {
        "slope": slope,
        "intercept": intercept,
        "predicted": predicted,
        "residuals": residuals,
        "rmse": sqrt(sse / len(y_values)),
        "r2": 1.0 if sst == 0 else 1.0 - sse / sst,
    }


@router.get("/status")
def status() -> dict[str, object]:
    return {
        "ok": True,
        "version": VERSION,
        "release": "Raspberry Pi, TinyML, and Embedded Device Studio",
        "browserLocal": True,
        "localRunner": {
            "service": "http://127.0.0.1:8787",
            "pairingRequired": True,
            "arbitraryShellEndpoint": False,
        },
        "capabilities": [
            "raspberry-pi-project-manifests",
            "tinyml-dataset-validation",
            "linear-sensor-calibration",
            "embedded-board-catalog",
            "structured-device-discovery",
        ],
    }


@router.get("/boards")
def boards() -> dict[str, object]:
    records = [
        {"family": "raspberry-pi", "name": "Raspberry Pi 5", "profile": "Linux SBC", "interfaces": ["gpio", "i2c", "spi", "serial", "camera", "network"]},
        {"family": "raspberry-pi", "name": "Raspberry Pi Zero 2 W", "profile": "Compact Linux SBC", "interfaces": ["gpio", "i2c", "spi", "serial", "network"]},
        {"family": "arduino", "name": "Arduino Nicla Vision", "profile": "TinyML vision and sensing", "interfaces": ["camera", "imu", "microphone", "tof"]},
        {"family": "arduino", "name": "Arduino Nicla Voice", "profile": "TinyML audio and motion", "interfaces": ["microphone", "imu", "bluetooth"]},
        {"family": "arduino", "name": "Arduino Portenta H7", "profile": "Dual-core industrial MCU", "interfaces": ["tinyml", "ethernet", "wifi", "camera"]},
        {"family": "esp32", "name": "ESP32 Arduino-compatible", "profile": "Wireless MCU", "interfaces": ["wifi", "bluetooth", "adc", "i2c", "spi"]},
        {"family": "fpga", "name": "Lattice iCE40-class", "profile": "Open FPGA workflow", "interfaces": ["verilog", "yosys", "nextpnr"]},
    ]
    return {"ok": True, "version": VERSION, "boards": records}


@router.post("/calibration/linear")
def calibrate(request: CalibrationRequest) -> dict[str, object]:
    try:
        fit = linear_fit(
            [point.measured for point in request.points],
            [point.reference for point in request.points],
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    points = []
    for point, predicted, residual in zip(request.points, fit["predicted"], fit["residuals"]):
        points.append(
            {
                "reference": point.reference,
                "measured": point.measured,
                "predictedReference": predicted,
                "residual": residual,
            }
        )
    return {
        "ok": True,
        "schema": "sc-workbench-sensor-calibration/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "instrument": request.instrument,
        "unit": request.unit,
        "equation": {
            "form": "reference = slope * measured + intercept",
            "slope": fit["slope"],
            "intercept": fit["intercept"],
        },
        "performance": {"points": len(points), "rmse": fit["rmse"], "r2": fit["r2"]},
        "points": points,
    }


@router.post("/tinyml/prepare")
def tinyml_prepare(request: DatasetRequest) -> dict[str, object]:
    headers = set(request.records[0])
    if request.target not in headers:
        raise HTTPException(status_code=422, detail="target column was not found")
    if any(set(record) != headers for record in request.records):
        raise HTTPException(status_code=422, detail="all records must have the same columns")

    features = sorted(headers - {request.target})
    if not features:
        raise HTTPException(status_code=422, detail="at least one feature is required")

    statistics: list[dict[str, object]] = []
    absolute_maximum = 0.0
    for feature in features:
        try:
            values = [float(record[feature]) for record in request.records]
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"feature {feature} must be numeric") from exc
        average = fmean(values)
        variance = fmean((value - average) ** 2 for value in values)
        absolute_maximum = max(absolute_maximum, *(abs(value) for value in values))
        statistics.append(
            {
                "name": feature,
                "min": min(values),
                "max": max(values),
                "mean": average,
                "standardDeviation": sqrt(variance),
            }
        )

    if request.task == "regression":
        try:
            [float(record[request.target]) for record in request.records]
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="regression target must be numeric") from exc

    quantization: dict[str, object]
    if request.quantization == "int8":
        quantization = {
            "type": "int8-symmetric-preview",
            "scale": 1.0 if absolute_maximum == 0 else absolute_maximum / 127.0,
            "zeroPoint": 0,
            "observedAbsoluteMaximum": absolute_maximum,
        }
    else:
        quantization = {"type": request.quantization}

    return {
        "ok": True,
        "schema": "sc-workbench-tinyml-dataset-profile/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "task": request.task,
        "target": request.target,
        "features": features,
        "records": len(request.records),
        "statistics": statistics,
        "quantization": quantization,
        "validationRequired": [
            "leakage",
            "class-balance-or-target-distribution",
            "group-or-time-aware-splitting",
            "drift",
            "latency",
            "flash",
            "ram",
            "energy",
            "hardware-in-the-loop",
        ],
    }


@router.post("/projects/raspberry-pi")
def raspberry_pi_project(request: RaspberryPiProjectRequest) -> dict[str, object]:
    return {
        "ok": True,
        "schema": "sc-workbench-raspberry-pi-project/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "project": request.model_dump(),
        "files": [
            "src/main.py",
            "project.json",
            "README.md",
            "systemd/workbench-device.service",
        ],
        "validation": [
            "electrical limits and logic levels",
            "pin assignments and interface enablement",
            "device permissions",
            "calibration and uncertainty",
            "logging and storage retention",
            "network and privacy boundaries",
            "failure and restart behavior",
        ],
    }


@router.post("/projects/tinyml")
def tinyml_project(request: TinyMLProjectRequest) -> dict[str, object]:
    return {
        "ok": True,
        "schema": "sc-workbench-tinyml-project/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "project": request.model_dump(),
        "files": [
            "data/source.csv",
            "training/train.py",
            "model/model-card.json",
            "deployment/model.h",
            "validation/hardware-in-loop.md",
        ],
        "gates": [
            "reproducible training environment",
            "held-out evaluation",
            "quantization comparison",
            "latency and memory measurement",
            "hardware-in-the-loop test",
            "drift and recalibration plan",
        ],
    }
