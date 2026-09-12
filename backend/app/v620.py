"""Workbench v6.2.0 — Energy Workbench Runtime."""
from fastapi import APIRouter
from .energy_workbench_runtime import framework

VERSION = "6.2.0"
router = APIRouter(prefix="/v620", tags=["workbench-v620-energy-runtime"])

@router.get("/status")
def status():
    f = framework()
    return {
        "ok": True,
        "version": VERSION,
        "release": "Energy Workbench Runtime",
        "energySystemsVersion": f["energy_systems_version"],
        "operationCount": len(f["operations"]),
        "explicitInputExecution": True,
        "automaticExecution": False,
        "automaticPersistence": False,
        "automaticRanking": False,
        "automaticRecommendation": False,
    }
