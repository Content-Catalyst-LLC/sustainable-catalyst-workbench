"""Workbench v5.9.0 — FPGA, PYNQ & Digital Logic Workbench.

Deterministic digital-logic analysis and export-only FPGA/PYNQ planning. Supports
restricted Boolean expressions, truth tables, logic minimization, Karnaugh maps,
finite-state-machine validation, timing/waveform analysis, resource estimates,
and Verilog/VHDL/PYNQ scaffolds.

This module never invokes a synthesis tool, shell, JTAG programmer, FPGA cable,
board GPIO, serial port, or bitstream loader. Generated HDL and constraints are
text artifacts for human review and external toolchains only.
"""
from __future__ import annotations

import itertools
import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, model_validator
from sympy import Symbol
from sympy.logic.boolalg import And, Not, Or, Xor, simplify_logic

from app.v510 import content_hash

VERSION = "5.9.0"
SCHEMA = "sc-workbench-digital-logic-object/1.0"
MAX_VARIABLES = 10
MAX_TRUTH_ROWS = 1 << MAX_VARIABLES
MAX_STATES = 64
MAX_TRANSITIONS = 512
MAX_TIMING_SAMPLES = 2048
MAX_PORTS = 64

router = APIRouter(prefix="/v590", tags=["workbench-v590-digital-logic-fpga"])


@dataclass(frozen=True)
class LogicNode:
    op: str
    value: Optional[str] = None
    left: Optional["LogicNode"] = None
    right: Optional["LogicNode"] = None


_TOKEN_RE = re.compile(
    r"\s*(?:(?P<ident>[A-Za-z][A-Za-z0-9_]{0,31})|(?P<const>[01])|(?P<op>[!~&|^()]))"
)


def _tokenize(expression: str) -> List[Tuple[str, str]]:
    text = str(expression).strip()
    if not text or len(text) > 512:
        raise ValueError("Boolean expression must contain 1–512 characters.")
    out: List[Tuple[str, str]] = []
    pos = 0
    while pos < len(text):
        match = _TOKEN_RE.match(text, pos)
        if not match:
            raise ValueError(f"Unsupported Boolean syntax near character {pos + 1}.")
        pos = match.end()
        if match.group("ident"):
            word = match.group("ident")
            upper = word.upper()
            if upper in {"NOT", "AND", "OR", "XOR"}:
                mapped = {"NOT": "!", "AND": "&", "OR": "|", "XOR": "^"}[upper]
                out.append(("op", mapped))
            else:
                out.append(("ident", word))
        elif match.group("const"):
            out.append(("const", match.group("const")))
        else:
            out.append(("op", match.group("op")))
    return out


class _LogicParser:
    def __init__(self, tokens: Sequence[Tuple[str, str]]):
        self.tokens = list(tokens)
        self.index = 0

    def current(self) -> Optional[Tuple[str, str]]:
        return self.tokens[self.index] if self.index < len(self.tokens) else None

    def eat(self, value: Optional[str] = None) -> Tuple[str, str]:
        token = self.current()
        if token is None:
            raise ValueError("Unexpected end of Boolean expression.")
        if value is not None and token[1] != value:
            raise ValueError(f"Expected '{value}'.")
        self.index += 1
        return token

    def parse(self) -> LogicNode:
        node = self.parse_or()
        if self.current() is not None:
            raise ValueError(f"Unexpected token '{self.current()[1]}'.")
        return node

    def parse_or(self) -> LogicNode:
        node = self.parse_xor()
        while self.current() and self.current()[1] == "|":
            self.eat("|")
            node = LogicNode("or", left=node, right=self.parse_xor())
        return node

    def parse_xor(self) -> LogicNode:
        node = self.parse_and()
        while self.current() and self.current()[1] == "^":
            self.eat("^")
            node = LogicNode("xor", left=node, right=self.parse_and())
        return node

    def parse_and(self) -> LogicNode:
        node = self.parse_unary()
        while self.current() and self.current()[1] == "&":
            self.eat("&")
            node = LogicNode("and", left=node, right=self.parse_unary())
        return node

    def parse_unary(self) -> LogicNode:
        token = self.current()
        if token and token[1] in {"!", "~"}:
            self.eat()
            return LogicNode("not", left=self.parse_unary())
        return self.parse_primary()

    def parse_primary(self) -> LogicNode:
        token = self.current()
        if token is None:
            raise ValueError("Expected a Boolean variable, constant, or parenthesized expression.")
        if token[0] == "ident":
            self.eat()
            return LogicNode("var", value=token[1])
        if token[0] == "const":
            self.eat()
            return LogicNode("const", value=token[1])
        if token[1] == "(":
            self.eat("(")
            node = self.parse_or()
            self.eat(")")
            return node
        raise ValueError(f"Unexpected token '{token[1]}'.")


