"""ERW 0.1.0 — reproducible project bootstrap and feedstock-mass arithmetic.

Reuses the v12 persistent project/calculation service and session authority.
No geochemical carbon removal is calculated in this release.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import (
    ProjectCreateRequest, SavedCalculationCreateRequest,
    _owner, create_project, get_project, save_calculation, list_calculations,
)

router = APIRouter(tags=["erw-0.1.0"])
SCHEMA = "sc.erw.research-project.v0.1.0"
PROJECT_KEY = "SC-ERW-IRELAND-001"
SOURCES = [
    {"doi": "10.1073/pnas.2319436121", "role": "basalt-field-evidence", "kind": "peer-reviewed"},
    {"doi": "10.3389/fclim.2024.1345224", "role": "mrv-methods", "kind": "peer-reviewed"},
    {"doi": "10.3389/fclim.2025.1657058", "role": "basalt-nondetection", "kind": "peer-reviewed"},
    {"doi": "10.1016/j.epsl.2025.119662", "role": "bicarbonate-hydrology", "kind": "peer-reviewed"},
    {"doi": "10.1016/j.apgeochem.2024.106056", "role": "irish-concrete-comparator", "kind": "peer-reviewed"},
]

def template():
    return {
        "schema": SCHEMA,
        "researchId": PROJECT_KEY,
        "title": "Wexford Enhanced Rock Weathering — Carbon Removal Assessment",
        "researchQuestion": "To what extent could basalt application to agricultural mineral soils in County Wexford provide additional, measurable, and durable atmospheric CO2 removal?",
        "studyArea": {"county": "Wexford", "country": "Ireland",
                      "siteStatus": "hypothetical", "areaHa": "100"},
        "pretreatmentYears": 1, "assessmentYears": 10,
        "applicationRatesTonnesPerHa": ["0", "10", "20"],
        "evidenceClass": "hypothetical-design",
        "sources": SOURCES,
        "claimsPolicy": "Feedstock mass is not atmospheric CO2 removal. No field observations or verified removal are implied.",
        "coreContracts": {"executionAuthority": "workbench", "persistenceAuthority": "workbench-v1220",
                          "evidenceAuthority": "source-records", "truthPromotion": False},
    }

class ProjectBootstrap(BaseModel):
    confirmHypothetical: bool = False

class MassRequest(BaseModel):
    projectId: str = Field(min_length=1, max_length=100)
    areaHa: str = "100"
    doseTonnesPerHa: str = "20"

def finite_nonnegative(value: str, label: str) -> Decimal:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise HTTPException(status_code=422, detail=f"{label}: invalid decimal")
    if not number.is_finite() or number < 0 or number > Decimal("1000000000"):
        raise HTTPException(status_code=422, detail=f"{label}: out of range")
    return number

def mass_object(area: str, dose: str):
    a = finite_nonnegative(area, "areaHa")
    d = finite_nonnegative(dose, "doseTonnesPerHa")
    result = a * d
    payload = {
        "schema": "sc.erw.mass-calculation.v0.1.0",
        "calculationId": "ERW-0.1.0-MASS-001",
        "operation": "multiply",
        "equation": "M_basalt = area_ha * dose_tonnes_per_ha",
        "inputs": [
            {"name": "area", "value": str(a), "unit": "ha", "evidenceClass": "hypothetical"},
            {"name": "dose", "value": str(d), "unit": "t/ha", "evidenceClass": "hypothetical"},
        ],
        "result": {"value": str(result), "unit": "t basalt",
                   "evidenceClass": "derived-from-hypothetical-inputs"},
        "researchId": PROJECT_KEY,
        "scientificLimit": "Rock mass only; this is not an estimate of CO2 capture or durable removal.",
        "sourceRequirements": [],
    }
    payload["calculationObjectHash"] = content_hash(payload)
    return payload

@router.get("/erw/v0.1.0/status")
def status():
    return {"ok": True, "extension": "erw", "extensionVersion": "0.1.0",
            "workbenchVersion": APP_VERSION, "persistence": "existing-v1220",
            "carbonRemovalCalculated": False}

@router.get("/erw/v0.1.0/template")
def get_template():
    return {"ok": True, "template": template()}

@router.post("/erw/v0.1.0/projects")
def create_research_project(req: ProjectBootstrap, authorization: Optional[str] = Header(default=None)):
    if not req.confirmHypothetical:
        raise HTTPException(status_code=422, detail="Explicitly confirm that the Wexford site is hypothetical")
    owner, _ = _owner(authorization)
    t = template()
    project = create_project(ProjectCreateRequest(
        name=t["title"], description=t["researchQuestion"],
        metadata={"researchId": PROJECT_KEY, "domain": "enhanced-rock-weathering",
                  "researchTemplate": t, "evidenceClass": "hypothetical-design"}), owner)
    return {"ok": True, "project": project, "researchTemplate": t}

@router.post("/erw/v0.1.0/calculations/mass")
def calculate_and_save(req: MassRequest, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    project = get_project(req.projectId, owner)
    if project.get("metadata", {}).get("researchId") != PROJECT_KEY:
        raise HTTPException(status_code=422, detail="Project is not the Wexford ERW research template")
    calculation = mass_object(req.areaHa, req.doseTonnesPerHa)
    saved = save_calculation(SavedCalculationCreateRequest(
        projectId=req.projectId, title="ERW feedstock mass (hypothetical)",
        calculationObject=calculation,
        tags=["erw", "hypothetical", "feedstock-mass"],
        metadata={"researchId": PROJECT_KEY, "evidenceClass": "derived-from-hypothetical-inputs"}), owner)
    return {"ok": True, "calculation": calculation, "saved": saved}

@router.get("/erw/v0.1.0/projects/{project_id}/package")
def export_project_package(project_id: str, authorization: Optional[str] = Header(default=None)):
    owner, _ = _owner(authorization)
    project = get_project(project_id, owner)
    if project.get("metadata", {}).get("researchId") != PROJECT_KEY:
        raise HTTPException(status_code=404, detail="ERW project not found")
    calculations = list_calculations(project_id, owner)
    bundle = {"schema": "sc.erw.research-package.v0.1.0", "extensionVersion": "0.1.0",
              "workbenchVersion": APP_VERSION, "researchId": PROJECT_KEY,
              "project": project, "calculations": calculations,
              "scientificStatus": "hypothetical-inputs-only",
              "verification": {"arithmetic": "deterministic", "atmosphericRemoval": "not-assessed"}}
    bundle["packageHash"] = content_hash(bundle)
    return {"ok": True, "package": bundle}
