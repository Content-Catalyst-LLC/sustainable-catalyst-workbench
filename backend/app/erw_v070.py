"""ERW 0.7 — static reproducible equations, spatial specifications and flow diagrams.

No geocoding, observed site coordinates, raster requests, or verified CDR.
"""
from __future__ import annotations
from decimal import Decimal
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
from .release import APP_VERSION
from .v510 import content_hash
from .v1220 import _owner,get_project,save_calculation,SavedCalculationCreateRequest
from .erw_v010 import PROJECT_KEY
from .erw_v060 import number

router=APIRouter(tags=["erw-0.7.0"])

class Location(BaseModel):
    locationId: str=Field(min_length=1,max_length=80,pattern=r"^[a-zA-Z0-9_-]+$")
    label: str=Field(min_length=1,max_length=160)
    latitude: str
    longitude: str
    coordinateSource: str=Field(min_length=1,max_length=600)
    evidenceClass: str=Field(pattern=r"^(hypothetical|literature-derived|measured)$")
    limitations: str=Field(min_length=1,max_length=600)

class DiagramRequest(BaseModel):
    researchId: str=PROJECT_KEY
    visualization: dict[str,Any]
    locations: list[Location]=Field(min_length=1,max_length=20)
    sourceReference: str=Field(min_length=1,max_length=1200)

class SaveDiagramRequest(DiagramRequest):
    projectId: str=Field(min_length=1,max_length=100)

def assemble(req:DiagramRequest):
    v=req.visualization
    if req.researchId!=PROJECT_KEY or v.get("researchId")!=PROJECT_KEY or v.get("schema")!="sc.erw.visual-research-package.v0.6.0":
        raise HTTPException(422,detail="ERW 0.6 visual research object required")
    if not isinstance(v.get("calculationObjectHash"),str) or len(v["calculationObjectHash"])<16:
        raise HTTPException(422,detail="Missing source visual hash")
    views=v.get("views")
    if not isinstance(views,list) or [x.get("id") for x in views]!=[
       "scenario-trajectories","lifecycle-breakdown","uncertainty-intervals",
       "sensitivity-ranking","mrv-evidence-matrix"]:
        raise HTTPException(422,detail="Expected all five source visualization views")
    if v.get("verifiedCDR") is not False or v.get("netDurableAtmosphericRemoval") is not None:
        raise HTTPException(422,detail="Incompatible scientific status")
    points=[]; seen=set()
    for loc in req.locations:
        if loc.locationId in seen:raise HTTPException(422,detail="Duplicate location ID")
        seen.add(loc.locationId)
        lat=number(loc.latitude,"latitude");lon=number(loc.longitude,"longitude")
        if abs(lat)>90 or abs(lon)>180:raise HTTPException(422,detail="Invalid geographic coordinates")
        points.append({"id":loc.locationId,"label":loc.label,
          "lat":str(lat),"lon":str(lon),"coordinateSource":loc.coordinateSource,
          "evidenceClass":loc.evidenceClass,"limitations":loc.limitations})
    # Maps are user-coordinate plotting specs, never assertions about where treatment occurred.
    flow=[
     {"id":"feedstock","label":"Feedstock mass","type":"input"},
     {"id":"theoretical","label":"Theoretical geochemical capacity","type":"model"},
     {"id":"proxy","label":"Illustrative realized-potential proxy","type":"model"},
     {"id":"lifecycle","label":"Modeled lifecycle burden","type":"inventory"},
     {"id":"screen","label":"Exploratory proxy minus burden","type":"screening"},
     {"id":"mrv","label":"MRV evidence limitations","type":"evidence"},
    ]
    edges=[
      {"from":"feedstock","to":"theoretical","relation":"stoichiometric potential"},
      {"from":"theoretical","to":"proxy","relation":"user-assumed realization fraction"},
      {"from":"proxy","to":"screen","relation":"screening input"},
      {"from":"lifecycle","to":"screen","relation":"modeled burden"},
      {"from":"mrv","to":"screen","relation":"evidence qualification"},
    ]
    equations=[
       {"id":"capacity","latex":r"C_{gross}=M_{rock}f_{CO_2}","label":"Theoretical capacity",
        "variables":{"M_rock":"feedstock mass, t","f_CO2":"theoretical capacity, tCO2/t"}},
       {"id":"proxy","latex":r"P_{model}=C_{gross}r","label":"Illustrative realization proxy",
        "variables":{"r":"user-specified modeled realization fraction, dimensionless"}},
       {"id":"burden","latex":r"E_{LCA}=\\sum_i Q_i EF_i/1000","label":"Lifecycle emissions (tCO2e)",
        "variables":{"Q_i":"activity quantity","EF_i":"kgCO2e per activity unit"}},
       {"id":"difference","latex":r"D_{screen}=P_{model}-E_{LCA}",
        "label":"Exploratory comparison, NOT net atmospheric CDR","variables":{}},
    ]
    output={"schema":"sc.erw.equations-maps-diagrams.v0.7.0",
       "researchId":PROJECT_KEY,"workbenchVersion":APP_VERSION,
       "sourceVisualHash":v["calculationObjectHash"],
       "equations":equations,
       "map":{"kind":"static-point-spec","crs":"EPSG:4326",
          "siteLocationsVerified":False,"points":points,
          "caution":"Input coordinates are user-supplied illustrative markers, not verified treatment sites."},
       "materialFlow":{"kind":"directed-acyclic-graph","nodes":flow,"edges":edges,
          "noCertifiedRemovalFlow":True},
       "annotation":{"sourceReference":req.sourceReference,
         "rendering":"client-renderer-neutral","dataStatus":"hypothetical-or-input-dependent",
         "noIndependentGeocoding":True,"sourceHashVerifiedAgainstStorage":False},
       "verifiedCDR":False,"verifiedAdditionality":False,"verifiedPermanence":False,
       "netDurableAtmosphericRemoval":None,
       "scientificLimit":"Equation and map/diagram specifications are explanatory representations; they do not verify physical weathering, permanence, causal additionality, observed locations, or net atmospheric removal."}
    output["calculationObjectHash"]=content_hash(output)
    return output

@router.get("/erw/v0.7.0/status")
def status():return {"ok":True,"extension":"erw","extensionVersion":"0.7.0","workbenchVersion":APP_VERSION,"verifiedCDR":False}

@router.post("/erw/v0.7.0/diagrams")
def diagrams(req:DiagramRequest):return {"ok":True,"diagrams":assemble(req)}

@router.post("/erw/v0.7.0/projects/diagrams")
def save_diagrams(req:SaveDiagramRequest,authorization:Optional[str]=Header(default=None)):
    owner,_=_owner(authorization)
    project=get_project(req.projectId,owner)
    if project.get("metadata",{}).get("researchId")!=PROJECT_KEY:raise HTTPException(422,detail="Not ERW project")
    obj=assemble(DiagramRequest(**req.model_dump(exclude={"projectId"})))
    saved=save_calculation(SavedCalculationCreateRequest(
       projectId=req.projectId,title="ERW 0.7 equations maps and scientific diagrams",
       calculationObject=obj,tags=["erw","equations","map-spec","diagram","not-verified-cdr"],
       metadata={"researchId":PROJECT_KEY,"scientificStatus":"exploratory-only"}),owner)
    return {"ok":True,"diagrams":obj,"saved":saved}
