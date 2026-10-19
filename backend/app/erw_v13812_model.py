"""ERW 1.3.8.1.2 — transparent hypothetical scenario model and immutable snapshots.

No field measurements, validated uptake factor or certified carbon removal implied.
"""
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from .erw_v121 import owner_from_auth
from .erw_v110 import project_for
from .erw_v010 import PROJECT_KEY
from .v510 import content_hash
from .v1220 import save_calculation, get_calculation, SavedCalculationCreateRequest
from .erw_v1381_source import extract_series
router=APIRouter(tags=["erw-1.3.8.1.2-scenario-model"])
SCHEMA="sc.erw.visual-research-package.v0.6.0"
class ScenarioParameters(BaseModel):
    areaHa:Decimal=Field(default=Decimal("100"),ge=1,le=100000)
    ratesTonnesPerHa:list[Decimal]=Field(default_factory=lambda:[Decimal("0"),Decimal("10"),Decimal("20")],min_length=2,max_length=8)
    potentialTonnesCO2PerTonneBasalt:Decimal=Field(default=Decimal("0.15"),ge=0,le=1)
    annualRealizationFraction:Decimal=Field(default=Decimal("0.10"),ge=0,le=1)
    annualAttenuationFraction:Decimal=Field(default=Decimal("0.05"),ge=0,le=1)
    years:int=Field(default=10,ge=1,le=30)
    assumptionNote:str=Field(min_length=12,max_length=1200)
    def normalized(self):
        if any(not r.is_finite() or r<0 or r>100 for r in self.ratesTonnesPerHa):
            raise HTTPException(422,detail="Invalid application rate")
        if len(set(self.ratesTonnesPerHa))!=len(self.ratesTonnesPerHa) or Decimal(0) not in self.ratesTonnesPerHa:
            raise HTTPException(422,detail="Unique treatment rates with a zero-dose control are required")
        for x in (self.areaHa,self.potentialTonnesCO2PerTonneBasalt,self.annualRealizationFraction,self.annualAttenuationFraction):
            if not x.is_finite():raise HTTPException(422,detail="Nonfinite model input")
        return self

def calculate(req:ScenarioParameters,project_id:str):
    req.normalized()
    series=[]
    for rate in sorted(req.ratesTonnesPerHa):
        points=[]
        for year in range(1,req.years+1):
            proxy=(req.areaHa*rate*req.potentialTonnesCO2PerTonneBasalt*
                   req.annualRealizationFraction*(Decimal(1)-req.annualAttenuationFraction)**(year-1))
            points.append({"year":year,"baselinePotentialTonnesCO2":"0",
             "scenarioPotentialTonnesCO2":str(proxy),
             "incrementalPotentialProxyTonnesCO2":str(proxy)})
        series.append({"rateTonnesPerHa":str(rate),"points":points})
    obj={"schema":SCHEMA,"researchId":PROJECT_KEY,"projectId":project_id,
       "title":"Wexford researcher-assumed scenario model",
       "views":[{"id":"scenario-trajectories","series":series}],
       "model":{"formula":"annual_proxy = area_ha * applied_tonnes_per_ha * assumed_potential_tCO2_per_tbasalt * assumed_annual_realization_fraction * (1 - annual_attenuation_fraction)^(year - 1)",
         "interpretation":"illustrative assumed annual potential proxy only; no field-derived calibration, no mass balance and no verified removal",
         "areaHa":str(req.areaHa),"ratesTonnesPerHa":[str(x) for x in req.ratesTonnesPerHa],
         "potentialTonnesCO2PerTonneBasalt":str(req.potentialTonnesCO2PerTonneBasalt),
         "annualRealizationFraction":str(req.annualRealizationFraction),
         "annualAttenuationFraction":str(req.annualAttenuationFraction),
         "years":req.years,"assumptionNote":req.assumptionNote,
         "inputsEvidenceStatus":"researcher-assumed-unvalidated"},
       "status":"hypothetical-draft","publicationEnabled":False,
       "verifiedCDR":False,"netDurableAtmosphericRemoval":None,
       "sourceIntegrityVerifiedExternally":False}
    obj["calculationObjectHash"]=content_hash(obj)
    extract_series(obj)
    return obj

@router.post("/erw/v1.3.8.1.2/projects/{project_id}/preview")
def preview(project_id:str,request:ScenarioParameters,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization);project_for(project_id,owner)
    return {"ok":True,"visual":calculate(request,project_id),"saved":False}

@router.post("/erw/v1.3.8.1.2/projects/{project_id}/save")
def save(project_id:str,request:ScenarioParameters,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization);project_for(project_id,owner)
    obj=calculate(request,project_id)
    row=save_calculation(SavedCalculationCreateRequest(projectId=project_id,
      title=obj["title"],calculationObject=obj,
      tags=["erw","wexford","hypothetical","visualization"],
      metadata={"researchId":PROJECT_KEY,"scientificStatus":"assumptions-only","publicationEnabled":False}),owner)
    return {"ok":True,"id":row["id"],"sourceHash":obj["calculationObjectHash"],
      "visual":obj,"immutableSnapshot":True,"verifiedCDR":False}

@router.get("/erw/v1.3.8.1.2/projects/{project_id}/saved/{calculation_id}")
def saved_model(project_id:str,calculation_id:str,hash:str,authorization:Optional[str]=Header(default=None)):
    owner=owner_from_auth(authorization);project_for(project_id,owner)
    row=get_calculation(calculation_id,owner)
    if row.get("projectId")!=project_id:raise HTTPException(404,detail="Object not in project")
    obj=row.get("calculationObject")
    if not isinstance(obj,dict) or obj.get("schema")!=SCHEMA or "model" not in obj:
        raise HTTPException(422,detail="Not a Wexford scenario model")
    h=obj.get("calculationObjectHash")
    if h!=hash or h!=content_hash({k:v for k,v in obj.items() if k!="calculationObjectHash"}):
        raise HTTPException(409,detail="Saved calculation hash mismatch")
    if obj.get("verifiedCDR") is not False or obj.get("netDurableAtmosphericRemoval") is not None:
        raise HTTPException(422,detail="Unsupported verification status")
    extract_series(obj)
    return {"ok":True,"visual":obj,"id":calculation_id,"immutableSnapshot":True}

@router.get("/erw/v1.3.8.1.2/status")
def status():
    return {"ok":True,"extensionVersion":"1.3.8.1.2","previewAndSave":True,
     "hypotheticalAssumptions":True,"storedVisualPackage":True,
     "verifiedCDR":False,"fieldCalibrated":False,"publicationCertified":False}
