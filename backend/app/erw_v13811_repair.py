"""1.3.8.1.1: read-only discovery of ALL saved ERW project calculations.

Never create or silently convert an object; a compatible chart can be projected
in memory from a hash-authenticated saved calculation.
"""
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .erw_v120 import VIS, REPORT, TABLE
from .erw_v1381_source import extract_series, SCHEMA
from .v1220 import list_calculations, get_calculation
from .v510 import content_hash

router=APIRouter(tags=["erw-1.3.8.1.1-repair"])
def eligible(obj):
    if not isinstance(obj,dict):return "invalid-object"
    h=obj.get("calculationObjectHash")
    if not isinstance(h,str) or h!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        return "hash-invalid"
    if obj.get("verifiedCDR") is not False or obj.get("netDurableAtmosphericRemoval") is not None:
        return "unsupported-verification-status"
    try:extract_series(obj)
    except (HTTPException,TypeError,ValueError):return "no-compatible-scenario-series"
    return "chart-ready"

def enumerate_objects(project_id,owner):
    project_for(project_id,owner)
    rows=[]
    for row in list_calculations(project_id,owner):
        obj=row.get("calculationObject")
        if not isinstance(obj,dict):obj={}
        reason=eligible(obj)
        rows.append({"id":row["id"],"title":str(obj.get("title") or row.get("title") or "Saved calculation")[:200],
          "schema":str(obj.get("schema") or "unknown")[:140],
          "hash":obj.get("calculationObjectHash") if isinstance(obj.get("calculationObjectHash"),str) else None,
          "status":reason,"chartReady":reason=="chart-ready",
          "nativeVisualPackage":obj.get("schema")==SCHEMA})
    return rows

@router.get("/erw/v1.3.8.1.1/projects/{project_id}/discover")
def discover(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    rows=enumerate_objects(project_id,owner)
    return {"ok":True,"objects":rows,"total":len(rows),"chartReady":sum(x["chartReady"] for x in rows),
            "excluded":len(rows)-sum(x["chartReady"] for x in rows),
            "readOnly":True,"noEligibleObjects":not any(x["chartReady"] for x in rows)}

@router.get("/erw/v1.3.8.1.1/projects/{project_id}/chart/{calculation_id}")
def chart(project_id:str,calculation_id:str,hash:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    row=get_calculation(calculation_id,owner)
    if row.get("projectId")!=project_id:raise HTTPException(404,detail="Object not in selected project")
    obj=row.get("calculationObject")
    status=eligible(obj)
    if status!="chart-ready":raise HTTPException(422,detail="Cannot chart source: "+status)
    if obj["calculationObjectHash"]!=hash:raise HTTPException(409,detail="Saved object hash changed")
    return {"ok":True,"researchObjectId":calculation_id,"sourceHash":hash,
      "schema":obj.get("schema"),"series":extract_series(obj),
      "unit":"modeled incremental potential proxy (tonnes CO2)",
      "verifiedCDR":False,"netDurableAtmosphericRemoval":None,
      "scientificCaution":"Saved modeled potential proxy only; NOT verified net atmospheric CO2 removal."}

@router.get("/erw/v1.3.8.1.1/status")
def status():
    return {"ok":True,"extensionVersion":"1.3.8.1.1","allProjectObjectsDiscoverable":True,
     "exclusionReasons":True,"compatibleSavedTrajectories":True,"readOnly":True,
     "verifiedCDR":False,"publicationCertified":False}
