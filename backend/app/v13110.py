"""Workbench v13.11.0 — Domain Calculator Registry & Templates."""
from __future__ import annotations
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from .release import APP_VERSION, PRODUCT_KEY, PRODUCT_NAME, RUNTIME_KIND
from .v510 import content_hash
from .v13100 import planning_contract

VERSION=APP_VERSION
router=APIRouter(tags=["workbench-v13110-domain-calculator-registry-templates"])
STATUS_SCHEMA="sc-workbench-domain-calculator-registry-status/1.0"
REGISTRY_SCHEMA="sc-workbench-domain-calculator-registry/1.0"
TEMPLATE_SCHEMA="sc-workbench-domain-calculator-template/1.0"
INSTANCE_SCHEMA="sc-workbench-domain-calculator-instance/1.0"

class TemplateInstantiateRequest(BaseModel):
    values: Dict[str,float]
    metadata: Dict[str,Any]=Field(default_factory=dict)

def _hash(x): return content_hash(x)

def P(id,label,unit,default,description,min_exclusive=None,min_inclusive=None):
    return {"id":id,"label":label,"type":"number","unit":unit,"default":default,"description":description,
            "constraints":{"minExclusive":min_exclusive,"minInclusive":min_inclusive}}

_RAW=[
{"id":"mathematics.circle-area","domain":"mathematics","category":"geometry","title":"Circle Area",
 "description":"Compute the area of a circle from its radius.","formula":"pi*({radius})**2","resultLabel":"Area",
 "resultUnit":"square units","operation":"evaluate","parameters":[P("radius","Radius","units",1.0,"Circle radius.",min_inclusive=0.0)]},
{"id":"physics.kinetic-energy","domain":"physics","category":"mechanics","title":"Kinetic Energy",
 "description":"Compute translational kinetic energy, KE = 1/2 m v².","formula":"0.5*({mass})*({velocity})**2",
 "resultLabel":"Kinetic energy","resultUnit":"J","operation":"evaluate","parameters":[P("mass","Mass","kg",1.0,"Object mass.",min_inclusive=0.0),P("velocity","Velocity","m/s",1.0,"Object velocity.")]},
{"id":"electrical.ohms-law-voltage","domain":"electrical-engineering","category":"circuits","title":"Ohm's Law — Voltage",
 "description":"Compute voltage from current and resistance, V = I R.","formula":"({current})*({resistance})",
 "resultLabel":"Voltage","resultUnit":"V","operation":"evaluate","parameters":[P("current","Current","A",1.0,"Circuit current."),P("resistance","Resistance","ohm",1.0,"Circuit resistance.",min_inclusive=0.0)]},
{"id":"energy.capacity-factor","domain":"energy","category":"generation","title":"Capacity Factor",
 "description":"Compute capacity factor from generated energy, rated capacity, and period hours.",
 "formula":"({energy})/(({capacity})*({hours}))","resultLabel":"Capacity factor","resultUnit":"fraction","operation":"evaluate",
 "parameters":[P("energy","Generated energy","MWh",500.0,"Energy generated during the period.",min_inclusive=0.0),P("capacity","Rated capacity","MW",100.0,"Nameplate/rated capacity.",min_exclusive=0.0),P("hours","Period","h",24.0,"Hours in the observation period.",min_exclusive=0.0)]},
{"id":"sustainability.emissions-intensity","domain":"sustainability","category":"carbon","title":"Emissions Intensity",
 "description":"Compute emissions per unit of output.","formula":"({emissions})/({output})","resultLabel":"Emissions intensity",
 "resultUnit":"emissions/output","operation":"evaluate","parameters":[P("emissions","Emissions","kg CO2e",1000.0,"Total emissions.",min_inclusive=0.0),P("output","Output","unit",100.0,"Activity, production, or service output.",min_exclusive=0.0)]},
{"id":"finance.compound-growth","domain":"finance","category":"time-value","title":"Compound Growth",
 "description":"Compute future value with periodic compounding.","formula":"({principal})*(1+({rate})/({periods}))**(({periods})*({years}))",
 "resultLabel":"Future value","resultUnit":"currency units","operation":"evaluate","parameters":[P("principal","Principal","currency",1000.0,"Starting principal.",min_inclusive=0.0),P("rate","Annual rate","decimal",0.05,"Annual nominal rate as a decimal."),P("periods","Compounds per year","1/year",12.0,"Compounding periods per year.",min_exclusive=0.0),P("years","Years","year",10.0,"Number of years.",min_inclusive=0.0)]},
{"id":"statistics.z-score","domain":"statistics","category":"descriptive-statistics","title":"Z-Score",
 "description":"Standardize an observation using z = (x - mean) / standard deviation.",
 "formula":"(({value})-({mean}))/({standard_deviation})","resultLabel":"Z-score","resultUnit":"standard deviations","operation":"evaluate",
 "parameters":[P("value","Value",None,110.0,"Observed value."),P("mean","Mean",None,100.0,"Reference mean."),P("standard_deviation","Standard deviation",None,15.0,"Reference standard deviation.",min_exclusive=0.0)]},
]

