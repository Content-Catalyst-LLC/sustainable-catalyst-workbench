from app.engines.runner import run_tool
from app.core.model_registry import list_tools

def test_registry_has_advanced_domains():
    domains = {t['domain'] for t in list_tools()}
    assert 'Engineering' in domains
    assert 'Architecture' in domains
    assert 'Energy' in domains
    assert 'Psychology' in domains

def test_linear_solver_runs():
    out = run_tool('linear-system-solver', {'A':'[[2,1],[1,3]]','b':'[5,7]'})
    assert out['ok'] is True
    assert 'solution' in out['values']

def test_energy_runs():
    out = run_tool('energy-systems-calculator', {'mode':'building_eui','inputs':'area_m2=1000;annual_kwh=180000'})
    assert out['ok'] is True
    assert out['values']['eui_kwh_per_m2_year'] == 180
