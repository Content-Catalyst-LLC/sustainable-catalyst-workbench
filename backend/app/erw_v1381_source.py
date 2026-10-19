"""ERW 1.3.8.1 — verified-owner source-linked scenario series, read-only."""
from __future__ import annotations
from math import isfinite
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from .erw_v121 import owner_from_auth
from .erw_v120 import SourceRef, valid_source, catalog
from .erw_v110 import project_for

router=APIRouter(tags=["erw-1.3.8.1-source-linked-graphics"])
SCHEMA="sc.erw.visual-research-package.v0.6.0"
def extract_series(obj):
    views=obj.get("views") or []
    view=next((v for v in views if isinstance(v,dict) and v.get("id")=="scenario-trajectories"),None)
    if not view:raise HTTPException(422,detail="Saved object contains no scenario-trajectories view")
    raw=view.get("series")
    if not isinstance(raw,list) or not raw:raise HTTPException(422,detail="Source has no scenario series")
    output=[]
    for s in raw[:16]:
        if not isinstance(s,dict):raise HTTPException(422,detail="Invalid series")
        try:
            dose=float(s["rateTonnesPerHa"])
            if not isfinite(dose) or dose<0:raise ValueError()
            pts=s["points"]
            if not isinstance(pts,list) or not (1<=len(pts)<=300):raise ValueError()
            points=[]
            for p in pts:
                year=float(p["year"]);val=float(p["incrementalPotentialProxyTonnesCO2"])
                if not isfinite(year) or year<0 or not isfinite(val) or val<0:raise ValueError()
                points.append({"year":year,"incrementalPotentialProxyTonnesCO2":val})
            if any(points[i]["year"]>=points[i+1]["year"] for i in range(len(points)-1)):raise ValueError()
        except (TypeError,ValueError,KeyError,OverflowError):
            raise HTTPException(422,detail="Invalid saved scenario data")
        output.append({"rateTonnesPerHa":dose,"points":points})
    return output

@router.get("/erw/v1.3.8.1/projects/{project_id}/sources")
def sources(project_id:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    return {"ok":True,"sources":[x for x in catalog(project_id,owner) if x["schema"]==SCHEMA and x["digestConsistent"]]}

@router.get("/erw/v1.3.8.1/projects/{project_id}/sources/{calculation_id}")
def source_chart(project_id:str,calculation_id:str,hash:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization)
    project_for(project_id,owner)
    obj=valid_source(project_id,owner,SourceRef(calculationId=calculation_id,objectHash=hash),{SCHEMA})
    series=extract_series(obj)
    return {"ok":True,"researchObjectId":calculation_id,"sourceHash":hash,
        "schema":SCHEMA,"chart":"scenario-trajectories","series":series,
        "unit":"modeled incremental potential proxy, tonnes CO2",
        "verifiedCDR":False,"netDurableAtmosphericRemoval":None,
        "scientificCaution":"Saved model output; hypothetical potential proxy, NOT verified net atmospheric CO2 removal."}

@router.get("/erw/v1.3.8.1/status")
def status():return {"ok":True,"extensionVersion":"1.3.8.1","savedSourceLinkedGraphics":True,
"ownerProjectScoped":True,"hashValidated":True,"readOnly":True,
"uncertaintyCalculated":False,"verifiedCDR":False,"publicationCertified":False}