def parse_logic(expression: str) -> LogicNode:
    return _LogicParser(_tokenize(expression)).parse()


def _variables(node: LogicNode) -> List[str]:
    names: set[str] = set()
    def visit(n: LogicNode) -> None:
        if n.op == "var" and n.value:
            names.add(n.value)
        if n.left:
            visit(n.left)
        if n.right:
            visit(n.right)
    visit(node)
    ordered = sorted(names, key=lambda x: (x.lower(), x))
    if len(ordered) > MAX_VARIABLES:
        raise ValueError(f"A Boolean expression may contain at most {MAX_VARIABLES} variables.")
    return ordered


def _evaluate(node: LogicNode, values: Dict[str, bool]) -> bool:
    if node.op == "var":
        return bool(values.get(str(node.value), False))
    if node.op == "const":
        return node.value == "1"
    if node.op == "not":
        return not _evaluate(node.left, values)  # type: ignore[arg-type]
    if node.op == "and":
        return _evaluate(node.left, values) and _evaluate(node.right, values)  # type: ignore[arg-type]
    if node.op == "or":
        return _evaluate(node.left, values) or _evaluate(node.right, values)  # type: ignore[arg-type]
    if node.op == "xor":
        return _evaluate(node.left, values) != _evaluate(node.right, values)  # type: ignore[arg-type]
    raise ValueError(f"Unsupported logic node: {node.op}")


def _sympy(node: LogicNode, symbols: Dict[str, Symbol]):
    if node.op == "var":
        return symbols[str(node.value)]
    if node.op == "const":
        return bool(node.value == "1")
    if node.op == "not":
        return Not(_sympy(node.left, symbols))  # type: ignore[arg-type]
    if node.op == "and":
        return And(_sympy(node.left, symbols), _sympy(node.right, symbols))  # type: ignore[arg-type]
    if node.op == "or":
        return Or(_sympy(node.left, symbols), _sympy(node.right, symbols))  # type: ignore[arg-type]
    if node.op == "xor":
        return Xor(_sympy(node.left, symbols), _sympy(node.right, symbols))  # type: ignore[arg-type]
    raise ValueError(f"Unsupported logic node: {node.op}")


def _logic_text(expr: Any) -> str:
    text = str(expr)
    replacements = {
        "~": "!",
        " & ": " & ",
        " | ": " | ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def _logic_stats(node: LogicNode) -> Dict[str, int]:
    counts = {"and": 0, "or": 0, "xor": 0, "not": 0, "gates": 0, "logicDepth": 0}
    def walk(n: LogicNode) -> int:
        if n.op in {"var", "const"}:
            return 0
        counts[n.op] += 1
        counts["gates"] += 1
        left_depth = walk(n.left) if n.left else 0
        right_depth = walk(n.right) if n.right else 0
        return 1 + max(left_depth, right_depth)
    counts["logicDepth"] = walk(node)
    return counts


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
        "synthesisExecutionAuthorized": False,
        "bitstreamGenerationAuthorized": False,
        "bitstreamProgrammingAuthorized": False,
        "jtagAccessAuthorized": False,
        "deviceExecutionAuthorized": False,
    }
    value["digitalLogicObjectHash"] = content_hash(value)
    return value


