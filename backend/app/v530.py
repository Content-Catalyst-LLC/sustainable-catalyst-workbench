"""Workbench v5.3.0 — Computational Blackboard, Creative Mathematics & Physical Prototyping.

This release extends the v5.1 restricted mathematics engine and v5.2 graph objects with:
- deterministic natural-language-to-symbolic blackboard translation,
- music/acoustics mathematics,
- creative parametric form generation,
- bounded physical-computing prototype templates.

No user expression is passed to Python eval/exec and no prototype endpoint executes code,
invokes a shell, flashes a device, or performs an external network action.
"""
from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Literal, Optional

import sympy as sp
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator

from app.v510 import RestrictedSympyParser, content_hash

VERSION = "5.3.0"
BLACKBOARD_SCHEMA = "sc-workbench-blackboard-object/1.0"
MUSIC_SCHEMA = "sc-workbench-music-math-object/1.0"
FORM_SCHEMA = "sc-workbench-creative-form-object/1.0"
PROTOTYPE_SCHEMA = "sc-workbench-prototype-object/1.0"
MAX_BLACKBOARD_INPUT = 2000
MAX_HARMONICS = 32
MAX_FORM_POINTS = 1201

router = APIRouter(prefix="/v530", tags=["workbench-v530-blackboard-creative-prototyping"])


def _record(schema: str, kind: str, source: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "schema": schema,
        "version": VERSION,
        "kind": kind,
        "source": source,
        **payload,
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "deviceExecutionAuthorized": False,
    }
    value["objectHash"] = content_hash(value)
    return value


def _normalize_blackboard_text(text: str) -> str:
    value = (text or "").strip()
    if not value:
        raise ValueError("Blackboard input is required.")
    if len(value) > MAX_BLACKBOARD_INPUT:
        raise ValueError(f"Blackboard input exceeds {MAX_BLACKBOARD_INPUT} characters.")
    value = (
        value.replace("−", "-")
        .replace("×", "*")
        .replace("÷", "/")
        .replace("²", "^2")
        .replace("³", "^3")
        .replace("π", "pi")
    )
    return re.sub(r"\s+", " ", value).strip()


def _split_for_variable(text: str) -> tuple[str, Optional[str]]:
    match = re.match(r"^(.*?)(?:\s+for\s+([A-Za-z][A-Za-z0-9_]*))\s*$", text, flags=re.I)
    if match:
        return match.group(1).strip(), match.group(2)
    return text.strip(), None


def _math_payload(value: Any, source: str, operation: str, precision: int = 15) -> Dict[str, Any]:
    exact = str(value)
    latex = sp.latex(value)
    try:
        decimal = str(sp.N(value, precision))
    except Exception:
        decimal = exact
    return {
        "operation": operation,
        "translatedExpression": source,
        "exactText": exact,
        "decimalText": decimal,
        "latex": latex,
        "freeSymbols": sorted(str(symbol) for symbol in getattr(value, "free_symbols", set())),
        "precision": precision,
    }


class BlackboardInput(BaseModel):
    input: str
    precision: int = Field(default=15, ge=1, le=100)


class MusicInput(BaseModel):
    mode: Literal["note", "frequency", "interval", "harmonics", "waveform"] = "note"
    note: str = "A4"
    frequencyHz: float = Field(default=440.0, gt=0, le=100000)
    secondFrequencyHz: Optional[float] = Field(default=None, gt=0, le=100000)
    semitones: int = Field(default=0, ge=-96, le=96)
    a4Hz: float = Field(default=440.0, ge=400.0, le=480.0)
    harmonics: int = Field(default=12, ge=1, le=MAX_HARMONICS)
    waveform: Literal["sine", "square", "triangle", "sawtooth"] = "sine"
    samples: int = Field(default=181, ge=33, le=721)
    speedOfSoundMps: float = Field(default=343.0, gt=250, lt=400)


