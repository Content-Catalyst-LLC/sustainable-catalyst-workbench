"""Workbench v2.2.0 FPGA, electronics design, and hardware validation API routes."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

router = APIRouter(prefix="/workbench/v2.2.0", tags=["workbench-v2.2.0"])
VERSION = "2.2.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class FpgaConstraint(BaseModel):
    signal: str = Field(min_length=1, max_length=120)
    pin: str = Field(min_length=1, max_length=120)
    io_standard: str = Field(default="", max_length=80)
    clock_mhz: float | None = Field(default=None, gt=0, le=2000)


class FpgaProjectRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")
    language: Literal["verilog", "systemverilog", "vhdl"]
    board: Literal["icebreaker", "ulx3s", "arty-a7", "generic"]
    clock_mhz: float = Field(gt=0, le=2000)
    top_level_source: str = Field(min_length=1, max_length=500_000)
    constraints: list[FpgaConstraint] = Field(min_length=1, max_length=1000)


class FunctionalBlock(BaseModel):
    reference: str = Field(min_length=1, max_length=80)
    type: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)


class ElectronicsRequest(BaseModel):
    design_id: str = Field(min_length=1, max_length=80)
    input_supply_v: float = Field(gt=0, le=10000)
    logic_rail_v: float = Field(gt=0, le=10000)
    estimated_load_ma: float = Field(ge=0, le=10_000_000)
    blocks: list[FunctionalBlock] = Field(min_length=1, max_length=1000)
    constraints: list[str] = Field(default_factory=list, max_length=1000)


class ComponentRecord(BaseModel):
    reference: str = Field(min_length=1, max_length=80)
    value: str = Field(default="", max_length=300)
    footprint: str = Field(default="", max_length=300)
    pins: list[str] = Field(min_length=1, max_length=1000)

    @field_validator("pins")
    @classmethod
    def unique_pins(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("pins must be unique within a component")
        return values


class NetRecord(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    endpoints: list[str] = Field(min_length=1, max_length=5000)


class SchematicRequest(BaseModel):
    components: list[ComponentRecord] = Field(min_length=1, max_length=5000)
    nets: list[NetRecord] = Field(min_length=1, max_length=5000)


class BomLine(BaseModel):
    reference: str = Field(min_length=1, max_length=200)
    manufacturer_part: str = Field(default="", max_length=300)
    description: str = Field(default="", max_length=1000)
    quantity: float = Field(gt=0, le=1_000_000)
    unit_cost: float = Field(ge=0, le=1_000_000)
    status: str = Field(default="unknown", max_length=80)
    substitute: str = Field(default="", max_length=300)


class BomRequest(BaseModel):
    currency: Literal["USD", "EUR", "GBP"] = "USD"
    budget: float | None = Field(default=None, gt=0, le=1_000_000_000)
    lifecycle_policy: Literal["strict", "review", "prototype"] = "strict"
    lines: list[BomLine] = Field(min_length=1, max_length=20_000)


class PlacementRecord(BaseModel):
    reference: str = Field(min_length=1, max_length=80)
    x_mm: float
    y_mm: float
    rotation: float = Field(ge=-3600, le=3600)
    side: Literal["top", "bottom"]
    component_class: str = Field(default="general", max_length=120)


class PcbRequest(BaseModel):
    width_mm: float = Field(gt=0, le=10_000)
    height_mm: float = Field(gt=0, le=10_000)
    copper_layers: Literal[2, 4, 6, 8, 10, 12]
    minimum_track_space_mm: float = Field(gt=0, le=100)
    minimum_via_drill_mm: float = Field(gt=0, le=100)
    edge_clearance_mm: float = Field(ge=0, le=1000)
    environment: Literal["indoor", "industrial", "outdoor"] = "indoor"
    placements: list[PlacementRecord] = Field(min_length=1, max_length=100_000)


class TestDefinition(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    measurement: str = Field(min_length=1, max_length=300)
    minimum: float
    maximum: float
    unit: str = Field(default="", max_length=80)
    method: str = Field(default="", max_length=1000)


class TestResult(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    value: float
    note: str = Field(default="", max_length=4000)
    evidence: str = Field(default="", max_length=1000)


class ValidationRequest(BaseModel):
    device_id: str = Field(min_length=1, max_length=160)
    revision: str = Field(default="", max_length=80)
    stage: Literal["bring-up", "verification", "environmental", "production"]
    tests: list[TestDefinition] = Field(min_length=1, max_length=20_000)
    results: list[TestResult] = Field(default_factory=list, max_length=20_000)


@router.get("/status")
def status() -> dict[str, object]:
    return {
        "ok": True,
        "version": VERSION,
        "release": "FPGA, Electronics Design, and Hardware Validation Studio",
        "browserLocal": True,
        "localRunner": {
            "service": "http://127.0.0.1:8787",
            "pairingRequired": True,
            "arbitraryShellEndpoint": False,
        },
        "capabilities": [
            "fpga-project-and-constraint-records",
            "electronics-architecture-review",
            "structured-schematic-and-netlist-validation",
            "bom-cost-lifecycle-and-substitution-review",
            "preliminary-pcb-planning-and-design-rule-review",
            "hardware-test-plan-evaluation-and-dossiers",
        ],
    }


@router.get("/fpga/boards")
def fpga_boards() -> dict[str, object]:
    return {
        "ok": True,
        "version": VERSION,
        "boards": [
            {"id": "icebreaker", "family": "Lattice iCE40UP5K", "openFlow": ["yosys", "nextpnr-ice40", "icepack", "openFPGALoader"]},
            {"id": "ulx3s", "family": "Lattice ECP5", "openFlow": ["yosys", "nextpnr-ecp5", "ecppack", "openFPGALoader"]},
            {"id": "arty-a7", "family": "AMD/Xilinx Artix-7", "flow": ["Vivado"]},
            {"id": "generic", "family": "Generic FPGA", "flow": ["user-defined"]},
        ],
    }


@router.post("/fpga/projects")
def fpga_project(request: FpgaProjectRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    signals = [item.signal for item in request.constraints]
    pins = [item.pin for item in request.constraints]
    if len(signals) != len(set(signals)):
        findings.append({"severity": "error", "code": "duplicate-signal", "message": "constraint signals must be unique"})
    if len(pins) != len(set(pins)):
        findings.append({"severity": "error", "code": "duplicate-pin", "message": "physical pins must be unique"})
    if not any("clk" in signal.lower() or "clock" in signal.lower() for signal in signals):
        findings.append({"severity": "warning", "code": "clock-unidentified", "message": "no clock-like signal was identified"})
    extension = {"verilog": "v", "systemverilog": "sv", "vhdl": "vhd"}[request.language]
    constraint_extension = {"icebreaker": "pcf", "ulx3s": "lpf"}.get(request.board, "xdc")
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-fpga-project/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "project": request.model_dump(),
        "clockPeriodNs": 1000.0 / request.clock_mhz,
        "files": [f"rtl/top.{extension}", f"constraints/{request.project_id}.{constraint_extension}", "project.json", "validation/implementation-review.md"],
        "findings": findings,
        "validationGates": ["lint", "simulation", "clock-domain review", "constraints review", "synthesis", "timing closure", "hardware bring-up"],
    }


@router.post("/electronics/review")
def electronics_review(request: ElectronicsRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    references = [block.reference for block in request.blocks]
    types = [block.type.lower() for block in request.blocks]
    if len(references) != len(set(references)):
        findings.append({"severity": "error", "code": "duplicate-reference", "message": "block references must be unique"})
    if request.input_supply_v > request.logic_rail_v and not any("regulator" in item or "converter" in item for item in types):
        findings.append({"severity": "error", "code": "missing-regulation", "message": "voltage conversion is required but no regulator or converter block was identified"})
    if not any(any(token in item for token in ("protection", "esd", "fuse", "tvs")) for item in types):
        findings.append({"severity": "warning", "code": "protection-review", "message": "no protection block was identified"})
    if not any(any(token in item for token in ("decoupling", "capacitor", "filter")) for item in types):
        findings.append({"severity": "warning", "code": "decoupling-review", "message": "no decoupling or filtering block was identified"})
    linear_loss_w = max(0.0, (request.input_supply_v - request.logic_rail_v) * request.estimated_load_ma / 1000.0)
    if linear_loss_w > 0.5:
        findings.append({"severity": "warning", "code": "thermal-regulator", "message": f"linear-regulator assumption dissipates approximately {linear_loss_w:.3f} W"})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-electronics-architecture/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "design": request.model_dump(),
        "power": {
            "inputPowerW": request.input_supply_v * request.estimated_load_ma / 1000.0,
            "loadPowerW": request.logic_rail_v * request.estimated_load_ma / 1000.0,
            "linearRegulatorLossW": linear_loss_w,
        },
        "findings": findings,
        "reviewGates": ["ratings", "power budget", "protection", "decoupling", "grounding", "thermal", "EMC", "test access"],
    }


@router.post("/schematic/validate")
def schematic_validate(request: SchematicRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    references = [component.reference for component in request.components]
    if len(references) != len(set(references)):
        findings.append({"severity": "error", "code": "duplicate-component-reference", "message": "component references must be unique"})
    net_names = [net.name for net in request.nets]
    if len(net_names) != len(set(net_names)):
        findings.append({"severity": "error", "code": "duplicate-net-name", "message": "net names must be unique"})
    valid_endpoints = {f"{component.reference}.{pin}" for component in request.components for pin in component.pins}
    endpoint_to_net: dict[str, str] = {}
    for net in request.nets:
        for endpoint in net.endpoints:
            if endpoint not in valid_endpoints:
                findings.append({"severity": "error", "code": "unknown-endpoint", "net": net.name, "endpoint": endpoint})
            previous = endpoint_to_net.get(endpoint)
            if previous is not None and previous != net.name:
                findings.append({"severity": "error", "code": "endpoint-on-multiple-nets", "endpoint": endpoint, "nets": [previous, net.name]})
            endpoint_to_net[endpoint] = net.name
    for endpoint in sorted(valid_endpoints - set(endpoint_to_net)):
        findings.append({"severity": "warning", "code": "unconnected-pin", "endpoint": endpoint})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-structured-schematic/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "components": [item.model_dump() for item in request.components],
        "nets": [item.model_dump() for item in request.nets],
        "findings": findings,
    }


@router.post("/bom/validate")
def bom_validate(request: BomRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    records: list[dict[str, object]] = []
    total = 0.0
    for line in request.lines:
        record = line.model_dump()
        record["extended_cost"] = line.quantity * line.unit_cost
        total += record["extended_cost"]
        status = line.status.lower()
        if not line.manufacturer_part:
            findings.append({"severity": "error", "code": "missing-mpn", "reference": line.reference})
        if request.lifecycle_policy == "strict" and status != "active":
            findings.append({"severity": "error", "code": "lifecycle-policy", "reference": line.reference, "status": status})
        elif status in {"obsolete", "eol"}:
            findings.append({"severity": "error", "code": "obsolete-part", "reference": line.reference, "status": status})
        elif status != "active":
            findings.append({"severity": "warning", "code": "lifecycle-review", "reference": line.reference, "status": status})
        if not line.substitute:
            findings.append({"severity": "warning", "code": "no-substitute", "reference": line.reference})
        records.append(record)
    if request.budget is not None and total > request.budget:
        findings.append({"severity": "error", "code": "over-budget", "estimatedTotal": total, "budget": request.budget})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-validated-bom/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "currency": request.currency,
        "budget": request.budget,
        "estimatedTotal": total,
        "lifecyclePolicy": request.lifecycle_policy,
        "records": records,
        "findings": findings,
    }


@router.post("/pcb/review")
def pcb_review(request: PcbRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    references = [item.reference for item in request.placements]
    if len(references) != len(set(references)):
        findings.append({"severity": "error", "code": "duplicate-reference", "message": "placement references must be unique"})
    occupied: set[tuple[float, float, str]] = set()
    for item in request.placements:
        if item.x_mm < request.edge_clearance_mm or item.x_mm > request.width_mm - request.edge_clearance_mm or item.y_mm < request.edge_clearance_mm or item.y_mm > request.height_mm - request.edge_clearance_mm:
            findings.append({"severity": "error", "code": "outside-usable-outline", "reference": item.reference})
        key = (item.x_mm, item.y_mm, item.side)
        if key in occupied:
            findings.append({"severity": "error", "code": "coordinate-collision", "reference": item.reference})
        occupied.add(key)
    thresholds = {
        "indoor": {"track": 0.10, "edge": 0.20},
        "industrial": {"track": 0.18, "edge": 0.35},
        "outdoor": {"track": 0.20, "edge": 0.50},
    }[request.environment]
    if request.minimum_track_space_mm < thresholds["track"]:
        findings.append({"severity": "warning", "code": "track-space-review", "thresholdMm": thresholds["track"]})
    if request.edge_clearance_mm < thresholds["edge"]:
        findings.append({"severity": "warning", "code": "edge-clearance-review", "thresholdMm": thresholds["edge"]})
    return {
        "ok": not any(item["severity"] == "error" for item in findings),
        "schema": "sc-workbench-pcb-plan/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "outline": {"widthMm": request.width_mm, "heightMm": request.height_mm, "areaMm2": request.width_mm * request.height_mm},
        "stackup": {"copperLayers": request.copper_layers, "environment": request.environment},
        "preliminaryRules": {
            "minimumTrackSpaceMm": request.minimum_track_space_mm,
            "minimumViaDrillMm": request.minimum_via_drill_mm,
            "edgeClearanceMm": request.edge_clearance_mm,
        },
        "placements": [item.model_dump() for item in request.placements],
        "findings": findings,
    }


@router.post("/validation/evaluate")
def validation_evaluate(request: ValidationRequest) -> dict[str, object]:
    findings: list[dict[str, object]] = []
    result_map: dict[str, TestResult] = {}
    for result in request.results:
        if result.id in result_map:
            findings.append({"severity": "error", "code": "duplicate-result-id", "id": result.id})
        result_map[result.id] = result
    evaluations: list[dict[str, object]] = []
    for test in request.tests:
        if test.minimum > test.maximum:
            findings.append({"severity": "error", "code": "invalid-limits", "id": test.id})
            evaluations.append({**test.model_dump(), "measuredValue": None, "status": "INVALID"})
            continue
        result = result_map.get(test.id)
        if result is None:
            findings.append({"severity": "error", "code": "missing-result", "id": test.id})
            evaluations.append({**test.model_dump(), "measuredValue": None, "status": "NOT RUN"})
            continue
        passed = test.minimum <= result.value <= test.maximum
        if not passed:
            findings.append({"severity": "error", "code": "acceptance-failure", "id": test.id, "value": result.value})
        if not result.evidence:
            findings.append({"severity": "warning", "code": "missing-evidence", "id": test.id})
        evaluations.append({**test.model_dump(), "measuredValue": result.value, "status": "PASS" if passed else "FAIL", "note": result.note, "evidence": result.evidence})
    test_ids = {test.id for test in request.tests}
    for result in request.results:
        if result.id not in test_ids:
            findings.append({"severity": "warning", "code": "orphan-result", "id": result.id})
    passed_count = sum(item["status"] == "PASS" for item in evaluations)
    failed_count = sum(item["status"] == "FAIL" for item in evaluations)
    return {
        "ok": failed_count == 0 and passed_count == len(evaluations),
        "schema": "sc-workbench-hardware-validation-dossier/1.0",
        "version": VERSION,
        "generatedAt": utc_now(),
        "device": {"id": request.device_id, "revision": request.revision, "stage": request.stage},
        "summary": {
            "tests": len(evaluations),
            "pass": passed_count,
            "fail": failed_count,
            "notRun": len(evaluations) - passed_count - failed_count,
            "disposition": "PASS" if failed_count == 0 and passed_count == len(evaluations) else "REVIEW",
        },
        "evaluations": evaluations,
        "findings": findings,
        "signoff": {"preparedBy": None, "reviewedBy": None, "approvedBy": None, "date": None},
    }
