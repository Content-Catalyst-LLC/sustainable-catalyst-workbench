"""Separate declared carbon-accounting balance from verified atmospheric removal.

Inputs must already be CO2 mass with explicit provenance; transported mol/eq
are never converted here. This adapter does not establish source attribution.
"""
from __future__ import annotations
import hashlib,json,math
from typing import Literal
from fastapi import APIRouter,Header,HTTPException
from pydantic import BaseModel,ConfigDict,Field,model_validator
from .v1220 import _owner,save_calculation,SavedCalculationCreateRequest
DOMAINS={'atmospheric-attribution','downstream-storage','reversals','extraction','crushing','transport','spreading','monitoring'}
class Strict(BaseModel):model_config=ConfigDict(extra='forbid',strict=True,allow_inf_nan=False)
class Entry(Strict):
 domain:Literal['atmospheric-attribution','downstream-storage','reversals','extraction','crushing','transport','spreading','monitoring']
 value:float|None=Field(default=None,ge=-1e100,le=1e100)
 standard_uncertainty:float|None=Field(default=None,ge=0,le=1e100)
 unit:Literal['kg CO2']
 source_refs:list[str]=Field(min_length=1,max_length=50)
 method_ref:str=Field(min_length=1,max_length=500)
 scope:str=Field(min_length=1,max_length=1000)
 @model_validator(mode='after')
 def nonnegative_deductions(self):
  if self.domain!='atmospheric-attribution' and self.value is not None and self.value<0:raise ValueError('Deductions and storage mass must be nonnegative; adverse attribution may be negative.')
  return self
class Ledger(Strict):
 projectId:str=Field(min_length=1,max_length=100)
 title:str=Field(min_length=1,max_length=240)
 source_kind:Literal['simulation','user-entered','field-observed']
 system_boundary_ref:str=Field(min_length=1,max_length=500)
 time_window_ref:str=Field(min_length=1,max_length=500)
 entries:list[Entry]=Field(min_length=1,max_length=8)
 covariance:list[list[float]]|None=None
 uncertainty_method:Literal['explicit-covariance-linear-propagation','not-declared']
 uncertainty_assumptions_ref:str|None=Field(default=None,min_length=1,max_length=500)
 @model_validator(mode='after')
 def validate_covariance(self):
  if len({e.domain for e in self.entries})!=len(self.entries):raise ValueError('Use one explicit aggregate entry per domain; duplicate domains would double count.')
  if self.covariance is not None:
   if self.uncertainty_method!='explicit-covariance-linear-propagation' or not self.uncertainty_assumptions_ref:raise ValueError('Covariance requires an explicit propagation method and assumptions.')
   n=len(self.entries)
   if len(self.covariance)!=n or any(len(row)!=n for row in self.covariance):raise ValueError('Covariance shape must match entry order.')
   import numpy as np
   matrix=np.asarray(self.covariance,dtype=float)
   if np.abs(matrix).max()>1e200:raise ValueError('Covariance magnitude exceeds the supported numerical range.')
   if not np.allclose(matrix,matrix.T,rtol=1e-10,atol=1e-12):raise ValueError('Covariance must be symmetric.')
   if any(e.standard_uncertainty is None for e in self.entries):raise ValueError('Covariance requires each entry standard uncertainty.')
   if any(not math.isclose(matrix[i,i],e.standard_uncertainty**2,rel_tol=1e-9,abs_tol=1e-12) for i,e in enumerate(self.entries)):raise ValueError('Covariance diagonal disagrees with declared standard uncertainties.')
   if np.linalg.eigvalsh(matrix).min() < -1e-10*max(1,float(np.abs(matrix).max())):raise ValueError('Covariance must be positive semidefinite.')
  return self

def calculate_ledger(recipe:Ledger):
 entries={e.domain:e for e in recipe.entries};missing=sorted(DOMAINS-set(entries));blockers=['Declared inputs do not establish atmospheric attribution, durable storage or independent verification.']
 if missing:blockers.append('Missing accounting domains: '+', '.join(missing))
 incomplete=[e.domain for e in recipe.entries if e.value is None]
 if incomplete:blockers.append('Missing mass values: '+', '.join(incomplete))
 balance=None;uncertainty=None;coefficients=None
 if not missing and not incomplete:
  attributable=entries['atmospheric-attribution'].value;stored=entries['downstream-storage'].value
  # Storage is an independently supported upper bound, not an additional credit.
  durable=min(attributable,stored)
  deductions=math.fsum(entries[d].value for d in DOMAINS-{'atmospheric-attribution','downstream-storage'})
  balance=durable-deductions
  if not math.isfinite(balance):raise HTTPException(422,'Accounting magnitude overflow.')
  if attributable==stored:blockers.append('Equal attribution/storage bounds form a nondifferentiable minimum; analytical uncertainty is unavailable.')
  else:
   limiting='atmospheric-attribution' if attributable<stored else 'downstream-storage'
   coefficients=[1 if e.domain==limiting else 0 if e.domain in {'atmospheric-attribution','downstream-storage'} else -1 for e in recipe.entries]
   if recipe.covariance is not None:
    variance=math.fsum(coefficients[i]*coefficients[j]*recipe.covariance[i][j] for i in range(len(coefficients)) for j in range(len(coefficients)))
    if not math.isfinite(variance):raise HTTPException(422,'Accounting uncertainty overflow.')
    uncertainty=math.sqrt(max(0,variance))
    blockers.append('Uncertainty is a local linear approximation; bound switching and source-model uncertainty require separate assessment.')
 if uncertainty is None:blockers.append('Declared covariance and supported uncertainty propagation are incomplete.')
 result={'schema':'sc-workbench-declared-carbon-ledger/1.0','method_version':'1.0','recipe':recipe.model_dump(),'declared_accounting_balance':{'value':balance,'unit':'kg CO2','standard_uncertainty':uncertainty,'confidence_interval':None,'uncertainty_distribution':'not-inferred','linear_coefficients':coefficients,'scientific_status':'declared-input arithmetic; not verified removal'},'net_removal':{'status':'NOT_QUANTIFIED','value':None,'blockers':blockers},'scientific_verification_performed':False,'certification_eligibility_asserted':False}
 result['calculationObjectHash']=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();return result
router=APIRouter(prefix='/standalone/v1/scientific-carbon-ledger',tags=['scientific-carbon-ledger'])
@router.post('/calculate')
def calculate_route(recipe:Ledger,authorization:str|None=Header(default=None)):
 _owner(authorization);return calculate_ledger(recipe)
@router.post('/save',status_code=201)
def save_route(recipe:Ledger,authorization:str|None=Header(default=None)):
 owner,_=_owner(authorization);result=calculate_ledger(recipe)
 return {'calculation':save_calculation(SavedCalculationCreateRequest(projectId=recipe.projectId,title=recipe.title,calculationObject=result,tags=['declared-carbon-ledger'],metadata={'scientificVerification':False}),owner)}
