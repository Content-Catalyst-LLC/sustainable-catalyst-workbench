from copy import deepcopy
import math
import pytest
from pydantic import ValidationError
from app.research_flux import FluxRecipe,calculate

def recipe():return {'projectId':'synthetic-only','title':'Synthetic transport regression','source_kind':'simulation','source_refs':['synthetic:test'],'discharge_unit':'L/s','concentration_unit':'mmol/L','max_gap_seconds':20,'temporal_model':'trapezoidal-linear-flux','uncertainty_model':'independent-samples-and-inputs','treated':[{'timestamp':'2026-01-01T00:00:00Z','discharge':1,'concentration':2,'discharge_standard_uncertainty':.1,'concentration_standard_uncertainty':.2},{'timestamp':'2026-01-01T00:00:10Z','discharge':1,'concentration':2,'discharge_standard_uncertainty':.1,'concentration_standard_uncertainty':.2}]}

def test_units_integration_and_uncertainty_with_no_removal_promotion():
 x=recipe();r=calculate(FluxRecipe.model_validate(x))
 assert r['treated']['transport']==pytest.approx(.02)
 assert r['treated']['standard_uncertainty']==pytest.approx(math.sqrt(4.02)*.001)
 assert r['unit']=='mol' and r['net_removal']['value'] is None
 x['discharge_unit']='m3/s'
 assert calculate(FluxRecipe.model_validate(x))['treated']['transport']==pytest.approx(20)
 x['concentration_unit']='ueq/L'
 assert calculate(FluxRecipe.model_validate(x))['unit']=='eq'

def test_null_and_adverse_effects_and_missing_data_remain_explicit():
 x=recipe();x['control']=deepcopy(x['treated']);x['hydrological_comparability_ref']='synthetic-comparability'
 r=calculate(FluxRecipe.model_validate(x));assert r['treatment_minus_control']==0 and r['net_removal']['status']=='NOT_QUANTIFIED'
 for s in x['control']:s['concentration']=3
 assert calculate(FluxRecipe.model_validate(x))['treatment_minus_control']==pytest.approx(-.01)
 x['treated'][0]['discharge']=None
 assert calculate(FluxRecipe.model_validate(x))['treated']['status']=='NOT_QUANTIFIED'
 x=recipe();x['max_gap_seconds']=1
 assert calculate(FluxRecipe.model_validate(x))['treated']['transport'] is None

@pytest.mark.parametrize('patch',[{'discharge_unit':'m/s'},{'concentration_unit':'kg CO2/ha'},{'max_gap_seconds':float('nan')}])
def test_dimension_and_nonfinite_rejection(patch):
 with pytest.raises(ValidationError):FluxRecipe.model_validate({**recipe(),**patch})

def test_timezone_and_duplicate_timestamp_rejection():
 x=recipe();x['treated'][0]['timestamp']='2026-01-01T00:00:00'
 with pytest.raises(ValidationError):FluxRecipe.model_validate(x)
 x=recipe();x['treated'][1]['timestamp']=x['treated'][0]['timestamp']
 from fastapi import HTTPException
 with pytest.raises(HTTPException):calculate(FluxRecipe.model_validate(x))
