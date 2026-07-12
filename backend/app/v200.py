"""Workbench v2.0.0 foundation routes.

These endpoints publish contracts and generate deterministic documentation scaffolds.
They do not execute browser or user-submitted native code. Native execution is confined
to the optional loopback Go runner running on the visitor's own computer.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v2", tags=["workbench-v2-foundation"])


class DocumentationRequest(BaseModel):
    title: str = Field(default="Technical project record", max_length=180)
    revision: str = Field(default="0.1.0", max_length=40)
    purpose: str = Field(default="", max_length=12000)
    methods: str = Field(default="", max_length=20000)
    validation: str = Field(default="", max_length=20000)
    project_id: str = Field(default="default", max_length=120)
    artifacts: list[dict[str, Any]] = Field(default_factory=list, max_length=100)


@router.get("/foundation")
def foundation() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "2.0.0",
        "schema": "sc-workbench-foundation/2.0",
        "release": "Go Runner, Research Lab, and Hardware Studio Foundation",
        "browser_storage_compatible": True,
        "native_execution_location": "optional loopback runner on the visitor device",
        "server_executes_user_code": False,
        "panels": [
            "research-lab-canvas",
            "research-notebook",
            "technical-documentation",
            "hardware-studio",
            "arduino-studio",
            "schematic-generator",
            "bill-of-materials",
            "conceptual-pcb",
            "assembly-translator-foundation",
            "fpga-studio-foundation",
            "local-runner-pairing",
        ],
    }


@router.get("/hardware/manifest")
def hardware_manifest() -> dict[str, Any]:
    return {
        "ok": True,
        "version": "2.0.0",
        "schema": "sc-workbench-hardware-manifest/2.0",
        "boards": [
            {"family": "Arduino", "examples": ["Uno R4", "MKR", "Nano", "Nicla", "Portenta"]},
            {"family": "Raspberry Pi", "examples": ["Pico", "Pico W", "Raspberry Pi SBC"]},
            {"family": "ESP32", "examples": ["Arduino-compatible ESP32 boards"]},
            {"family": "FPGA", "examples": ["iCE40", "ECP5", "vendor-toolchain projects"]},
        ],
        "outputs": ["sketch scaffold", "schematic concept", "BOM", "PCB placement concept", "Verilog scaffold"],
        "manufacturing_ready": False,
        "synthesis_or_timing_proven": False,
        "review_boundary": "Validate components, voltages, pinouts, buses, standards, clearances, timing, thermal behavior, and safety on actual hardware.",
    }


@router.post("/documentation")
def documentation(request: DocumentationRequest) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    markdown = f"""# {request.title}

**Revision:** {request.revision}
**Project:** {request.project_id}
**Generated:** {generated_at}
**Schema:** sc-workbench-technical-document/2.0

## Purpose and scope

{request.purpose or 'Not yet documented.'}

## Methods and architecture

{request.methods or 'Not yet documented.'}

## Validation and limitations

{request.validation or 'Not yet documented.'}

## Connected artifacts

{len(request.artifacts)} artifact record(s) supplied.

## Review boundary

This generated document is a project scaffold. Validate all calculations, code, components, interfaces, standards, operating conditions, and safety claims before implementation.
"""
    return {
        "ok": True,
        "version": "2.0.0",
        "schema": "sc-workbench-technical-document/2.0",
        "generated_at": generated_at,
        "project_id": request.project_id,
        "artifact_count": len(request.artifacts),
        "markdown": markdown,
        "professional_review_required": True,
    }
