"""Workbench v5.8.0 — Electronics & Embedded Systems Studio.

Bounded electronics calculations and embedded-system planning for resistor/RLC
networks, ADC/DAC quantization, PWM/timer selection, sampling, digital buses,
sensor transfer models, GPIO allocation, and export-only prototype scaffolds.

This module never opens serial ports, network sockets, GPIO devices, JTAG,
programmers, shells, or user-supplied executable code. Physical execution and
automatic device programming remain explicitly unauthorized.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Literal, Optional, Sequence

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.v510 import content_hash

VERSION = "5.8.0"
SCHEMA = "sc-workbench-electronics-embedded-object/1.0"
MAX_COMPONENTS = 64
MAX_ASSIGNMENTS = 64
MAX_PAYLOAD_BYTES = 1_048_576

router = APIRouter(prefix="/v580", tags=["workbench-v580-electronics-embedded"])


def _finite(value: float, label: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite.")
    return number


def _positive(value: float, label: str, allow_zero: bool = False) -> float:
    number = _finite(value, label)
    if allow_zero:
        if number < 0:
            raise ValueError(f"{label} must be greater than or equal to zero.")
    elif number <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return number


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
        "serialPortAccessAuthorized": False,
        "gpioAccessAuthorized": False,
        "jtagAccessAuthorized": False,
    }
    value["electronicsEmbeddedObjectHash"] = content_hash(value)
    return value


def _complex_record(value: complex) -> Dict[str, float]:
    return {
        "real": round(float(value.real), 12),
        "imag": round(float(value.imag), 12),
        "magnitude": round(float(abs(value)), 12),
        "phaseDeg": round(float(math.degrees(math.atan2(value.imag, value.real))), 9),
    }


class ResistorNetworkInput(BaseModel):
    topology: Literal["series", "parallel"] = "series"
    resistancesOhm: List[float] = Field(min_length=1, max_length=MAX_COMPONENTS)
    sourceVoltageV: float = Field(default=5.0, ge=0, le=1e6)

    @model_validator(mode="after")
    def validate_resistors(self):
        for idx, value in enumerate(self.resistancesOhm):
            _positive(value, f"resistancesOhm[{idx}]")
        _finite(self.sourceVoltageV, "sourceVoltageV")
        return self


class RLCInput(BaseModel):
    topology: Literal["series", "parallel"] = "series"
    resistanceOhm: float = Field(default=100.0, ge=0, le=1e12)
    inductanceH: float = Field(default=0.01, ge=0, le=1e6)
    capacitanceF: float = Field(default=1e-6, ge=0, le=1e3)
    frequencyHz: float = Field(default=1000.0, gt=0, le=1e12)
    sourceVoltageV: float = Field(default=1.0, ge=0, le=1e6)

    @model_validator(mode="after")
    def validate_rlc(self):
        if self.resistanceOhm == 0 and self.inductanceH == 0 and self.capacitanceF == 0:
            raise ValueError("At least one R, L, or C component must be non-zero.")
        return self


class ADCDACInput(BaseModel):
    bits: int = Field(default=12, ge=1, le=32)
    referenceVoltageV: float = Field(default=3.3, gt=0, le=1e6)
    inputVoltageV: float = Field(default=1.65, ge=-1e6, le=1e6)
    dacCode: Optional[int] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_dac_code(self):
        max_code = (1 << self.bits) - 1
        if self.dacCode is not None and self.dacCode > max_code:
            raise ValueError(f"dacCode must be between 0 and {max_code} for {self.bits} bits.")
        return self


class PWMTimerInput(BaseModel):
    clockHz: float = Field(default=16_000_000.0, gt=0, le=1e12)
    desiredFrequencyHz: float = Field(default=1000.0, gt=0, le=1e9)
    dutyCyclePercent: float = Field(default=50.0, ge=0, le=100)
    counterBits: int = Field(default=16, ge=4, le=64)
    alignment: Literal["edge", "center"] = "edge"
    availablePrescalers: List[int] = Field(default_factory=lambda: [1, 8, 64, 256, 1024], min_length=1, max_length=32)

    @model_validator(mode="after")
    def validate_prescalers(self):
        if any(int(p) <= 0 for p in self.availablePrescalers):
            raise ValueError("Every prescaler must be a positive integer.")
        return self


class SamplingInput(BaseModel):
    sampleRateHz: float = Field(default=10_000.0, gt=0, le=1e12)
    signalBandwidthHz: float = Field(default=1000.0, gt=0, le=1e12)
    adcBits: int = Field(default=12, ge=1, le=32)
    durationS: float = Field(default=1.0, gt=0, le=86_400)


class BusPlanInput(BaseModel):
    protocol: Literal["i2c", "spi", "uart"] = "i2c"
    clockOrBaudHz: float = Field(default=400_000.0, gt=0, le=10e9)
    payloadBytes: int = Field(default=32, ge=1, le=MAX_PAYLOAD_BYTES)
    transactionCount: int = Field(default=1, ge=1, le=100_000)
    i2cAddressBits: Literal[7, 10] = 7
    uartDataBits: int = Field(default=8, ge=5, le=9)
    uartParity: Literal["none", "even", "odd"] = "none"
    uartStopBits: Literal[1, 2] = 1


class SensorModelInput(BaseModel):
    model: Literal["linear", "voltage-divider", "ntc-beta"] = "linear"
    inputVoltageV: float = Field(default=1.0, ge=-1e6, le=1e6)
    gainPerVolt: float = Field(default=100.0, ge=-1e12, le=1e12)
    offset: float = Field(default=0.0, ge=-1e12, le=1e12)
    outputUnit: str = Field(default="units", max_length=32)
    supplyVoltageV: float = Field(default=3.3, gt=0, le=1e6)
    knownResistanceOhm: float = Field(default=10_000.0, gt=0, le=1e12)
    sensorPosition: Literal["high", "low"] = "low"
    measuredResistanceOhm: float = Field(default=10_000.0, gt=0, le=1e12)
    nominalResistanceOhm: float = Field(default=10_000.0, gt=0, le=1e12)
    nominalTemperatureC: float = Field(default=25.0, ge=-273.14, le=1000)
    betaK: float = Field(default=3950.0, gt=0, le=100_000)


class PinAssignment(BaseModel):
    signal: str = Field(min_length=1, max_length=64)
    pin: str = Field(min_length=1, max_length=64)
    direction: Literal["input", "output", "bidirectional"] = "bidirectional"
    voltageV: float = Field(default=3.3, ge=0, le=1000)
    interface: Literal["gpio", "adc", "dac", "pwm", "i2c", "spi", "uart", "clock", "other"] = "gpio"


class GPIOPlanInput(BaseModel):
    target: Literal["arduino", "esp32", "raspberry-pi", "pynq", "generic"] = "generic"
    assignments: List[PinAssignment] = Field(min_length=1, max_length=MAX_ASSIGNMENTS)

    @model_validator(mode="after")
    def validate_assignments(self):
        pins = [item.pin.strip().lower() for item in self.assignments]
        if len(set(pins)) != len(pins):
            raise ValueError("Each physical pin may be assigned only once in a plan.")
        signals = [item.signal.strip().lower() for item in self.assignments]
        if len(set(signals)) != len(signals):
            raise ValueError("Each signal name must be unique in a plan.")
        return self


class PrototypeScaffoldInput(BaseModel):
    target: Literal["arduino", "esp32", "raspberry-pi", "pynq", "verilog", "vhdl"] = "arduino"
    projectName: str = Field(default="catalyst_prototype", min_length=1, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    interface: Literal["gpio", "adc", "pwm", "i2c", "spi", "uart"] = "gpio"
    sampleRateHz: float = Field(default=1000.0, gt=0, le=1e9)


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-electronics-embedded-status/1.0",
        "version": VERSION,
        "inherits": {
            "mathematics": "5.1.0",
            "graphMathematics": "5.4.0",
            "dynamicGeometry": "5.5.0",
            "numericalComputing": "5.6.0",
            "signalsControl": "5.7.0",
        },
        "capabilities": [
            "resistor-network-analysis",
            "rlc-impedance-analysis",
            "adc-dac-quantization",
            "pwm-timer-planning",
            "sampling-nyquist-analysis",
            "i2c-spi-uart-planning",
            "sensor-transfer-models",
            "gpio-allocation-planning",
            "export-only-embedded-scaffolds",
            "arduino",
            "esp32",
            "raspberry-pi",
            "pynq",
            "verilog",
            "vhdl",
            "canonical-electronics-embedded-objects",
        ],
        "executionBoundary": "analysis-planning-and-export-only",
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "deviceExecutionAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
        "serialPortAccessAuthorized": False,
        "gpioAccessAuthorized": False,
        "jtagAccessAuthorized": False,
    }


def resistor_network_object(payload: ResistorNetworkInput) -> Dict[str, Any]:
    resistances = [float(r) for r in payload.resistancesOhm]
    voltage = float(payload.sourceVoltageV)
    if payload.topology == "series":
        equivalent = sum(resistances)
        total_current = 0.0 if equivalent == 0 else voltage / equivalent
        components = [
            {
                "index": idx,
                "resistanceOhm": round(r, 12),
                "currentA": round(total_current, 12),
                "voltageV": round(total_current * r, 12),
                "powerW": round((total_current ** 2) * r, 12),
            }
            for idx, r in enumerate(resistances)
        ]
    else:
        equivalent = 1.0 / sum(1.0 / r for r in resistances)
        total_current = 0.0 if equivalent == 0 else voltage / equivalent
        components = [
            {
                "index": idx,
                "resistanceOhm": round(r, 12),
                "currentA": round(voltage / r, 12),
                "voltageV": round(voltage, 12),
                "powerW": round((voltage ** 2) / r, 12),
            }
            for idx, r in enumerate(resistances)
        ]
    total_power = voltage * total_current
    result = _record(
        "resistor-network",
        payload.model_dump(),
        {
            "topology": payload.topology,
            "equivalentResistanceOhm": round(equivalent, 12),
            "sourceVoltageV": round(voltage, 12),
            "totalCurrentA": round(total_current, 12),
            "totalPowerW": round(total_power, 12),
            "components": components,
        },
    )
    return {"ok": True, "result": result}


def rlc_object(payload: RLCInput) -> Dict[str, Any]:
    r = float(payload.resistanceOhm)
    l = float(payload.inductanceH)
    c = float(payload.capacitanceF)
    f = float(payload.frequencyHz)
    omega = 2.0 * math.pi * f
    zr = complex(r, 0) if r > 0 else None
    zl = complex(0, omega * l) if l > 0 else None
    zc = complex(0, -1.0 / (omega * c)) if c > 0 else None
    branches = [z for z in (zr, zl, zc) if z is not None]
    if payload.topology == "series":
        z_total = sum(branches, complex(0, 0))
    else:
        admittance = sum((1.0 / z for z in branches if abs(z) > 1e-30), complex(0, 0))
        if abs(admittance) <= 1e-30:
            raise ValueError("Parallel network has zero total admittance.")
        z_total = 1.0 / admittance
    current = complex(payload.sourceVoltageV, 0) / z_total if abs(z_total) > 1e-30 else complex(0, 0)
    resonance = None
    q_factor = None
    if l > 0 and c > 0:
        resonance = 1.0 / (2.0 * math.pi * math.sqrt(l * c))
        if r > 0:
            omega0 = 2.0 * math.pi * resonance
            q_factor = (omega0 * l / r) if payload.topology == "series" else (r / (omega0 * l))
    result = _record(
        "rlc-impedance",
        payload.model_dump(),
        {
            "topology": payload.topology,
            "frequencyHz": round(f, 12),
            "angularFrequencyRadS": round(omega, 12),
            "resistorImpedance": None if zr is None else _complex_record(zr),
            "inductorImpedance": None if zl is None else _complex_record(zl),
            "capacitorImpedance": None if zc is None else _complex_record(zc),
            "equivalentImpedance": _complex_record(z_total),
            "sourceCurrent": _complex_record(current),
            "resonantFrequencyHz": None if resonance is None else round(resonance, 12),
            "qualityFactorApprox": None if q_factor is None else round(q_factor, 12),
        },
    )
    return {"ok": True, "result": result}


def adc_dac_object(payload: ADCDACInput) -> Dict[str, Any]:
    max_code = (1 << payload.bits) - 1
    lsb = payload.referenceVoltageV / max_code
    clipped_voltage = min(max(payload.inputVoltageV, 0.0), payload.referenceVoltageV)
    adc_code = int(round((clipped_voltage / payload.referenceVoltageV) * max_code))
    quantized_voltage = adc_code * lsb
    dac_code = payload.dacCode if payload.dacCode is not None else adc_code
    dac_voltage = int(dac_code) * lsb
    result = _record(
        "adc-dac-quantization",
        payload.model_dump(),
        {
            "bits": payload.bits,
            "maxCode": max_code,
            "lsbVoltageV": round(lsb, 15),
            "adc": {
                "inputVoltageV": round(payload.inputVoltageV, 12),
                "clipped": payload.inputVoltageV < 0 or payload.inputVoltageV > payload.referenceVoltageV,
                "code": adc_code,
                "quantizedVoltageV": round(quantized_voltage, 12),
                "quantizationErrorV": round(quantized_voltage - clipped_voltage, 12),
                "idealQuantizationUncertaintyV": round(lsb / 2.0, 15),
            },
            "dac": {"code": int(dac_code), "outputVoltageV": round(dac_voltage, 12)},
        },
    )
    return {"ok": True, "result": result}


def pwm_timer_object(payload: PWMTimerInput) -> Dict[str, Any]:
    max_count = (1 << payload.counterBits) - 1
    alignment_factor = 1 if payload.alignment == "edge" else 2
    candidates = []
    for prescaler in sorted(set(int(p) for p in payload.availablePrescalers)):
        ideal_counts = payload.clockHz / (prescaler * payload.desiredFrequencyHz * alignment_factor)
        period = int(round(ideal_counts)) - 1
        if period < 0 or period > max_count:
            continue
        actual = payload.clockHz / (prescaler * (period + 1) * alignment_factor)
        error_ppm = ((actual - payload.desiredFrequencyHz) / payload.desiredFrequencyHz) * 1e6
        compare = int(round((payload.dutyCyclePercent / 100.0) * (period + 1)))
        compare = min(max(compare, 0), period + 1)
        candidates.append({
            "prescaler": prescaler,
            "periodRegister": period,
            "compareCount": compare,
            "actualFrequencyHz": actual,
            "frequencyErrorPpm": error_ppm,
            "dutyResolutionBits": math.log2(period + 1) if period + 1 > 0 else 0,
        })
    if not candidates:
        raise ValueError("No provided prescaler can represent the requested frequency at this counter width.")
    best = min(candidates, key=lambda item: (abs(item["frequencyErrorPpm"]), -item["dutyResolutionBits"]))
    clean = [
        {
            "prescaler": item["prescaler"],
            "periodRegister": item["periodRegister"],
            "compareCount": item["compareCount"],
            "actualFrequencyHz": round(item["actualFrequencyHz"], 12),
            "frequencyErrorPpm": round(item["frequencyErrorPpm"], 6),
            "dutyResolutionBits": round(item["dutyResolutionBits"], 6),
        }
        for item in candidates
    ]
    result = _record(
        "pwm-timer-plan",
        payload.model_dump(),
        {
            "alignment": payload.alignment,
            "counterBits": payload.counterBits,
            "selected": min(clean, key=lambda item: (abs(item["frequencyErrorPpm"]), -item["dutyResolutionBits"])),
            "candidates": clean,
        },
    )
    return {"ok": True, "result": result}


def sampling_object(payload: SamplingInput) -> Dict[str, Any]:
    nyquist = payload.sampleRateHz / 2.0
    ratio = payload.sampleRateHz / (2.0 * payload.signalBandwidthHz)
    sample_count = int(math.ceil(payload.sampleRateHz * payload.durationS))
    ideal_snr = 6.02 * payload.adcBits + 1.76
    result = _record(
        "sampling-plan",
        payload.model_dump(),
        {
            "nyquistFrequencyHz": round(nyquist, 12),
            "oversamplingRatio": round(ratio, 12),
            "nyquistSatisfied": payload.sampleRateHz >= 2.0 * payload.signalBandwidthHz,
            "sampleCount": sample_count,
            "sampleIntervalS": round(1.0 / payload.sampleRateHz, 15),
            "idealAdcSnrDb": round(ideal_snr, 6),
            "recommendAntiAliasFilter": payload.sampleRateHz < 4.0 * payload.signalBandwidthHz,
        },
    )
    return {"ok": True, "result": result}


def bus_plan_object(payload: BusPlanInput) -> Dict[str, Any]:
    data_bits = payload.payloadBytes * 8
    if payload.protocol == "i2c":
        address_bytes = 2 if payload.i2cAddressBits == 10 else 1
        transmitted_bytes = payload.payloadBytes + address_bytes
        total_bits_per_transaction = transmitted_bytes * 9 + 2  # ACK/NACK plus START/STOP approximation
        wires = 2
        duplex = "half-duplex shared bus"
        note = "Approximation includes one ACK/NACK bit per transmitted byte plus START/STOP allowance."
    elif payload.protocol == "spi":
        total_bits_per_transaction = data_bits
        wires = 4
        duplex = "full-duplex clocked"
        note = "Chip-select setup/hold time is not included in the bit-count estimate."
    else:
        parity_bits = 0 if payload.uartParity == "none" else 1
        frame_bits = 1 + payload.uartDataBits + parity_bits + payload.uartStopBits
        total_bits_per_transaction = payload.payloadBytes * frame_bits
        wires = 2
        duplex = "asynchronous point-to-point"
        note = f"UART estimate uses {payload.uartDataBits} data bits, {payload.uartParity} parity, {payload.uartStopBits} stop bit(s)."
    total_bits = total_bits_per_transaction * payload.transactionCount
    total_time = total_bits / payload.clockOrBaudHz
    throughput = (payload.payloadBytes * payload.transactionCount) / total_time if total_time > 0 else 0
    efficiency = (data_bits * payload.transactionCount) / total_bits if total_bits > 0 else 0
    result = _record(
        "digital-bus-plan",
        payload.model_dump(),
        {
            "protocol": payload.protocol,
            "nominalRateHz": round(payload.clockOrBaudHz, 12),
            "payloadBytesTotal": payload.payloadBytes * payload.transactionCount,
            "wireCountMinimum": wires,
            "duplex": duplex,
            "estimatedWireBits": total_bits,
            "estimatedTransferTimeS": round(total_time, 12),
            "estimatedPayloadThroughputBytesS": round(throughput, 6),
            "payloadEfficiency": round(efficiency, 9),
            "assumption": note,
        },
    )
    return {"ok": True, "result": result}


def sensor_model_object(payload: SensorModelInput) -> Dict[str, Any]:
    if payload.model == "linear":
        output = payload.gainPerVolt * payload.inputVoltageV + payload.offset
        detail = {
            "inputVoltageV": round(payload.inputVoltageV, 12),
            "gainPerVolt": round(payload.gainPerVolt, 12),
            "offset": round(payload.offset, 12),
            "value": round(output, 12),
            "unit": payload.outputUnit,
        }
    elif payload.model == "voltage-divider":
        v = payload.inputVoltageV
        vs = payload.supplyVoltageV
        if v <= 0 or v >= vs:
            raise ValueError("For a voltage-divider model, inputVoltageV must lie strictly between 0 and supplyVoltageV.")
        rk = payload.knownResistanceOhm
        if payload.sensorPosition == "low":
            unknown = rk * v / (vs - v)
        else:
            unknown = rk * (vs - v) / v
        detail = {
            "measuredVoltageV": round(v, 12),
            "supplyVoltageV": round(vs, 12),
            "knownResistanceOhm": round(rk, 12),
            "sensorPosition": payload.sensorPosition,
            "inferredSensorResistanceOhm": round(unknown, 12),
        }
    else:
        r = payload.measuredResistanceOhm
        r0 = payload.nominalResistanceOhm
        t0 = payload.nominalTemperatureC + 273.15
        inv_t = (1.0 / t0) + (1.0 / payload.betaK) * math.log(r / r0)
        temp_k = 1.0 / inv_t
        detail = {
            "measuredResistanceOhm": round(r, 12),
            "nominalResistanceOhm": round(r0, 12),
            "betaK": round(payload.betaK, 12),
            "temperatureC": round(temp_k - 273.15, 9),
            "temperatureK": round(temp_k, 9),
        }
    result = _record("sensor-transfer-model", payload.model_dump(), {"model": payload.model, "result": detail})
    return {"ok": True, "result": result}


def gpio_plan_object(payload: GPIOPlanInput) -> Dict[str, Any]:
    warnings: List[str] = []
    for assignment in payload.assignments:
        if assignment.voltageV > 5.0:
            warnings.append(f"{assignment.signal}: {assignment.voltageV:g} V requires board-specific voltage-domain review.")
    interfaces: Dict[str, int] = {}
    for assignment in payload.assignments:
        interfaces[assignment.interface] = interfaces.get(assignment.interface, 0) + 1
    result = _record(
        "gpio-allocation-plan",
        payload.model_dump(),
        {
            "target": payload.target,
            "assignmentCount": len(payload.assignments),
            "interfaces": interfaces,
            "assignments": [item.model_dump() for item in payload.assignments],
            "conflictFree": True,
            "warnings": warnings,
            "boardPinoutValidated": False,
            "note": "Pin names and voltage domains must be checked against the exact board revision before physical wiring.",
        },
    )
    return {"ok": True, "result": result}


def _scaffold_files(target: str, project: str, interface: str, sample_rate: float) -> List[Dict[str, str]]:
    hz = f"{sample_rate:.12g}"
    if target in {"arduino", "esp32"}:
        board = "ESP32" if target == "esp32" else "Arduino-compatible"
        text = (
            f"// {project} — {board} export scaffold\n"
            f"// Interface: {interface}; nominal sample rate: {hz} Hz\n"
            "// REVIEW BOARD PINOUT AND ELECTRICAL LIMITS BEFORE FLASHING.\n\n"
            "void setup() {\n  // Configure pins/peripherals explicitly after review.\n}\n\n"
            "void loop() {\n  // Insert bounded acquisition/control logic here.\n}\n"
        )
        return [{"path": f"{project}/{project}.ino", "language": "cpp", "content": text}]
    if target in {"raspberry-pi", "pynq"}:
        platform = "PYNQ" if target == "pynq" else "Raspberry Pi"
        text = (
            f'"""{project} — {platform} export scaffold.\n'
            f"Interface: {interface}; nominal sample rate: {hz} Hz.\n"
            "No GPIO/device access is performed by this scaffold until the user adds reviewed platform code.\n"
            '"""\n\n'
            "def main():\n    # Add reviewed platform-specific I/O here.\n    pass\n\n"
            "if __name__ == '__main__':\n    main()\n"
        )
        return [{"path": f"{project}/main.py", "language": "python", "content": text}]
    if target == "verilog":
        text = (
            f"// {project} — Verilog export scaffold\n"
            f"// Planned interface: {interface}; nominal sample rate: {hz} Hz\n"
            "module catalyst_top(input wire clk, input wire rst_n, output wire activity);\n"
            "  assign activity = clk & rst_n; // replace after timing/board review\n"
            "endmodule\n"
        )
        return [{"path": f"{project}/catalyst_top.v", "language": "verilog", "content": text}]
    text = (
        f"-- {project} — VHDL export scaffold\n"
        f"-- Planned interface: {interface}; nominal sample rate: {hz} Hz\n"
        "library ieee; use ieee.std_logic_1164.all;\n"
        "entity catalyst_top is port(clk, rst_n : in std_logic; activity : out std_logic); end entity;\n"
        "architecture rtl of catalyst_top is begin activity <= clk and rst_n; end architecture;\n"
    )
    return [{"path": f"{project}/catalyst_top.vhd", "language": "vhdl", "content": text}]


