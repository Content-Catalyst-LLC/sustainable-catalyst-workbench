"""Workbench v11.5.0 — Julia Scientific Runtime Foundation."""
from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, RUNTIME_KIND
from .v1100 import UnifiedCalculationRequest, build_calculation_object
from .v510 import content_hash

VERSION = APP_VERSION
STATUS_SCHEMA = "sc-workbench-julia-runtime-status/1.0"
EXEC_SCHEMA = "sc-workbench-julia-runtime-execution/1.0"
CONTRACT_SCHEMA = "sc-workbench-julia-runtime-contract/1.0"
router = APIRouter(tags=["workbench-v1150-julia-scientific-runtime"])
RUNNER = Path(__file__).resolve().parents[1] / "julia-runtime" / "runner.jl"

class JuliaExecutionRequest(BaseModel):
    operation: Literal["runtime-info","vector-dot","matrix-multiply","linear-solve","statistics"]
    vectorA: List[float] = Field(default_factory=list, max_length=100000)
    vectorB: List[float] = Field(default_factory=list, max_length=100000)
    matrixA: List[List[float]] = Field(default_factory=list, max_length=5000)
    matrixB: List[List[float]] = Field(default_factory=list, max_length=5000)
    allowPythonFallback: bool = True

class JuliaCalculationObjectRequest(BaseModel):
    calculationObjectRequest: UnifiedCalculationRequest
    julia: JuliaExecutionRequest

def _hash(payload: Dict[str, Any]) -> str:
    return content_hash(payload)

def _julia_binary() -> Optional[str]:
    configured = os.getenv("SCWB_JULIA_BIN", "").strip()
    if configured and Path(configured).exists():
        return configured
    return shutil.which("julia")

def runtime_identity() -> Dict[str, Any]:
    binary = _julia_binary()
    installed = binary is not None
    julia_version = None
    error = None
    if installed:
        try:
            proc = subprocess.run([binary,"--startup-file=no","--version"], check=True,
                                  capture_output=True, text=True, timeout=10)
            julia_version = (proc.stdout or proc.stderr).strip()
        except Exception as exc:
            installed = False
            error = str(exc)
    body = {
        "ok": True, "schema": STATUS_SCHEMA, "version": VERSION, "runtime": "julia",
        "installed": installed, "binary": binary, "juliaVersion": julia_version,
        "runner": str(RUNNER), "runnerPresent": RUNNER.exists(),
        "executionMode": "subprocess-structured-kernel",
        "pythonFallbackAvailable": True, "wordpressRequired": False,
    }
    if error: body["probeError"] = error
    body["runtimeIdentityHash"] = _hash({k:v for k,v in body.items() if k not in {"ok","runtimeIdentityHash"}})
    return body

def runtime_contract() -> Dict[str, Any]:
    body = {
        "ok": True, "schema": CONTRACT_SCHEMA, "version": VERSION, "runtime": "julia",
        "plannerRole": "scientific-execution-target", "orchestrator": "python",
        "transport": "local-subprocess", "arbitraryCodeExecution": False,
        "structuredKernelOnly": True,
        "supportedOperations": ["runtime-info","vector-dot","matrix-multiply","linear-solve","statistics"],
        "fallbackPolicy": {
            "fallbackRuntime": "python",
            "fallbackRequiresRequestPermission": True,
            "fallbackRecordedInProvenance": True,
        },
        "futureScientificTargets": [
            "ode","sde","dae","delay-differential-equations","optimization",
            "ensemble-simulation","sensitivity","parameter-estimation","scientific-ml"
        ],
        "wordpressRequired": False,
    }
    body["contractHash"] = _hash({k:v for k,v in body.items() if k not in {"ok","contractHash"}})
    return body

def _encode_vector(v): return ",".join(format(float(x), ".17g") for x in v)
def _encode_matrix(m): return ";".join(_encode_vector(row) for row in m)
def _parse_vector(text): return [] if text == "" else [float(x) for x in text.split(",")]
def _parse_matrix(text): return [] if text == "" else [_parse_vector(row) for row in text.split(";")]

def _python_fallback(req: JuliaExecutionRequest) -> Dict[str, Any]:
    op = req.operation
    if op == "runtime-info":
        result = {"runtime":"python-fallback"}
    elif op == "vector-dot":
        if len(req.vectorA) != len(req.vectorB): raise ValueError("vector-dot requires equal lengths")
        result = float(np.dot(np.asarray(req.vectorA), np.asarray(req.vectorB)))
    elif op == "matrix-multiply":
        result = (np.asarray(req.matrixA,dtype=float) @ np.asarray(req.matrixB,dtype=float)).tolist()
    elif op == "linear-solve":
        result = np.linalg.solve(np.asarray(req.matrixA,dtype=float), np.asarray(req.vectorA,dtype=float)).tolist()
    elif op == "statistics":
        if not req.vectorA: raise ValueError("statistics requires vectorA")
        arr=np.asarray(req.vectorA,dtype=float)
        result={"mean":float(np.mean(arr)),
                "std":float(np.std(arr,ddof=1)) if len(arr)>1 else 0.0,
                "minimum":float(np.min(arr)),"maximum":float(np.max(arr))}
    else:
        raise ValueError(f"Unsupported Julia operation: {op}")
    return {"result":result,"engine":"numpy","runtime":"python","fallback":True}

