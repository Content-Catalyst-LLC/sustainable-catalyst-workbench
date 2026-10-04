"""Workbench v12.3.0 — Standalone Calculator Workspace.

Provides the first complete standalone calculator workflow:
session-authorized calculation execution through the canonical v11 engine,
project-aware save semantics through the v12.2 persistent store, and a
frontend-oriented calculator capability/configuration contract.

No mathematics is duplicated here. v12.3 orchestrates existing canonical
CalculationObject execution and persistence.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v1210 import require_session
from .v1220 import (
    SavedCalculationCreateRequest,
    get_project,
    list_projects,
    save_calculation,
)
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-standalone-calculator-workspace-status/1.0"
CONFIG_SCHEMA = "sc-workbench-standalone-calculator-config/1.0"
EXECUTION_SCHEMA = "sc-workbench-standalone-calculator-execution/1.0"

router = APIRouter(tags=["workbench-v1230-standalone-calculator-workspace"])


class CalculatorWorkspaceExecuteRequest(BaseModel):
    calculationRequest: UnifiedCalculationRequest
    projectId: Optional[str] = Field(default=None, max_length=100)
    saveResult: bool = False
    title: str = Field(default="Calculation", min_length=1, max_length=240)
    tags: List[str] = Field(default_factory=list, max_length=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


def _hash(payload: Any) -> str:
    return content_hash(payload)


def _owner(authorization: Optional[str]) -> tuple[str, Dict[str, Any]]:
    session = require_session(authorization)
    return session["subject"]["id"], session


def calculator_config() -> Dict[str, Any]:
    operations = [
        {
            "id": "evaluate",
            "label": "Evaluate",
            "requires": ["expression"],
            "resultType": "numeric",
            "category": "general",
        },
        {
            "id": "exact",
            "label": "Exact",
            "requires": ["expression"],
            "resultType": "exact",
            "category": "symbolic",
        },
        {
            "id": "simplify",
            "label": "Simplify",
            "requires": ["expression"],
            "resultType": "symbolic",
            "category": "symbolic",
        },
        {
            "id": "solve",
            "label": "Solve",
            "requires": ["expression"],
            "optional": ["variable"],
            "resultType": "symbolic",
            "category": "equations",
        },
        {
            "id": "differentiate",
            "label": "Differentiate",
            "requires": ["expression", "variable"],
            "resultType": "symbolic",
            "category": "calculus",
        },
        {
            "id": "integrate-symbolic",
            "label": "Integrate",
            "requires": ["expression", "variable"],
            "optional": ["domain"],
            "resultType": "symbolic",
            "category": "calculus",
        },
        {
            "id": "root",
            "label": "Find Root",
            "requires": ["expression", "variable"],
            "optional": ["initialGuess", "bracket"],
            "resultType": "numeric",
            "category": "numerical",
        },
        {
            "id": "integrate-numeric",
            "label": "Numerical Integral",
            "requires": ["expression", "variable", "domain"],
            "resultType": "numeric",
            "category": "numerical",
        },
        {
            "id": "optimize-scalar",
            "label": "Optimize",
            "requires": ["expression", "variable"],
            "optional": ["domain"],
            "resultType": "numeric",
            "category": "optimization",
        },
    ]
    body = {
        "schema": CONFIG_SCHEMA,
        "version": VERSION,
        "workspaceMode": "standalone-primary",
        "canonicalExecutionEndpoint": "/calculation-engine/v1/compute",
        "workspaceExecutionEndpoint": "/standalone/v1/calculator/execute",
        "projectStoreEndpoint": "/standalone/v1/projects",
        "savedCalculationEndpoint": "/standalone/v1/calculations",
        "wordpressRequired": False,
        "operations": operations,
        "defaults": {
            "operation": "evaluate",
            "requestedResultType": "auto",
            "preferredRuntime": "auto",
            "requireVerification": True,
            "requireProvenance": True,
            "precisionDigits": 30,
        },
        "capabilities": {
            "executeCalculationObject": True,
            "selectPersistentProject": True,
            "saveCalculationObject": True,
            "displayVerification": True,
            "displayProvenance": True,
            "displayRuntimePlan": True,
            "preserveCalculationObjectHash": True,
        },
    }
    body["configHash"] = _hash(body)
    return body


def execute_workspace(
    req: CalculatorWorkspaceExecuteRequest,
    owner: str,
    session: Dict[str, Any],
) -> Dict[str, Any]:
    if req.saveResult and not req.projectId:
        raise HTTPException(
            status_code=422,
            detail="projectId is required when saveResult=true",
        )

    project = None
    if req.projectId:
        project = get_project(req.projectId, owner)

    calculation_object = build_calculation_object(req.calculationRequest)

    saved = None
    if req.saveResult:
        saved = save_calculation(
            SavedCalculationCreateRequest(
                projectId=req.projectId,
                title=req.title,
                calculationObject=calculation_object,
                tags=req.tags,
                metadata={
                    **req.metadata,
                    "source": "standalone-calculator-workspace",
                    "workbenchVersion": VERSION,
                },
            ),
            owner,
        )

    result = {
        "ok": True,
        "schema": EXECUTION_SCHEMA,
        "version": VERSION,
        "workspaceMode": "standalone-primary",
        "session": {
            "sessionId": session["sessionId"],
            "subjectId": session["subject"]["id"],
            "subjectType": session["subject"]["type"],
        },
        "project": project,
        "calculationObject": calculation_object,
        "savedCalculation": saved,
        "saved": saved is not None,
        "wordpressRequired": False,
    }
    result["workspaceExecutionHash"] = _hash(
        {k: v for k, v in result.items() if k not in {"ok", "workspaceExecutionHash"}}
    )
    return result


def status() -> Dict[str, Any]:
    config = calculator_config()
    return {
        "ok": True,
        "schema": STATUS_SCHEMA,
        "version": VERSION,
        "release": "Standalone Calculator Workspace",
        "product": PRODUCT_KEY,
        "runtime": RUNTIME_KIND,
        "wordpressRequired": False,
        "canonicalCalculationEngine": "v11 Unified Calculation Engine",
        "persistentStore": "v12.2 Persistent Calculation & Project Store",
        "sessionAuthority": "v12.1 FastAPI signed session",
        "configHash": config["configHash"],
        "capabilities": {
            "standaloneCalculatorWorkspace": True,
            "canonicalCalculationObjectExecution": True,
            "projectAwareExecution": True,
            "oneStepExecuteAndSave": True,
            "projectOwnershipEnforced": True,
            "calculationObjectPersistence": True,
            "verificationPresentationContract": True,
            "provenancePresentationContract": True,
            "runtimePlanPresentationContract": True,
            "wordpressComputationNotRequired": True,
        },
    }


@router.get("/v1230/status")
def status_route():
    return status()


@router.get("/standalone/v1/calculator/config")
def calculator_config_route(authorization: Optional[str] = Header(default=None)):
    owner, session = _owner(authorization)
    return {
        "ok": True,
        "version": VERSION,
        "ownerSubject": owner,
        "sessionId": session["sessionId"],
        "calculator": calculator_config(),
        "projects": list_projects(owner),
    }


@router.post("/standalone/v1/calculator/execute")
def calculator_execute_route(
    req: CalculatorWorkspaceExecuteRequest,
    authorization: Optional[str] = Header(default=None),
):
    owner, session = _owner(authorization)
    return execute_workspace(req, owner, session)