class BooleanExpressionInput(BaseModel):
    expression: str = Field(default="(A & B) | (!A & C)", min_length=1, max_length=512)


class KarnaughInput(BooleanExpressionInput):
    variables: Optional[List[str]] = Field(default=None, max_length=4)


class FSMTransition(BaseModel):
    fromState: str = Field(min_length=1, max_length=32)
    input: str = Field(default="0", min_length=1, max_length=32)
    toState: str = Field(min_length=1, max_length=32)
    output: Optional[str] = Field(default=None, max_length=32)


class FSMInput(BaseModel):
    states: List[str] = Field(min_length=1, max_length=MAX_STATES)
    initialState: str = Field(min_length=1, max_length=32)
    transitions: List[FSMTransition] = Field(min_length=1, max_length=MAX_TRANSITIONS)
    encoding: Literal["binary", "gray", "one-hot"] = "binary"

    @model_validator(mode="after")
    def validate_fsm(self):
        normalized = [s.strip() for s in self.states]
        if any(not s for s in normalized):
            raise ValueError("State names may not be blank.")
        if len(set(normalized)) != len(normalized):
            raise ValueError("State names must be unique.")
        if self.initialState not in normalized:
            raise ValueError("initialState must appear in states.")
        known = set(normalized)
        seen: set[Tuple[str, str]] = set()
        for transition in self.transitions:
            if transition.fromState not in known or transition.toState not in known:
                raise ValueError("Every transition state must appear in states.")
            key = (transition.fromState, transition.input)
            if key in seen:
                raise ValueError("FSM must be deterministic: duplicate state/input transition.")
            seen.add(key)
        return self