def _run_julia(req: JuliaExecutionRequest) -> Dict[str, Any]:
    binary=_julia_binary()
    if not binary or not RUNNER.exists(): raise RuntimeError("Julia runtime unavailable")
    args=[binary,"--startup-file=no","--history-file=no",str(RUNNER),req.operation,
          _encode_vector(req.vectorA),_encode_vector(req.vectorB),
          _encode_matrix(req.matrixA),_encode_matrix(req.matrixB)]
    proc=subprocess.run(args,check=True,capture_output=True,text=True,timeout=30)
    fields={}
    for line in proc.stdout.splitlines():
        if "\t" in line:
            k,v=line.split("\t",1); fields[k]=v
    if fields.get("status")!="ok":
        raise RuntimeError(fields.get("error") or proc.stderr or "Julia execution failed")
    kind=fields.get("resultKind","scalar"); raw=fields.get("result","")
    if kind=="scalar": result=float(raw)
    elif kind=="vector": result=_parse_vector(raw)
    elif kind=="matrix": result=_parse_matrix(raw)
    elif kind=="statistics":
        result={k:float(fields[k]) for k in ["mean","std","minimum","maximum"]}
    elif kind=="runtime-info":
        result={"juliaVersion":fields.get("juliaVersion"),"threads":int(fields.get("threads","1"))}
    else: result=raw
    return {"result":result,"engine":"julia-stdlib","runtime":"julia","fallback":False,
            "juliaVersion":fields.get("juliaVersion"),"threads":int(fields.get("threads","1"))}

def execute_julia(req: JuliaExecutionRequest) -> Dict[str, Any]:
    identity=runtime_identity(); fallback_reason=None
    try:
        executed=_run_julia(req)
    except Exception as exc:
        if not req.allowPythonFallback:
            raise HTTPException(status_code=503, detail=f"Julia runtime unavailable or execution failed: {exc}")
        fallback_reason=str(exc); executed=_python_fallback(req)
    body={
        "ok":True,"schema":EXEC_SCHEMA,"version":VERSION,"operation":req.operation,
        "requestedRuntime":"julia","selectedRuntime":executed["runtime"],
        "engine":executed["engine"],"fallback":executed["fallback"],
        "fallbackReason":fallback_reason,"result":executed["result"],
        "runtimeIdentity":identity,
        "execution":{"juliaVersion":executed.get("juliaVersion"),
                     "threads":executed.get("threads"),
                     "structuredKernel":True,"arbitraryCodeExecution":False},
        "wordpressRequired":False,
    }
    body["executionHash"]=_hash({k:v for k,v in body.items() if k not in {"ok","executionHash"}})
    return body

def calculation_object_extension(req: UnifiedCalculationRequest, julia_req: JuliaExecutionRequest):
    obj=build_calculation_object(req); result=execute_julia(julia_req)
    obj["extensions"]=dict(obj.get("extensions") or {})
    obj["extensions"]["juliaRuntime"]=result
    obj["result"]["juliaRuntime"]=result["result"]
    obj["executionPlan"]["juliaRuntime"]={
        "requestedRuntime":"julia","selectedRuntime":result["selectedRuntime"],
        "engine":result["engine"],"operation":julia_req.operation,"fallback":result["fallback"]}
    obj["verification"]["juliaRuntime"]={
        "runtimeAvailable":result["runtimeIdentity"]["installed"],
        "fallbackUsed":result["fallback"],"structuredKernel":True}
    obj["provenance"]["juliaExecutionHash"]=result["executionHash"]
    obj["provenance"]["juliaRuntimeIdentityHash"]=result["runtimeIdentity"]["runtimeIdentityHash"]
    obj["calculationObjectHash"]=_hash({k:v for k,v in obj.items() if k not in {"ok","calculationObjectHash"}})
    return obj

def status():
    identity=runtime_identity(); contract=runtime_contract()
    return {
        "ok":True,"schema":STATUS_SCHEMA,"version":VERSION,
        "release":"Julia Scientific Runtime Foundation","product":PRODUCT_KEY,
        "runtime":RUNTIME_KIND,"wordpressRequired":False,"julia":identity,
        "contractHash":contract["contractHash"],
        "capabilities":{"juliaExecutionTarget":True,"structuredKernelExecution":True,
                        "runtimeIdentityCapture":True,"versionCapture":True,
                        "fallbackProvenance":True,"vectorDot":True,"matrixMultiply":True,
                        "linearSolve":True,"statistics":True,
                        "calculationObjectExtension":True},
    }

@router.get("/v1150/status")
def status_route(): return status()

@router.get("/calculation-engine/v1/runtimes/julia")
def julia_runtime_route(): return runtime_identity()

@router.get("/calculation-engine/v1/runtimes/julia/contract")
def julia_contract_route(): return runtime_contract()

@router.post("/calculation-engine/v1/runtimes/julia/execute")
def julia_execute_route(req: JuliaExecutionRequest): return execute_julia(req)

@router.post("/calculation-engine/v1/runtimes/julia/calculation-object")
def julia_calculation_object_route(req: JuliaCalculationObjectRequest):
    return calculation_object_extension(req.calculationObjectRequest, req.julia)
