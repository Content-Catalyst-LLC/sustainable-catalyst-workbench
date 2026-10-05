"""Workbench v13.2.0 — Calculator Experience & Result Presentation."""
from __future__ import annotations
from typing import Any, Dict, Optional
from fastapi import APIRouter
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v1310 import hardening_readiness

VERSION = APP_VERSION
router = APIRouter(tags=["workbench-v1320-calculator-experience-result-presentation"])

class CalculationPresentationRequest(BaseModel):
    calculationObject: Dict[str, Any]
    title: str = Field(default="Calculation", max_length=240)
    saved: bool = False
    savedCalculationId: Optional[str] = Field(default=None, max_length=160)

def _hash(x): return content_hash(x)

def _stringify(v):
    if v is None: return "—"
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)

    if isinstance(v, str):
        text = v.strip()

        # Presentation-only numeric normalization.
        # Preserve symbolic/algebraic strings exactly as supplied.
        import re
        from decimal import Decimal, InvalidOperation

        if re.fullmatch(
            r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?",
            text,
        ):
            try:
                number = Decimal(text)

                if number == number.to_integral():
                    return format(number.quantize(Decimal("1")), "f")

                rendered = format(number, "f")
                return rendered.rstrip("0").rstrip(".")

            except InvalidOperation:
                pass

        return v
    if isinstance(v, list): return ", ".join(_stringify(x) for x in v)
    if isinstance(v, dict):
        for k in ("display","text","exact","symbolic","value","float"):
            if k in v and v[k] is not None: return _stringify(v[k])
        import json
        return json.dumps(v, sort_keys=True, ensure_ascii=False)
    return str(v)

def calculation_presentation(req):
    obj=req.calculationObject
    result=obj.get("result") or {}
    inp=obj.get("input") or {}
    plan=obj.get("executionPlan") or {}
    verification=obj.get("verification") or {}
    provenance=obj.get("provenance") or {}
    reproducibility=obj.get("reproducibility") or {}
    checks=verification.get("checks") or {}
    failed=[k for k,v in checks.items() if v is False]
    warnings=[]
    diagnostics=result.get("diagnostics")
    if isinstance(diagnostics,dict):
        for k,v in diagnostics.items():
            if k.lower() in {"warning","warnings","message"} and v:
                warnings.append(_stringify(v))
    if failed:
        warnings.append("Verification checks requiring attention: " + ", ".join(failed))
    body={
        "schema":"sc-workbench-calculation-presentation/1.0",
        "version":VERSION,
        "title":req.title,
        "operation":result.get("operation") or inp.get("operation") or "calculation",
        "primaryResult":{"display":_stringify(result.get("value")),"raw":result.get("value"),"resultType":inp.get("requestedResultType") or "auto"},
        "execution":{"runtime":plan.get("selectedRuntime") or provenance.get("runtime") or "unknown","engine":result.get("engine") or plan.get("selectedEngine") or "unknown","method":result.get("method") or plan.get("methodFamily") or "unknown","precision":result.get("precision") or obj.get("precision")},
        "verification":{"status":verification.get("status") or ("verified" if checks and not failed else "not-reported"),"requested":verification.get("requested"),"passed":len(failed)==0 if checks else None,"failedChecks":failed,"checks":checks},
        "provenance":{"canonicalBackend":provenance.get("canonicalBackend") or "FastAPI","workbenchVersion":provenance.get("workbenchVersion") or VERSION,"inputHash":provenance.get("inputHash"),"executionPlanHash":provenance.get("executionPlanHash"),"resultHash":provenance.get("resultHash"),"provenanceHash":provenance.get("provenanceHash")},
        "reproducibility":{"calculationObjectHash":obj.get("calculationObjectHash"),"deterministicInputHash":reproducibility.get("deterministicInputHash"),"executionPlanHash":reproducibility.get("executionPlanHash"),"resultHash":reproducibility.get("resultHash")},
        "saveState":{"saved":req.saved,"savedCalculationId":req.savedCalculationId},
        "warnings":warnings,
        "technical":{"calculationObject":obj},
        "wordpressRequired":False,
    }
    body["presentationHash"]=_hash({k:v for k,v in body.items() if k not in {"presentationHash","technical"}})
    return body

def experience_contract():
    body={
        "schema":"sc-workbench-calculator-experience-contract/1.0",
        "version":VERSION,
        "canonicalComputationAuthority":"FastAPI",
        "presentationAuthority":"v13.2 presentation adapter",
        "wordpressRequired":False,
        "features":{
            "primaryAnswer":True,"operationAwareFields":True,"methodRuntimeSummary":True,
            "verificationSummary":True,"provenanceSummary":True,"saveState":True,
            "graphHandoff":True,"expandableTechnicalDetail":True,"keyboardExecute":True,
            "recentExpressionMemory":True,
        },
    }
    body["contractHash"]=_hash(body)
    return body

def status():
    h=hardening_readiness()
    c=experience_contract()
    checks={
        "v13HardeningReady":h["hardeningReady"] is True,
        "canonicalBackendPreserved":c["canonicalComputationAuthority"]=="FastAPI",
        "presentationContractReady":all(c["features"].values()),
        "wordpressRequiredFalse":c["wordpressRequired"] is False,
    }
    return {"ok":all(checks.values()),"schema":"sc-workbench-calculator-experience-result-presentation-status/1.0","version":VERSION,"release":"Calculator Experience & Result Presentation","product":PRODUCT_KEY,"name":PRODUCT_NAME,"runtime":RUNTIME_KIND,"wordpressRequired":False,"experienceReady":all(checks.values()),"checks":checks,"contractHash":c["contractHash"]}

@router.get("/v1320/status")
def status_route(): return status()

@router.get("/standalone/v1/calculator/experience-contract")
def experience_contract_route(): return {"ok":True,"version":VERSION,"experience":experience_contract()}

@router.post("/standalone/v1/calculator/presentation")
def calculation_presentation_route(req:CalculationPresentationRequest):
    return {"ok":True,"version":VERSION,"presentation":calculation_presentation(req)}