class TimingSignal(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    values: List[Literal[0, 1]] = Field(min_length=1, max_length=MAX_TIMING_SAMPLES)


class TimingInput(BaseModel):
    expression: str = Field(default="A ^ B", min_length=1, max_length=512)
    signals: List[TimingSignal] = Field(min_length=1, max_length=MAX_VARIABLES)
    samplePeriodNs: float = Field(default=10.0, gt=0, le=1e12)

    @model_validator(mode="after")
    def validate_timing(self):
        lengths = {len(signal.values) for signal in self.signals}
        if len(lengths) != 1:
            raise ValueError("All timing signals must contain the same number of samples.")
        names = [signal.name for signal in self.signals]
        if len(set(names)) != len(names):
            raise ValueError("Timing signal names must be unique.")
        node = parse_logic(self.expression)
        missing = sorted(set(_variables(node)) - set(names))
        if missing:
            raise ValueError("Timing input is missing signals: " + ", ".join(missing))
        return self


class HDLScaffoldInput(BaseModel):
    language: Literal["verilog", "vhdl"] = "verilog"
    moduleName: str = Field(default="catalyst_logic", min_length=1, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    expression: str = Field(default="(A & B) | (!A & C)", min_length=1, max_length=512)
    outputName: str = Field(default="Y", min_length=1, max_length=32, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    includeTestbench: bool = True


class ResourceEstimateInput(BooleanExpressionInput):
    targetFamily: Literal["generic-fpga", "xilinx-7", "zynq-7000", "ultrascale", "intel-cyclone"] = "generic-fpga"
    lutInputs: int = Field(default=6, ge=2, le=8)


class PYNQOverlayInput(BaseModel):
    projectName: str = Field(default="catalyst_overlay", min_length=1, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    moduleName: str = Field(default="catalyst_logic", min_length=1, max_length=48, pattern=r"^[A-Za-z][A-Za-z0-9_]*$")
    expression: str = Field(default="A ^ B", min_length=1, max_length=512)
    board: Literal["pynq-z2", "pynq-z1", "generic-pynq"] = "generic-pynq"


def status_record() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "sc-workbench-digital-logic-fpga-status/1.0",
        "version": VERSION,
        "inherits": {
            "mathematics": "5.1.0",
            "advancedGraph": "5.4.0",
            "numericalComputing": "5.6.0",
            "signalsControl": "5.7.0",
            "electronicsEmbedded": "5.8.0",
        },
        "capabilities": [
            "restricted-boolean-expression-parser",
            "truth-tables",
            "boolean-minimization",
            "karnaugh-maps",
            "logic-gate-analysis",
            "finite-state-machine-validation",
            "state-encoding",
            "digital-timing-waveforms",
            "logic-resource-estimates",
            "verilog-scaffolds",
            "vhdl-scaffolds",
            "testbench-scaffolds",
            "pynq-overlay-scaffolds",
            "constraint-placeholders",
            "canonical-digital-logic-objects",
        ],
        "executionBoundary": "logic-analysis-simulation-and-export-only",
        "arbitraryCodeExecutionAuthorized": False,
        "pythonEvalAuthorized": False,
        "remoteShellAuthorized": False,
        "synthesisExecutionAuthorized": False,
        "bitstreamGenerationAuthorized": False,
        "bitstreamProgrammingAuthorized": False,
        "jtagAccessAuthorized": False,
        "deviceExecutionAuthorized": False,
    }


def truth_table_object(payload: BooleanExpressionInput) -> Dict[str, Any]:
    node = parse_logic(payload.expression)
    variables = _variables(node)
    if not variables:
        rows = [{"inputs": {}, "output": int(_evaluate(node, {}))}]
    else:
        rows = []
        for bits in itertools.product((0, 1), repeat=len(variables)):
            values = {name: bool(bit) for name, bit in zip(variables, bits)}
            rows.append({"inputs": {name: int(values[name]) for name in variables}, "output": int(_evaluate(node, values))})
    minterms = [idx for idx, row in enumerate(rows) if row["output"] == 1]
    maxterms = [idx for idx, row in enumerate(rows) if row["output"] == 0]
    return _record(
        "truth-table",
        {"expression": payload.expression},
        {"result": {"variables": variables, "rowCount": len(rows), "rows": rows, "minterms": minterms, "maxterms": maxterms, "logic": _logic_stats(node)}},
    )


def minimize_object(payload: BooleanExpressionInput) -> Dict[str, Any]:
    node = parse_logic(payload.expression)
    variables = _variables(node)
    symbols = {name: Symbol(name, boolean=True) for name in variables}
    expr = _sympy(node, symbols)
    sop = simplify_logic(expr, form="dnf", force=True)
    pos = simplify_logic(expr, form="cnf", force=True)
    sop_text = _logic_text(sop)
    pos_text = _logic_text(pos)
    minimized_node = parse_logic(sop_text.replace("True", "1").replace("False", "0")) if sop_text not in {"True", "False"} else LogicNode("const", value="1" if sop_text == "True" else "0")
    return _record(
        "boolean-minimization",
        {"expression": payload.expression},
        {"result": {"variables": variables, "sumOfProducts": sop_text, "productOfSums": pos_text, "originalLogic": _logic_stats(node), "minimizedLogic": _logic_stats(minimized_node)}},
    )


def _gray(n: int) -> List[int]:
    return [i ^ (i >> 1) for i in range(1 << n)]


def karnaugh_object(payload: KarnaughInput) -> Dict[str, Any]:
    node = parse_logic(payload.expression)
    discovered = _variables(node)
    variables = list(payload.variables) if payload.variables else discovered
    if set(variables) != set(discovered):
        raise ValueError("Karnaugh variables must match the expression variables exactly.")
    if not 2 <= len(variables) <= 4:
        raise ValueError("Karnaugh maps require 2–4 Boolean variables.")
    row_bits = len(variables) // 2
    col_bits = len(variables) - row_bits
    row_order, col_order = _gray(row_bits), _gray(col_bits)
    grid: List[List[int]] = []
    minterms: List[int] = []
    for r in row_order:
        grid_row: List[int] = []
        for c in col_order:
            bits = [(r >> (row_bits - 1 - i)) & 1 for i in range(row_bits)] + [(c >> (col_bits - 1 - i)) & 1 for i in range(col_bits)]
            values = {name: bool(bit) for name, bit in zip(variables, bits)}
            out = int(_evaluate(node, values))
            grid_row.append(out)
            binary_index = 0
            for bit in bits:
                binary_index = (binary_index << 1) | bit
            if out:
                minterms.append(binary_index)
        grid.append(grid_row)
    simplified = minimize_object(BooleanExpressionInput(expression=payload.expression))["result"]
    return _record(
        "karnaugh-map",
        {"expression": payload.expression, "variables": variables},
        {"result": {"variables": variables, "rowVariables": variables[:row_bits], "columnVariables": variables[row_bits:], "rowGrayOrder": row_order, "columnGrayOrder": col_order, "grid": grid, "minterms": sorted(minterms), "simplified": simplified}},
    )


def _state_codes(states: List[str], encoding: str) -> Dict[str, str]:
    count = len(states)
    if encoding == "one-hot":
        width = count
        return {state: format(1 << idx, f"0{width}b") for idx, state in enumerate(states)}
    width = max(1, math.ceil(math.log2(count)))
    if encoding == "gray":
        return {state: format(idx ^ (idx >> 1), f"0{width}b") for idx, state in enumerate(states)}
    return {state: format(idx, f"0{width}b") for idx, state in enumerate(states)}


def fsm_object(payload: FSMInput) -> Dict[str, Any]:
    states = list(payload.states)
    reachable = {payload.initialState}
    changed = True
    while changed:
        changed = False
        for transition in payload.transitions:
            if transition.fromState in reachable and transition.toState not in reachable:
                reachable.add(transition.toState)
                changed = True
    unreachable = sorted(set(states) - reachable)
    inputs_by_state: Dict[str, List[str]] = {state: [] for state in states}
    table: List[Dict[str, Any]] = []
    for t in payload.transitions:
        inputs_by_state[t.fromState].append(t.input)
        table.append({"fromState": t.fromState, "input": t.input, "toState": t.toState, "output": t.output})
    observed_inputs = sorted({t.input for t in payload.transitions})
    incomplete = {state: sorted(set(observed_inputs) - set(inputs_by_state[state])) for state in states if set(observed_inputs) - set(inputs_by_state[state])}
    warnings: List[str] = []
    if unreachable:
        warnings.append("Unreachable states: " + ", ".join(unreachable))
    if incomplete:
        warnings.append("FSM is incomplete for one or more observed input symbols.")
    codes = _state_codes(states, payload.encoding)
    return _record(
        "finite-state-machine",
        {"initialState": payload.initialState, "encoding": payload.encoding},
        {"result": {"states": states, "transitionCount": len(table), "inputAlphabet": observed_inputs, "deterministic": True, "reachableStates": sorted(reachable), "unreachableStates": unreachable, "incompleteInputsByState": incomplete, "stateEncoding": codes, "transitionTable": table, "warnings": warnings}},
    )


def timing_object(payload: TimingInput) -> Dict[str, Any]:
    node = parse_logic(payload.expression)
    variables = _variables(node)
    signal_map = {signal.name: signal.values for signal in payload.signals}
    count = len(payload.signals[0].values)
    output: List[int] = []
    for idx in range(count):
        values = {name: bool(signal_map[name][idx]) for name in variables}
        output.append(int(_evaluate(node, values)))
    transitions = []
    for idx in range(1, count):
        if output[idx] != output[idx - 1]:
            transitions.append({"sample": idx, "timeNs": round(idx * payload.samplePeriodNs, 9), "from": output[idx - 1], "to": output[idx]})
    input_transition_count = sum(sum(1 for i in range(1, count) if s.values[i] != s.values[i - 1]) for s in payload.signals)
    return _record(
        "digital-timing-waveform",
        {"expression": payload.expression, "samplePeriodNs": payload.samplePeriodNs},
        {"result": {"variables": variables, "sampleCount": count, "durationNs": round(count * payload.samplePeriodNs, 9), "signals": {s.name: s.values for s in payload.signals}, "output": output, "outputTransitions": transitions, "outputTransitionCount": len(transitions), "inputTransitionCount": input_transition_count, "propagationDelayModeled": False}},
    )


def _verilog_expr(node: LogicNode) -> str:
    if node.op == "var": return str(node.value)
    if node.op == "const": return "1'b1" if node.value == "1" else "1'b0"
    if node.op == "not": return f"~({_verilog_expr(node.left)})"  # type: ignore[arg-type]
    op = {"and": "&", "or": "|", "xor": "^"}[node.op]
    return f"({_verilog_expr(node.left)} {op} {_verilog_expr(node.right)})"  # type: ignore[arg-type]


def _vhdl_expr(node: LogicNode) -> str:
    if node.op == "var": return str(node.value)
    if node.op == "const": return "'1'" if node.value == "1" else "'0'"
    if node.op == "not": return f"not ({_vhdl_expr(node.left)})"  # type: ignore[arg-type]
    op = {"and": "and", "or": "or", "xor": "xor"}[node.op]
    return f"({_vhdl_expr(node.left)} {op} {_vhdl_expr(node.right)})"  # type: ignore[arg-type]


def hdl_scaffold_object(payload: HDLScaffoldInput) -> Dict[str, Any]:
    node = parse_logic(payload.expression)
    variables = _variables(node)
    if payload.outputName in variables:
        raise ValueError("outputName must not duplicate an input variable.")
    files: List[Dict[str, str]] = []
    if payload.language == "verilog":
        ports = ", ".join(variables + [payload.outputName])
        input_decl = f"  input wire {', '.join(variables)};\n" if variables else ""
        code = f"module {payload.moduleName}({ports});\n{input_decl}  output wire {payload.outputName};\n  assign {payload.outputName} = {_verilog_expr(node)};\nendmodule\n"
        files.append({"path": f"{payload.moduleName}.v", "content": code})
        if payload.includeTestbench:
            declarations = "\n".join(f"  reg {name};" for name in variables)
            portmap = ", ".join(f".{name}({name})" for name in variables + [payload.outputName])
            vectors = []
            for bits in itertools.product((0,1), repeat=min(len(variables), 6)):
                assigns = " ".join(f"{name}=1'b{bit};" for name, bit in zip(variables, bits))
                vectors.append(f"    {assigns} #10;")
            tb = f"`timescale 1ns/1ps\nmodule {payload.moduleName}_tb;\n{declarations}\n  wire {payload.outputName};\n  {payload.moduleName} dut({portmap});\n  initial begin\n" + "\n".join(vectors) + "\n    $finish;\n  end\nendmodule\n"
            files.append({"path": f"{payload.moduleName}_tb.v", "content": tb})
    else:
        port_lines = ";\n    ".join([f"{name} : in std_logic" for name in variables] + [f"{payload.outputName} : out std_logic"])
        code = f"library ieee;\nuse ieee.std_logic_1164.all;\n\nentity {payload.moduleName} is\n  port (\n    {port_lines}\n  );\nend entity;\n\narchitecture rtl of {payload.moduleName} is\nbegin\n  {payload.outputName} <= {_vhdl_expr(node)};\nend architecture;\n"
        files.append({"path": f"{payload.moduleName}.vhd", "content": code})
        if payload.includeTestbench:
            files.append({"path": f"{payload.moduleName}_tb.vhd", "content": "-- Testbench scaffold: add clocking/vector assertions in your external HDL simulator.\n"})
    files.append({"path": f"{payload.moduleName}.xdc", "content": "# Constraint placeholder generated by Sustainable Catalyst Workbench.\n# Assign PACKAGE_PIN and IOSTANDARD only after verifying the exact board schematic and master constraints file.\n"})
    return _record(
        "hdl-scaffold",
        {"language": payload.language, "moduleName": payload.moduleName, "expression": payload.expression},
        {"result": {"variables": variables, "output": payload.outputName, "files": files, "exportOnly": True, "requiresHumanReviewBeforeSynthesis": True, "synthesisPerformed": False, "bitstreamGenerated": False}},
    )


def resource_estimate_object(payload: ResourceEstimateInput) -> Dict[str, Any]:
    original = parse_logic(payload.expression)
    minimized = minimize_object(BooleanExpressionInput(expression=payload.expression))["result"]
    minimized_text = minimized["sumOfProducts"]
    min_node = parse_logic(minimized_text.replace("True", "1").replace("False", "0")) if minimized_text not in {"True","False"} else LogicNode("const", value="1" if minimized_text == "True" else "0")
    stats = _logic_stats(min_node)
    vars_count = len(_variables(original))
    lut_estimate = 0 if stats["gates"] == 0 else max(1, math.ceil(stats["gates"] / max(1, payload.lutInputs - 1)))
    return _record(
        "logic-resource-estimate",
        {"expression": payload.expression, "targetFamily": payload.targetFamily, "lutInputs": payload.lutInputs},
        {"result": {"variables": vars_count, "minimizedExpression": minimized_text, "gateEstimate": stats, "estimatedLUTs": lut_estimate, "estimatedFlipFlops": 0, "estimateType": "pre-synthesis-heuristic", "placementRoutingModeled": False, "timingClosureModeled": False}},
    )


def pynq_overlay_object(payload: PYNQOverlayInput) -> Dict[str, Any]:
    logic = hdl_scaffold_object(HDLScaffoldInput(language="verilog", moduleName=payload.moduleName, expression=payload.expression, outputName="Y", includeTestbench=True))["result"]
    notebook = f"from pynq import Overlay\n\n# Build the bitstream externally in Vivado after verifying constraints.\n# Then copy {payload.projectName}.bit and .hwh into this project.\noverlay = Overlay('{payload.projectName}.bit')\nprint(overlay.ip_dict)\n"
    manifest = {
        "board": payload.board,
        "projectName": payload.projectName,
        "moduleName": payload.moduleName,
        "constraintPolicy": "board-specific pins intentionally unresolved",
        "expectedArtifacts": [f"{payload.projectName}.bit", f"{payload.projectName}.hwh"],
    }
    files = list(logic["files"]) + [
        {"path": "pynq_overlay.py", "content": notebook},
        {"path": "overlay_manifest.json", "content": str(manifest).replace("'", '"')},
        {"path": "README_PYNQ.md", "content": "Review board constraints in the official master XDC before synthesis. Workbench does not build or program bitstreams.\n"},
    ]
    return _record(
        "pynq-overlay-scaffold",
        {"projectName": payload.projectName, "moduleName": payload.moduleName, "board": payload.board, "expression": payload.expression},
        {"result": {"files": files, "board": payload.board, "exportOnly": True, "vivadoExecutionPerformed": False, "bitstreamGenerated": False, "overlayLoaded": False, "physicalPinsResolved": False, "requiresOfficialBoardConstraintReview": True}},
    )


@router.get("/status")
def status() -> Dict[str, Any]:
    return status_record()


@router.post("/truth-table")
def truth_table(payload: BooleanExpressionInput) -> Dict[str, Any]:
    try:
        return truth_table_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/minimize")
def minimize(payload: BooleanExpressionInput) -> Dict[str, Any]:
    try:
        return minimize_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/karnaugh")
def karnaugh(payload: KarnaughInput) -> Dict[str, Any]:
    try:
        return karnaugh_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/fsm")
def fsm(payload: FSMInput) -> Dict[str, Any]:
    try:
        return fsm_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/timing")
def timing(payload: TimingInput) -> Dict[str, Any]:
    try:
        return timing_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/hdl-scaffold")
def hdl_scaffold(payload: HDLScaffoldInput) -> Dict[str, Any]:
    try:
        return hdl_scaffold_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/resource-estimate")
def resource_estimate(payload: ResourceEstimateInput) -> Dict[str, Any]:
    try:
        return resource_estimate_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/pynq-overlay")
def pynq_overlay(payload: PYNQOverlayInput) -> Dict[str, Any]:
    try:
        return pynq_overlay_object(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
