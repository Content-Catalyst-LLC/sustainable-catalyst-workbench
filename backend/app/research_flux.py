"""Dimensionally explicit transport and treatment-control recipes.

Transported mol/eq are never silently converted into atmospheric CO2 removal.
Recipes persist through the existing owned CalculationObject store.
"""
from __future__ import annotations
from datetime import datetime
import hashlib,json,math
from typing import Literal
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator,field_validator
from .v1220 import _owner,save_calculation,SavedCalculationCreateRequest
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
class Sample(Strict):
 timestamp:datetime
 discharge:float|None=Field(default=None,ge=0,strict=True)
 concentration:float|None=Field(default=None,ge=0,strict=True)
 discharge_standard_uncertainty:float|None=Field(default=None,ge=0,strict=True)
 concentration_standard_uncertainty:float|None=Field(default=None,ge=0,strict=True)
 @field_validator('timestamp',mode='before')
 @classmethod
 def explicit_timestamp(cls,value):
  if not isinstance(value,(str,datetime)):raise ValueError('Use an explicit timezone-aware measurement timestamp.')
  return value
 @model_validator(mode='after')
 def aware(self):
  if self.timestamp.tzinfo is None:raise ValueError('Measurement timestamp requires a timezone.')
  return self
class FluxRecipe(Strict):
 projectId:str=Field(min_length=1,max_length=100)
 title:str=Field(min_length=1,max_length=240)
 source_kind:Literal['field-observed','simulation','user-entered']
 source_refs:list[str]=Field(min_length=1,max_length=100)
 discharge_unit:Literal['L/s','m3/s']
 concentration_unit:Literal['mmol/L','mol/m3','ueq/L']
 max_gap_seconds:float=Field(gt=0)
 temporal_model:Literal['trapezoidal-linear-flux']
 uncertainty_model:Literal['independent-samples-and-inputs','not-declared']
 treated:list[Sample]=Field(min_length=2,max_length=10000)
 control:list[Sample]|None=Field(default=None,min_length=2,max_length=10000)
 hydrological_comparability_ref:str|None=Field(default=None,min_length=1,max_length=300)
 area_m2:float|None=Field(default=None,gt=0)

def integrate(samples,recipe):
 times=[s.timestamp.timestamp() for s in samples]
 dt=[b-a for a,b in zip(times,times[1:])]
 if any(t<=0 for t in dt):raise HTTPException(422,'Duplicate or unordered measurement timestamps.')
 if any(t>recipe.max_gap_seconds for t in dt):
  return {'status':'NOT_QUANTIFIED','blockers':['Discharge/chemistry interval exceeds the declared coverage limit.'],'transport':None,'standard_uncertainty':None}
 if any(s.discharge is None or s.concentration is None for s in samples):
  return {'status':'NOT_QUANTIFIED','blockers':['Missing discharge or concentration blocks transport integration.'],'transport':None,'standard_uncertainty':None}
 qfactor=1 if recipe.discharge_unit=='L/s' else 1000
 cfactor=1e-6 if recipe.concentration_unit=='ueq/L' else .001
 weights=[dt[0]/2]+[(dt[i-1]+dt[i])/2 for i in range(1,len(samples)-1)]+[dt[-1]/2]
 flux=[s.discharge*qfactor*s.concentration*cfactor for s in samples]
 transport=math.fsum(w*f for w,f in zip(weights,flux))
 if not math.isfinite(transport):raise HTTPException(422,'Transport overflow; unsupported input magnitude.')
 variance=None
 if recipe.uncertainty_model=='independent-samples-and-inputs' and all(s.discharge_standard_uncertainty is not None and s.concentration_standard_uncertainty is not None for s in samples):
  # Shared interval endpoints enter once with their combined trapezoid weight.
  variances=[(qfactor*cfactor)**2*(s.concentration**2*s.discharge_standard_uncertainty**2+s.discharge**2*s.concentration_standard_uncertainty**2+s.discharge_standard_uncertainty**2*s.concentration_standard_uncertainty**2) for s in samples]
  variance=math.fsum(w*w*v for w,v in zip(weights,variances))
  if not math.isfinite(variance):raise HTTPException(422,'Uncertainty overflow.')
 return {'status':'CALCULATED_FROM_DECLARED_INPUTS','transport':transport,'standard_uncertainty':math.sqrt(variance) if variance is not None else None,
  'uncertainty_model':recipe.uncertainty_model,'uncertainty_distribution':'not-inferred','confidence_interval':None,
  'flux':flux,'timestamps':[s.timestamp.isoformat() for s in samples],'coverage_seconds':math.fsum(dt),'blockers':[] if variance is not None else ['Measurement uncertainty or independence support is undeclared.']}

def calculate(recipe:FluxRecipe):
 treated=integrate(recipe.treated,recipe);control=integrate(recipe.control,recipe) if recipe.control else None
 blockers=['Atmospheric source correction, downstream fate, lifecycle inventory and independent review are required.']
 effect=None;effect_uncertainty=None
 if control is None:blockers.append('No untreated control; treatment attribution is unavailable.')
 elif not recipe.hydrological_comparability_ref:blockers.append('Hydrological comparability has not been documented.')
 elif [s.timestamp for s in recipe.treated]!=[s.timestamp for s in recipe.control]:blockers.append('Treated and control observation windows do not match.')
 elif treated['transport'] is not None and control['transport'] is not None:
  effect=treated['transport']-control['transport']
  if treated['standard_uncertainty'] is not None and control['standard_uncertainty'] is not None:
   # Between-arm dependence is not supplied; do not assume independent arms.
   blockers.append('Treatment-control covariance is undeclared; effect uncertainty is not quantified.')
 blockers.extend(treated['blockers']);blockers.extend(control['blockers'] if control else [])
 unit='eq' if recipe.concentration_unit=='ueq/L' else 'mol'
 result={'schema':'sc-workbench-scientific-transport-result/1.0','method_version':'1.0','source_kind':recipe.source_kind,
  'unit':unit,'treated':treated,'control':control,'treatment_minus_control':effect,'effect_standard_uncertainty':effect_uncertainty,
  'area_m2':recipe.area_m2,'normalized_effect_per_m2':effect/recipe.area_m2 if effect is not None and recipe.area_m2 else None,
  'net_removal':{'status':'NOT_QUANTIFIED','value':None,'unit':'kg CO2','blockers':blockers},
  'scientific_verification_performed':False,'certification_eligibility_asserted':False,
  'recipe':recipe.model_dump(mode='json')}
 result['calculationObjectHash']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
 return result
router=APIRouter(prefix='/standalone/v1/scientific-transport',tags=['scientific-transport'])
@router.post('/calculate')
def calculate_route(recipe:FluxRecipe,authorization:str|None=Header(default=None)):
 _owner(authorization);return calculate(recipe)
@router.post('/save',status_code=201)
def save_route(recipe:FluxRecipe,authorization:str|None=Header(default=None)):
 owner,_=_owner(authorization);result=calculate(recipe)
 return {'calculation':save_calculation(SavedCalculationCreateRequest(projectId=recipe.projectId,title=recipe.title,calculationObject=result,tags=['scientific-transport'],metadata={'sourceRefs':recipe.source_refs,'scientificVerification':False}),owner)}