class FormInput(BaseModel):
    family: Literal["lissajous", "rose", "spiral", "harmonic-orbit"] = "lissajous"
    a: float = 3.0
    b: float = 2.0
    c: float = 1.0
    phase: float = 0.0
    turns: float = Field(default=6.0, gt=0, le=50)
    points: int = Field(default=601, ge=101, le=MAX_FORM_POINTS)

    @model_validator(mode="after")
    def finite_parameters(self):
        for label in ("a", "b", "c", "phase", "turns"):
            if not math.isfinite(float(getattr(self, label))):
                raise ValueError(f"{label} must be finite.")
        return self


class PrototypeInput(BaseModel):
    target: Literal["arduino", "esp32", "raspberry-pi", "pynq", "verilog", "vhdl"] = "arduino"
    projectName: str = "signal_prototype"
    signalFrequencyHz: float = Field(default=440.0, gt=0, le=50000000)
    sampleRateHz: float = Field(default=8000.0, gt=1, le=200000000)
    pin: str = "A0"
    clockMHz: float = Field(default=100.0, gt=0.01, le=1000)


def _safe_identifier(name: str, fallback: str = "signal_prototype") -> str:
    value = re.sub(r"[^A-Za-z0-9_]+", "_", (name or "").strip()).strip("_")
    if not value:
        value = fallback
    if not re.match(r"^[A-Za-z_]", value):
        value = "p_" + value
    return value[:64]


