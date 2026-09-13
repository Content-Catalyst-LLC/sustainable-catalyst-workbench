"""Workbench v6.3.0 — Grid, Storage & Reliability Analysis."""
from fastapi import APIRouter
from .energy_workbench_runtime import framework

VERSION = "6.3.0"
router = APIRouter(prefix="/v630", tags=["workbench-v630-grid-storage-reliability"])

@router.get("/status")
def status():
    f=framework()
    grid=[x for x in f["operations"] if x["section"]=="grid_storage_reliability"]
    return {"ok":True,"version":VERSION,"release":"Grid, Storage & Reliability Analysis","energySystemsVersion":f["energy_systems_version"],"gridStorageReliabilityOperations":len(grid),"automaticExecution":False,"automaticPersistence":False,"reliabilityDeclaration":False,"outagePrediction":False}