def templates():
    out=[]
    for raw in _RAW:
        t={"schema":TEMPLATE_SCHEMA,"version":VERSION,**raw,
           "canonicalCalculationAuthority":"v11 Unified Calculation Engine through v12.3 Calculator Workspace",
           "templateExecutesMathematics":False,"requiresExplicitInstantiation":True}
        t["templateHash"]=_hash({k:v for k,v in t.items() if k!="templateHash"}); out.append(t)
    return out

def get_template(template_id):
    for t in templates():
        if t["id"]==template_id: return t
    raise HTTPException(status_code=404,detail="Domain calculator template not found")

def domains():
    counts={}
    for t in templates(): counts[t["domain"]]=counts.get(t["domain"],0)+1
    return [{"id":k,"templateCount":v} for k,v in sorted(counts.items())]

def registry(domain=None,query=None):
    items=templates()
    if domain: items=[t for t in items if t["domain"]==domain]
    if query:
        q=query.strip().lower(); items=[t for t in items if any(q in str(t[k]).lower() for k in ("id","title","description","domain","category"))]
    body={"schema":REGISTRY_SCHEMA,"version":VERSION,"domains":domains(),"templates":items,"templateCount":len(items),
          "totalTemplateCount":len(templates()),"filters":{"domain":domain,"query":query},
          "governance":{"builtInRegistry":True,"immutableAtRuntime":True,"templateHashes":True,"canonicalExecutionOnly":True,"userValuesValidated":True},
          "wordpressRequired":False}
    body["registryHash"]=_hash({"domains":body["domains"],"templates":[t["templateHash"] for t in templates()],"governance":body["governance"]}); return body

def _fmt(v):
    if not math.isfinite(v): raise HTTPException(status_code=422,detail="Template parameters must be finite numbers")
    return format(float(v),".17g")

def _validate(p,v):
    c=p.get("constraints") or {}
    if c.get("minExclusive") is not None and not v>c["minExclusive"]: raise HTTPException(status_code=422,detail=f"{p['id']} must be greater than {c['minExclusive']}")
    if c.get("minInclusive") is not None and not v>=c["minInclusive"]: raise HTTPException(status_code=422,detail=f"{p['id']} must be at least {c['minInclusive']}")

