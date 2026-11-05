import pytest
from pydantic import ValidationError
from app.scientific_carbon_ledger import Ledger,calculate_ledger

def recipe():
 domains=['atmospheric-attribution','downstream-storage','reversals','extraction','crushing','transport','spreading','monitoring']
 return {'projectId':'synthetic','title':'Synthetic declared ledger','source_kind':'simulation','system_boundary_ref':'synthetic:boundary','time_window_ref':'synthetic:window','entries':[{'domain':d,'value':100 if i==0 else 80 if i==1 else 5,'standard_uncertainty':1,'unit':'kg CO2','source_refs':['synthetic:'+d],'method_ref':'synthetic:declared-mass','scope':'Synthetic test input; not field evidence'} for i,d in enumerate(domains)],'covariance':[[float(i==j) for j in range(8)] for i in range(8)],'uncertainty_method':'explicit-covariance-linear-propagation','uncertainty_assumptions_ref':'synthetic:independent-inputs'}
def test_storage_caps_attribution_and_no_truth_promotion():
 r=calculate_ledger(Ledger.model_validate(recipe()))
 assert r['declared_accounting_balance']['value']==50
 assert r['declared_accounting_balance']['standard_uncertainty']==pytest.approx(7**.5)
 assert r['net_removal']['value'] is None and r['net_removal']['status']=='NOT_QUANTIFIED'
def test_missing_domains_null_and_adverse_balance_preserved():
 x=recipe();x['entries'][1]['value']=30
 assert calculate_ledger(Ledger.model_validate(x))['declared_accounting_balance']['value']==0
 x['entries'][1]['value']=20
 assert calculate_ledger(Ledger.model_validate(x))['declared_accounting_balance']['value']==-10
 x=recipe();x['entries'].pop();x['covariance']=None
 assert calculate_ledger(Ledger.model_validate(x))['declared_accounting_balance']['value'] is None
@pytest.mark.parametrize('mutation',['mol','duplicate','bad-covariance','negative-emission','bool','missing-assumption'])
def test_ambiguous_accounting_and_invalid_uncertainty_rejected(mutation):
 x=recipe()
 if mutation=='mol':x['entries'][0]['unit']='mol'
 if mutation=='duplicate':x['entries'][1]['domain']=x['entries'][0]['domain']
 if mutation=='bad-covariance':x['covariance'][0][1]=2;x['covariance'][1][0]=2
 if mutation=='negative-emission':x['entries'][3]['value']=-1
 if mutation=='bool':x['entries'][0]['value']=True
 if mutation=='missing-assumption':x['uncertainty_assumptions_ref']=None
 with pytest.raises(ValidationError):Ledger.model_validate(x)