def prototype_scaffold_object(payload: PrototypeScaffoldInput) -> Dict[str, Any]:
    project = re.sub(r"[^A-Za-z0-9_-]", "_", payload.projectName)
    files = _scaffold_files(payload.target, project, payload.interface, payload.sampleRateHz)
    result = _record(
        "embedded-prototype-scaffold",
        payload.model_dump(),
        {
            "target": payload.target,
            "projectName": project,
            "interface": payload.interface,
            "files": files,
            "exportOnly": True,
            "requiresHumanReviewBeforeExecution": True,
            "deviceProgrammingPerformed": False,
        },
    )
    return {"ok": True, "result": result}


def _guard(callable_):
    try:
        return callable_()
    except (ValueError, TypeError, ZeroDivisionError, OverflowError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Electronics/embedded engine could not complete the operation: {exc}") from exc


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/resistor-network")
def resistor_network_endpoint(payload: ResistorNetworkInput) -> Dict[str, Any]:
    return _guard(lambda: resistor_network_object(payload))


@router.post("/rlc")
def rlc_endpoint(payload: RLCInput) -> Dict[str, Any]:
    return _guard(lambda: rlc_object(payload))


@router.post("/adc-dac")
def adc_dac_endpoint(payload: ADCDACInput) -> Dict[str, Any]:
    return _guard(lambda: adc_dac_object(payload))


@router.post("/pwm-timer")
def pwm_timer_endpoint(payload: PWMTimerInput) -> Dict[str, Any]:
    return _guard(lambda: pwm_timer_object(payload))


@router.post("/sampling")
def sampling_endpoint(payload: SamplingInput) -> Dict[str, Any]:
    return _guard(lambda: sampling_object(payload))


@router.post("/bus-plan")
def bus_plan_endpoint(payload: BusPlanInput) -> Dict[str, Any]:
    return _guard(lambda: bus_plan_object(payload))


@router.post("/sensor-model")
def sensor_model_endpoint(payload: SensorModelInput) -> Dict[str, Any]:
    return _guard(lambda: sensor_model_object(payload))


@router.post("/gpio-plan")
def gpio_plan_endpoint(payload: GPIOPlanInput) -> Dict[str, Any]:
    return _guard(lambda: gpio_plan_object(payload))


@router.post("/prototype-scaffold")
def prototype_scaffold_endpoint(payload: PrototypeScaffoldInput) -> Dict[str, Any]:
    return _guard(lambda: prototype_scaffold_object(payload))