def instantiate(template_id,values,metadata):
    t=get_template(template_id); allowed={p["id"] for p in t["parameters"]}; unknown=sorted(set(values)-allowed)
    if unknown: raise HTTPException(status_code=422,detail={"unknownParameters":unknown})
    resolved={}; lineage=[]
    for p in t["parameters"]:
        source="user" if p["id"] in values else "default"; v=float(values[p["id"]] if p["id"] in values else p["default"])
        _fmt(v); _validate(p,v); resolved[p["id"]]=v; lineage.append({"parameterId":p["id"],"value":v,"unit":p.get("unit"),"source":source})
    expr=t["formula"]
    for p in t["parameters"]: expr=expr.replace("{"+p["id"]+"}",_fmt(resolved[p["id"]]))
    req={"calculation":{"operation":t["operation"],"expression":expr},"requestedResultType":"numeric","requireVerification":True,"requireProvenance":True}
    inst={"schema":INSTANCE_SCHEMA,"version":VERSION,"templateId":t["id"],"templateHash":t["templateHash"],"domain":t["domain"],"category":t["category"],
          "title":t["title"],"resultLabel":t["resultLabel"],"resultUnit":t["resultUnit"],"values":resolved,"parameterLineage":lineage,
          "formulaTemplate":t["formula"],"instantiatedExpression":expr,"calculationRequest":req,"metadata":metadata,
          "policy":{"templateExecutesMathematics":False,"canonicalCalculatorRequired":True,"reviewBeforeExecution":True,"verificationRequired":True,"provenanceRequired":True}}
    inst["instanceHash"]=_hash({"templateHash":inst["templateHash"],"values":resolved,"instantiatedExpression":expr,"calculationRequest":req}); return inst

def domain_calculator_contract():
    prev=planning_contract(); features={"v13100PlanningPreserved":all(prev["features"].values()),"governedDomainRegistry":True,"domainFiltering":True,"templateSearch":True,
      "immutableBuiltInTemplates":True,"templateHashes":True,"parameterSchemas":True,"parameterDefaults":True,"parameterConstraints":True,"parameterLineage":True,
      "deterministicInstantiation":True,"explicitCalculationRequest":True,"canonicalExecutionOnly":True,"verificationRequired":True,"provenanceRequired":True,"wordpressRequiredFalse":True}
    body={"schema":"sc-workbench-domain-calculator-contract/1.0","version":VERSION,"features":features,"seedDomains":[d["id"] for d in domains()],
          "seedTemplateCount":len(templates()),"canonicalExecutionAuthority":"v11 Unified Calculation Engine through v12.3 Calculator Workspace","wordpressRequired":False}
    body["contractHash"]=_hash(body); return body

def status():
    c=domain_calculator_contract(); checks={"domainCalculatorRegistryReady":all(c["features"].values()),"v13100PlanningPreserved":c["features"]["v13100PlanningPreserved"],
      "canonicalCalculationAuthorityPreserved":c["features"]["canonicalExecutionOnly"],"templateRegistryPopulated":c["seedTemplateCount"]>=7,"wordpressRequiredFalse":c["wordpressRequired"] is False}
    return {"ok":all(checks.values()),"schema":STATUS_SCHEMA,"version":VERSION,"release":"Domain Calculator Registry & Templates","product":PRODUCT_KEY,"name":PRODUCT_NAME,
      "runtime":RUNTIME_KIND,"wordpressRequired":False,"domainCalculatorRegistryReady":all(checks.values()),"checks":checks,"templateCount":c["seedTemplateCount"],
      "domains":c["seedDomains"],"registryHash":registry()["registryHash"],"contractHash":c["contractHash"]}

@router.get("/v13110/status")
def status_route(): return status()
@router.get("/standalone/v1/domain-calculators/contract")
def contract_route(): return {"ok":True,"version":VERSION,"domainCalculators":domain_calculator_contract()}
@router.get("/standalone/v1/domain-calculators/domains")
def domains_route(): return {"ok":True,"version":VERSION,"domains":domains()}
@router.get("/standalone/v1/domain-calculators/registry")
def registry_route(domain:Optional[str]=Query(default=None),q:Optional[str]=Query(default=None)): return {"ok":True,"version":VERSION,"registry":registry(domain,q)}
@router.get("/standalone/v1/domain-calculators/templates/{template_id}")
def template_route(template_id:str): return {"ok":True,"version":VERSION,"template":get_template(template_id)}
@router.post("/standalone/v1/domain-calculators/templates/{template_id}/instantiate")
def instantiate_route(template_id:str,req:TemplateInstantiateRequest): return {"ok":True,"version":VERSION,"instance":instantiate(template_id,req.values,req.metadata)}
