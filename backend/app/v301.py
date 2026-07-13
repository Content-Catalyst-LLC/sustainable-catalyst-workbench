"""Workbench v3.0.1 production activation and interface reliability routes."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

VERSION = "3.0.1"
SCHEMA = "sc-workbench-production-activation/1.0"
EXPECTED_STUDIOS = (
    "unified",
    "research",
    "embedded",
    "electronics",
    "robotics",
    "instrumentation",
    "simulation",
    "runtime",
    "visualization",
    "experiments",
    "documentation",
    "recovery",
)

router = APIRouter(prefix="/v301", tags=["workbench-v301"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class StudioProbe(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    shortcode: str = Field(default="", max_length=160)
    registered: bool = False
    rendered: bool = False
    assets_loaded: bool = False
    mount_count: int = Field(default=0, ge=0, le=1000)
    state: Literal["ready", "loading", "empty", "offline", "error", "unavailable"] = "unavailable"
    error: str = Field(default="", max_length=2000)


class ActivationAuditRequest(BaseModel):
    primary_shortcode_registered: bool = False
    router_loaded: bool = False
    page_builder: Literal["gutenberg", "elementor", "classic", "unknown"] = "unknown"
    viewport_width: int = Field(default=1440, ge=240, le=10000)
    studios: list[StudioProbe] = Field(default_factory=list, max_length=100)


class RegistryValidationRequest(BaseModel):
    expected_keys: list[str] = Field(default_factory=lambda: list(EXPECTED_STUDIOS), max_length=100)
    registered_keys: list[str] = Field(default_factory=list, max_length=100)
    registered_shortcodes: list[str] = Field(default_factory=list, max_length=500)


class InterfaceEvent(BaseModel):
    studio: str = Field(min_length=1, max_length=100)
    event: Literal["activate", "render", "resize", "error", "recover"]
    success: bool = True
    duration_ms: float = Field(default=0.0, ge=0.0, le=600_000.0)
    detail: str = Field(default="", max_length=2000)


class InterfaceRunRequest(BaseModel):
    events: list[InterfaceEvent] = Field(default_factory=list, max_length=10000)


def audit_activation(request: ActivationAuditRequest) -> dict[str, Any]:
    by_key = {probe.key: probe for probe in request.studios}
    missing = [key for key in EXPECTED_STUDIOS if key not in by_key or not by_key[key].registered]
    unrendered = [
        key for key in EXPECTED_STUDIOS
        if key in by_key and by_key[key].registered and not by_key[key].rendered
    ]
    missing_assets = [
        key for key in EXPECTED_STUDIOS
        if key in by_key and by_key[key].registered and not by_key[key].assets_loaded
    ]
    empty = [key for key, probe in by_key.items() if probe.state == "empty" or probe.mount_count == 0]
    offline = [key for key, probe in by_key.items() if probe.state == "offline"]
    errors = [key for key, probe in by_key.items() if probe.state == "error" or bool(probe.error.strip())]
    duplicate_keys = sorted(key for key, count in Counter(probe.key for probe in request.studios).items() if count > 1)

    penalties = (
        (0 if request.primary_shortcode_registered else 25)
        + (0 if request.router_loaded else 20)
        + len(missing) * 5
        + len(unrendered) * 4
        + len(missing_assets) * 3
        + len(errors) * 4
        + len(empty) * 2
        + len(duplicate_keys) * 3
    )
    score = max(0.0, min(100.0, 100.0 - penalties))
    mobile = request.viewport_width < 861
    warnings: list[str] = []
    if request.page_builder == "unknown":
        warnings.append("Page-builder context was not identified")
    if mobile:
        warnings.append("Mobile horizontal studio navigation must remain keyboard and touch accessible")
    if offline:
        warnings.append("One or more studios reported an offline backend or local runner")

    return {
        "ok": score >= 95 and not missing and not unrendered and not errors,
        "schema": SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "score": round(score, 2),
        "pageBuilder": request.page_builder,
        "viewport": {"width": request.viewport_width, "mobileLayout": mobile},
        "expectedStudioCount": len(EXPECTED_STUDIOS),
        "reportedStudioCount": len(request.studios),
        "primaryShortcodeRegistered": request.primary_shortcode_registered,
        "routerLoaded": request.router_loaded,
        "missingStudios": missing,
        "unrenderedStudios": unrendered,
        "studiosMissingAssets": missing_assets,
        "emptyStudios": sorted(set(empty)),
        "offlineStudios": sorted(set(offline)),
        "errorStudios": sorted(set(errors)),
        "duplicateStudioKeys": duplicate_keys,
        "warnings": warnings,
    }


@router.get("/status")
def status() -> dict[str, Any]:
    return {
        "ok": True,
        "schema": SCHEMA,
        "version": VERSION,
        "generatedAt": _now(),
        "expectedStudios": list(EXPECTED_STUDIOS),
        "expectedStudioCount": len(EXPECTED_STUDIOS),
    }


@router.post("/activation/audit")
def activation_audit(request: ActivationAuditRequest) -> dict[str, Any]:
    return audit_activation(request)


@router.post("/registry/validate")
def validate_registry(request: RegistryValidationRequest) -> dict[str, Any]:
    expected = list(dict.fromkeys(request.expected_keys or list(EXPECTED_STUDIOS)))
    registered = list(dict.fromkeys(request.registered_keys))
    missing = sorted(set(expected) - set(registered))
    unexpected = sorted(set(registered) - set(expected))
    duplicate_shortcodes = sorted(
        key for key, count in Counter(request.registered_shortcodes).items() if count > 1
    )
    return {
        "ok": not missing and not duplicate_shortcodes,
        "schema": "sc-workbench-studio-registry-validation/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "expectedCount": len(expected),
        "registeredCount": len(registered),
        "missingKeys": missing,
        "unexpectedKeys": unexpected,
        "duplicateShortcodes": duplicate_shortcodes,
    }


@router.post("/interface/run-audit")
def audit_interface_run(request: InterfaceRunRequest) -> dict[str, Any]:
    failures = [event.model_dump() for event in request.events if not event.success or event.event == "error"]
    activated = sorted({event.studio for event in request.events if event.event == "activate" and event.success})
    rendered = sorted({event.studio for event in request.events if event.event == "render" and event.success})
    missing_activation = sorted(set(EXPECTED_STUDIOS) - set(activated))
    missing_render = sorted(set(EXPECTED_STUDIOS) - set(rendered))
    durations = [event.duration_ms for event in request.events if event.duration_ms > 0]
    return {
        "ok": not failures and not missing_activation and not missing_render,
        "schema": "sc-workbench-interface-run-audit/1.0",
        "version": VERSION,
        "generatedAt": _now(),
        "eventCount": len(request.events),
        "activatedStudios": activated,
        "renderedStudios": rendered,
        "missingActivation": missing_activation,
        "missingRender": missing_render,
        "failures": failures,
        "maximumDurationMs": max(durations) if durations else 0.0,
    }