def translate_blackboard(payload: BlackboardInput) -> Dict[str, Any]:
    text = _normalize_blackboard_text(payload.input)
    low = text.lower()
    parser = RestrictedSympyParser()
    operation = "parse"
    symbolic = text
    result: Any
    formal: Any = None
    display_input = text

    try:
        # Definite integration: "integrate x^2 from 0 to 3".
        match = re.match(r"^(?:integrate|integral of)\s+(.+?)\s+from\s+(.+?)\s+to\s+(.+?)(?:\s+(?:with respect to|wrt)\s+([A-Za-z][A-Za-z0-9_]*))?$", text, flags=re.I)
        if match:
            expr_text, lower_text, upper_text, variable_name = match.groups()
            variable_name = variable_name or "x"
            variable = parser.symbol(variable_name)
            expr = parser.parse(expr_text)
            lower = parser.parse(lower_text)
            upper = parser.parse(upper_text)
            formal = sp.Integral(expr, (variable, lower, upper))
            result = sp.integrate(expr, (variable, lower, upper))
            operation = "definite-integral"
            symbolic = f"Integral({expr_text}, ({variable_name}, {lower_text}, {upper_text}))"
        else:
            # Indefinite integration.
            match = re.match(r"^(?:integrate|integral of)\s+(.+?)(?:\s+(?:with respect to|wrt)\s+([A-Za-z][A-Za-z0-9_]*))?$", text, flags=re.I)
            if match:
                expr_text, variable_name = match.groups()
                variable_name = variable_name or "x"
                variable = parser.symbol(variable_name)
                expr = parser.parse(expr_text)
                formal = sp.Integral(expr, variable)
                result = sp.integrate(expr, variable)
                operation = "integrate"
                symbolic = f"Integral({expr_text}, {variable_name})"
            else:
                # Derivatives: d/dx expr, derivative of expr wrt x.
                match = re.match(r"^d/d([A-Za-z][A-Za-z0-9_]*)\s+(.+)$", text, flags=re.I)
                if match:
                    variable_name, expr_text = match.groups()
                    variable = parser.symbol(variable_name)
                    expr = parser.parse(expr_text)
                    formal = sp.Derivative(expr, variable)
                    result = sp.diff(expr, variable)
                    operation = "differentiate"
                    symbolic = f"Derivative({expr_text}, {variable_name})"
                else:
                    match = re.match(r"^(?:differentiate|derivative of)\s+(.+?)(?:\s+(?:with respect to|wrt)\s+([A-Za-z][A-Za-z0-9_]*))?$", text, flags=re.I)
                    if match:
                        expr_text, variable_name = match.groups()
                        variable_name = variable_name or "x"
                        variable = parser.symbol(variable_name)
                        expr = parser.parse(expr_text)
                        formal = sp.Derivative(expr, variable)
                        result = sp.diff(expr, variable)
                        operation = "differentiate"
                        symbolic = f"Derivative({expr_text}, {variable_name})"
                    elif low.startswith("solve "):
                        equation_text, variable_name = _split_for_variable(text[6:].strip())
                        equation = parser.equation(equation_text)
                        variables = [parser.symbol(variable_name)] if variable_name else sorted(equation.free_symbols, key=str)
                        if not variables:
                            raise ValueError("Solve requires at least one symbolic variable.")
                        formal = equation
                        result = sp.solve(equation, variables if len(variables) > 1 else variables[0], dict=len(variables) > 1)
                        operation = "solve"
                        symbolic = str(equation)
                    elif low.startswith("factor "):
                        expr_text = text[7:].strip()
                        formal = parser.parse(expr_text)
                        result = sp.factor(formal)
                        operation = "factor"
                        symbolic = expr_text
                    elif low.startswith("expand "):
                        expr_text = text[7:].strip()
                        formal = parser.parse(expr_text)
                        result = sp.expand(formal)
                        operation = "expand"
                        symbolic = expr_text
                    elif low.startswith("simplify "):
                        expr_text = text[9:].strip()
                        formal = parser.parse(expr_text)
                        result = sp.simplify(formal)
                        operation = "simplify"
                        symbolic = expr_text
                    else:
                        formal = parser.equation(text)
                        result = formal
                        operation = "parse"
                        symbolic = text

        if operation == "solve":
            solution_payload = []
            for item in result if isinstance(result, (list, tuple)) else [result]:
                if isinstance(item, dict):
                    solution_payload.append({str(k): {"exact": str(v), "decimal": str(sp.N(v, payload.precision)), "latex": sp.latex(v)} for k, v in item.items()})
                else:
                    solution_payload.append({"exact": str(item), "decimal": str(sp.N(item, payload.precision)), "latex": sp.latex(item)})
            record = _record(
                BLACKBOARD_SCHEMA,
                "solution",
                {"input": display_input},
                {
                    "operation": operation,
                    "translatedExpression": symbolic,
                    "translatedLatex": sp.latex(formal) if formal is not None else symbolic,
                    "translatedPretty": sp.pretty(formal, use_unicode=True) if formal is not None else symbolic,
                    "latex": sp.latex(formal) if formal is not None else symbolic,
                    "solutions": solution_payload,
                    "solutionCount": len(solution_payload),
                },
            )
        else:
            math_payload = _math_payload(result, symbolic, operation, payload.precision)
            if formal is None:
                formal = result
            math_payload["translatedLatex"] = sp.latex(formal)
            math_payload["translatedPretty"] = sp.pretty(formal, use_unicode=True)
            math_payload["resultPretty"] = sp.pretty(result, use_unicode=True)
            record = _record(BLACKBOARD_SCHEMA, "mathematics", {"input": display_input}, math_payload)
        return {"ok": True, "result": record}
    except (ValueError, TypeError, sp.SympifyError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


_NOTE_PATTERN = re.compile(r"^([A-Ga-g])([#b]?)(-?\d+)$")
_NOTE_INDEX = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
_NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _note_to_midi(note: str) -> int:
    match = _NOTE_PATTERN.match((note or "").strip())
    if not match:
        raise ValueError("Note must look like A4, C#5, or Bb3.")
    letter, accidental, octave_text = match.groups()
    pitch = _NOTE_INDEX[letter.upper()]
    if accidental == "#":
        pitch += 1
    elif accidental == "b":
        pitch -= 1
    octave = int(octave_text)
    midi = (octave + 1) * 12 + pitch
    if not 0 <= midi <= 127:
        raise ValueError("Note is outside MIDI 0–127.")
    return midi


def _midi_to_note(midi: int) -> str:
    midi = max(0, min(127, int(midi)))
    return f"{_NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def _frequency_for_midi(midi: float, a4: float) -> float:
    return a4 * (2.0 ** ((float(midi) - 69.0) / 12.0))


def _frequency_note_info(freq: float, a4: float) -> Dict[str, Any]:
    midi_float = 69.0 + 12.0 * math.log2(freq / a4)
    nearest = round(midi_float)
    nearest_freq = _frequency_for_midi(nearest, a4)
    cents = 1200.0 * math.log2(freq / nearest_freq)
    return {"nearestNote": _midi_to_note(nearest), "midi": nearest, "centsFromNearest": round(cents, 6), "nearestFrequencyHz": round(nearest_freq, 9)}


def music_math(payload: MusicInput) -> Dict[str, Any]:
    try:
        if payload.mode == "note":
            midi = _note_to_midi(payload.note)
            freq = _frequency_for_midi(midi, payload.a4Hz)
        else:
            freq = float(payload.frequencyHz)
            midi = round(69.0 + 12.0 * math.log2(freq / payload.a4Hz))

        wavelength = payload.speedOfSoundMps / freq
        harmonic_rows = []
        for n in range(1, payload.harmonics + 1):
            hf = freq * n
            info = _frequency_note_info(hf, payload.a4Hz)
            harmonic_rows.append({"n": n, "frequencyHz": round(hf, 9), "ratio": f"{n}:1", **info})

        interval = None
        second = payload.secondFrequencyHz
        if payload.mode == "interval" and second is None:
            second = freq * (2.0 ** (payload.semitones / 12.0))
        if second is not None:
            ratio = second / freq
            cents = 1200.0 * math.log2(ratio)
            interval = {"secondFrequencyHz": round(second, 9), "ratio": round(ratio, 12), "cents": round(cents, 6), "semitones": round(cents / 100.0, 6)}

        samples = []
        for i in range(payload.samples):
            phase = 2.0 * math.pi * i / (payload.samples - 1)
            sine = math.sin(phase)
            if payload.waveform == "square":
                amp = 1.0 if sine >= 0 else -1.0
            elif payload.waveform == "triangle":
                amp = (2.0 / math.pi) * math.asin(sine)
            elif payload.waveform == "sawtooth":
                amp = 2.0 * ((i / (payload.samples - 1)) - math.floor(0.5 + i / (payload.samples - 1)))
            else:
                amp = sine
            samples.append({"phase": round(phase, 9), "amplitude": round(amp, 9)})

        info = _frequency_note_info(freq, payload.a4Hz)
        record = _record(
            MUSIC_SCHEMA,
            "music-mathematics",
            {"mode": payload.mode, "note": payload.note, "frequencyHz": payload.frequencyHz, "a4Hz": payload.a4Hz},
            {
                "frequencyHz": round(freq, 9),
                "periodSeconds": round(1.0 / freq, 12),
                "wavelengthMeters": round(wavelength, 9),
                "angularFrequencyRadPerSecond": round(2.0 * math.pi * freq, 9),
                **info,
                "interval": interval,
                "harmonics": harmonic_rows,
                "waveform": payload.waveform,
                "waveformSamples": samples,
            },
        )
        return {"ok": True, "result": record}
    except (ValueError, OverflowError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def creative_form(payload: FormInput) -> Dict[str, Any]:
    points: List[Dict[str, float]] = []
    max_abs = 0.0
    for i in range(payload.points):
        t = 2.0 * math.pi * payload.turns * i / (payload.points - 1)
        if payload.family == "lissajous":
            x = payload.c * math.sin(payload.a * t + payload.phase)
            y = payload.c * math.sin(payload.b * t)
        elif payload.family == "rose":
            r = payload.c * math.cos(payload.b * t)
            x = r * math.cos(t)
            y = r * math.sin(t)
        elif payload.family == "spiral":
            r = payload.c * (i / (payload.points - 1))
            x = r * math.cos(payload.a * t + payload.phase)
            y = r * math.sin(payload.b * t)
        else:  # harmonic-orbit
            x = payload.c * (math.sin(payload.a * t + payload.phase) + 0.35 * math.sin((payload.a + payload.b) * t))
            y = payload.c * (math.cos(payload.b * t) - 0.35 * math.cos((payload.a + payload.b) * t + payload.phase))
        max_abs = max(max_abs, abs(x), abs(y))
        points.append({"t": round(t, 9), "x": round(x, 9), "y": round(y, 9)})
    record = _record(
        FORM_SCHEMA,
        "creative-form",
        {"family": payload.family, "a": payload.a, "b": payload.b, "c": payload.c, "phase": payload.phase, "turns": payload.turns},
        {"points": points, "extent": round(max_abs or 1.0, 9), "pointCount": len(points)},
    )
    return {"ok": True, "result": record}


def _prototype_scaffold(payload: PrototypeInput) -> tuple[str, str, List[str]]:
    project = _safe_identifier(payload.projectName)
    freq = float(payload.signalFrequencyHz)
    sample_rate = float(payload.sampleRateHz)
    target = payload.target
    if target == "arduino":
        code = f"""// Sustainable Catalyst Workbench v5.3.0 — Arduino prototype scaffold
// Review board voltage, pin mapping, timer limits, load, and electrical safety before use.
const int SIGNAL_PIN = 9;
const unsigned long HALF_PERIOD_US = (unsigned long)(500000.0 / {freq:.9g});

void setup() {{ pinMode(SIGNAL_PIN, OUTPUT); }}
void loop() {{
  digitalWrite(SIGNAL_PIN, HIGH); delayMicroseconds(HALF_PERIOD_US);
  digitalWrite(SIGNAL_PIN, LOW);  delayMicroseconds(HALF_PERIOD_US);
}}
"""
        return "arduino.ino", code, ["Arduino-compatible board", "logic-level output", "verify timer accuracy"]
    if target == "esp32":
        code = f"""// Sustainable Catalyst Workbench v5.3.0 — ESP32 prototype scaffold
const int SIGNAL_PIN = 18;
const int PWM_CHANNEL = 0;
void setup() {{
  ledcSetup(PWM_CHANNEL, {freq:.9g}, 10);
  ledcAttachPin(SIGNAL_PIN, PWM_CHANNEL);
  ledcWrite(PWM_CHANNEL, 512);
}}
void loop() {{ delay(1000); }}
"""
        return "esp32_signal.ino", code, ["ESP32", "LEDC/PWM", "verify current and connected load"]
    if target == "raspberry-pi":
        code = f"""# Sustainable Catalyst Workbench v5.3.0 — Raspberry Pi bounded prototype scaffold
# This file is generated only; Workbench does not execute it remotely.
import math
sample_rate = {sample_rate:.9g}
frequency = {freq:.9g}
samples = [math.sin(2*math.pi*frequency*n/sample_rate) for n in range(256)]
print(samples[:8])
"""
        return "raspberry_pi_signal.py", code, ["Raspberry Pi", "Python", "offline/sample-generation scaffold"]
    if target == "pynq":
        code = f"""# Sustainable Catalyst Workbench v5.3.0 — PYNQ prototype scaffold
# Requires a reviewed bitstream and the PYNQ runtime on the target board.
from pynq import Overlay
BITSTREAM = \"{project}.bit\"
overlay = Overlay(BITSTREAM)
# Bind reviewed IP blocks explicitly, e.g. overlay.axi_gpio_0
# Target signal frequency: {freq:.9g} Hz
# No bitstream is loaded by the public Workbench; this is an export scaffold only.
print(overlay.ip_dict.keys())
"""
        return "pynq_overlay.py", code, ["PYNQ board", "reviewed .bit overlay", "explicit IP binding", "no automatic device programming"]
    if target == "vhdl":
        half_cycles = max(1, round(payload.clockMHz * 1_000_000 / (2.0 * freq)))
        code = f"""-- Sustainable Catalyst Workbench v5.3.0 — VHDL signal prototype
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
entity {project} is
  port(clk : in std_logic; reset_n : in std_logic; signal_out : out std_logic);
end entity;
architecture rtl of {project} is
  constant HALF_CYCLES : integer := {half_cycles};
  signal counter : integer range 0 to HALF_CYCLES-1 := 0;
  signal q : std_logic := '0';
begin
  process(clk) begin
    if rising_edge(clk) then
      if reset_n='0' then counter<=0; q<='0';
      elsif counter=HALF_CYCLES-1 then counter<=0; q<=not q;
      else counter<=counter+1; end if;
    end if;
  end process;
  signal_out <= q;
end architecture;
"""
        return f"{project}.vhd", code, ["VHDL", f"nominal clock {payload.clockMHz:g} MHz", "simulate + constrain + synthesize before hardware"]
    half_cycles = max(1, round(payload.clockMHz * 1_000_000 / (2.0 * freq)))
    code = f"""// Sustainable Catalyst Workbench v5.3.0 — Verilog signal prototype
module {project}(
  input wire clk,
  input wire reset_n,
  output reg signal_out
);
  localparam integer HALF_CYCLES = {half_cycles};
  integer counter = 0;
  always @(posedge clk) begin
    if (!reset_n) begin counter <= 0; signal_out <= 1'b0; end
    else if (counter == HALF_CYCLES-1) begin counter <= 0; signal_out <= ~signal_out; end
    else counter <= counter + 1;
  end
endmodule
"""
    return f"{project}.v", code, ["Verilog", f"nominal clock {payload.clockMHz:g} MHz", "simulate + constrain + synthesize before hardware"]


def prototype(payload: PrototypeInput) -> Dict[str, Any]:
    filename, code, requirements = _prototype_scaffold(payload)
    record = _record(
        PROTOTYPE_SCHEMA,
        "prototype-scaffold",
        {"target": payload.target, "projectName": payload.projectName},
        {
            "filename": filename,
            "code": code,
            "requirements": requirements,
            "signalFrequencyHz": payload.signalFrequencyHz,
            "sampleRateHz": payload.sampleRateHz,
            "clockMHz": payload.clockMHz,
            "execution": "export-only",
            "programmingAuthorized": False,
            "flashingAuthorized": False,
        },
    )
    return {"ok": True, "result": record}


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-v530-status/1.0",
        "version": VERSION,
        "capabilities": [
            "computational-blackboard",
            "deterministic-symbolic-translation",
            "creative-mathematics",
            "music-acoustics-mathematics",
            "note-frequency-conversion",
            "harmonic-series",
            "interval-cents-analysis",
            "waveform-generation",
            "mathematics-to-form",
            "physical-prototype-scaffolds",
            "arduino",
            "esp32",
            "raspberry-pi",
            "pynq",
            "verilog",
            "vhdl",
            "homepage-computational-instrument",
        ],
        "inherits": {"cas": "5.1.0", "graphMathematics": "5.2.0"},
        "prototypeTargets": ["arduino", "esp32", "raspberry-pi", "pynq", "verilog", "vhdl"],
        "executionBoundary": "templates-and-mathematics-only",
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "deviceExecutionAuthorized": False,
        "automaticDeviceProgrammingAuthorized": False,
    }


@router.get("/status")
def status_endpoint() -> Dict[str, Any]:
    return status_record()


@router.post("/blackboard/translate")
def blackboard_endpoint(payload: BlackboardInput) -> Dict[str, Any]:
    return translate_blackboard(payload)


@router.post("/music")
def music_endpoint(payload: MusicInput) -> Dict[str, Any]:
    return music_math(payload)


@router.post("/form")
def form_endpoint(payload: FormInput) -> Dict[str, Any]:
    return creative_form(payload)


@router.post("/prototype")
def prototype_endpoint(payload: PrototypeInput) -> Dict[str, Any]:
    return prototype(payload)
