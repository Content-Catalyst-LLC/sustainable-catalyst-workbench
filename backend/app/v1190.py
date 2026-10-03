"""Workbench v11.9.0 — Arbitrary Precision & Interval Arithmetic."""
from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional
from threading import Lock
import mpmath as mp
from fastapi import APIRouter
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION=APP_VERSION
STATUS_SCHEMA="sc-workbench-arbitrary-precision-interval-status/1.0"
RESULT_SCHEMA="sc-workbench-arbitrary-precision-interval-result/1.0"
router=APIRouter(tags=["workbench-v1190-arbitrary-precision-interval"])
_IV_LOCK=Lock()

class IntervalSpec(BaseModel):
    lower: str
    upper: str

class PrecisionIntervalRequest(BaseModel):
    operation: Literal[
        "evaluate","constant","interval-create","interval-add","interval-subtract",
        "interval-multiply","interval-divide","interval-power","interval-sqrt",
        "interval-function","interval-width","interval-midpoint","interval-contains",
        "interval-intersect","interval-hull"
    ]
    expression: Optional[str]=Field(default=None,max_length=20000)
    constant: Optional[Literal["pi","e","phi","catalan","euler"]]=None
    precisionDigits: int=Field(default=50,ge=15,le=5000)
    interval: Optional[IntervalSpec]=None
    intervalB: Optional[IntervalSpec]=None
    exponent: Optional[int]=Field(default=None,ge=-1000,le=1000)
    function: Optional[Literal["sin","cos","tan","exp","log","sqrt"]]=None
    value: Optional[str]=None

class PrecisionCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    precisionArithmetic: PrecisionIntervalRequest

def _hash(x): return content_hash(x)

def _safe_eval(expr:str,dps:int):
    with mp.workdps(dps):
        env={"pi":mp.pi,"e":mp.e,"sqrt":mp.sqrt,"sin":mp.sin,"cos":mp.cos,"tan":mp.tan,
             "exp":mp.exp,"log":mp.log,"gamma":mp.gamma,"zeta":mp.zeta,"power":mp.power}
        value=eval(expr,{"__builtins__":{}},env)
        return mp.nstr(value,n=dps)

def _iv(spec:IntervalSpec):
    return mp.iv.mpf([spec.lower,spec.upper])

def _iv_payload(x,dps:int):
    s=str(x)
    # mpmath interval str is canonical and outward-rounded.
    return {"interval":s,"width":str(x.delta),"midpoint":str(x.mid),"precisionDigits":dps}

def execute_precision(req:PrecisionIntervalRequest)->Dict[str,Any]:
    details={}; verification={}
    op=req.operation
    if op=="evaluate":
        if not req.expression: raise ValueError("evaluate requires expression")
        result={"value":_safe_eval(req.expression,req.precisionDigits)}
    elif op=="constant":
        if not req.constant: raise ValueError("constant requires constant")
        with mp.workdps(req.precisionDigits):
            vals={"pi":mp.pi,"e":mp.e,"phi":mp.phi,"catalan":mp.catalan,"euler":mp.euler}
            result={"value":mp.nstr(vals[req.constant],n=req.precisionDigits)}
    else:
        if req.interval is None: raise ValueError(f"{op} requires interval")
        with _IV_LOCK:
            old=mp.iv.dps; mp.iv.dps=req.precisionDigits
            try:
                a=_iv(req.interval)
                if op=="interval-create": x=a
                elif op=="interval-add": x=a+_iv(req.intervalB)
                elif op=="interval-subtract": x=a-_iv(req.intervalB)
                elif op=="interval-multiply": x=a*_iv(req.intervalB)
                elif op=="interval-divide": x=a/_iv(req.intervalB)
                elif op=="interval-power":
                    if req.exponent is None: raise ValueError("interval-power requires exponent")
                    x=a**req.exponent
                elif op=="interval-sqrt": x=mp.iv.sqrt(a)
                elif op=="interval-function":
                    if not req.function: raise ValueError("interval-function requires function")
                    x=getattr(mp.iv,req.function)(a)
                elif op=="interval-width":
                    result={"width":str(a.delta)}; x=None
                elif op=="interval-midpoint":
                    result={"midpoint":str(a.mid)}; x=None
                elif op=="interval-contains":
                    if req.value is None: raise ValueError("interval-contains requires value")
                    v=mp.iv.mpf(req.value); result=bool(v in a); x=None
                elif op=="interval-intersect":
                    b=_iv(req.intervalB); lo=max(a.a,b.a); hi=min(a.b,b.b)
                    result=None if lo>hi else _iv_payload(mp.iv.mpf([lo,hi]),req.precisionDigits); x=None
                elif op=="interval-hull":
                    b=_iv(req.intervalB); x=mp.iv.mpf([min(a.a,b.a),max(a.b,b.b)])
                else: raise ValueError(f"Unsupported operation: {op}")
                if x is not None: result=_iv_payload(x,req.precisionDigits)
            finally:
                mp.iv.dps=old
    body={"ok":True,"schema":RESULT_SCHEMA,"version":VERSION,"operation":op,
          "engine":"mpmath","runtime":"python","precisionDigits":req.precisionDigits,
          "result":result,"details":details,"verification":verification,"wordpressRequired":False}
    body["resultHash"]=_hash({k:v for k,v in body.items() if k not in {"ok","resultHash"}})
    return body

def calculation_object_extension(req,prec):
    obj=build_calculation_object(req); r=execute_precision(prec)
    obj["extensions"]=dict(obj.get("extensions") or {})
    obj["extensions"]["precisionArithmetic"]=r
    obj["result"]["precisionArithmetic"]=r["result"]
    obj["executionPlan"]["precisionArithmetic"]={"runtime":"python","engine":"mpmath",
        "operation":prec.operation,"precisionDigits":prec.precisionDigits}
    obj["verification"]["precisionArithmetic"]=r["verification"]
    obj["provenance"]["precisionArithmeticResultHash"]=r["resultHash"]
    obj["provenance"]["precisionDigits"]=prec.precisionDigits
    obj["calculationObjectHash"]=_hash({k:v for k,v in obj.items() if k not in {"ok","calculationObjectHash"}})
    return obj

def status():
    return {"ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
        "release":"Arbitrary Precision & Interval Arithmetic","product":PRODUCT_KEY,
        "runtime":RUNTIME_KIND,"engine":"mpmath","wordpressRequired":False,
        "capabilities":{"arbitraryPrecisionEvaluation":True,"highPrecisionConstants":True,
        "intervalArithmetic":True,"intervalFunctions":True,"containmentChecks":True,
        "intervalIntersection":True,"intervalHull":True,"calculationObjectExtension":True}}

@router.get("/v1190/status")
def status_route(): return status()
@router.post("/calculation-engine/v1/precision")
def precision_route(req:PrecisionIntervalRequest): return execute_precision(req)
@router.post("/calculation-engine/v1/precision/calculation-object")
def precision_calc_route(req:PrecisionCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest,req.precisionArithmetic)
