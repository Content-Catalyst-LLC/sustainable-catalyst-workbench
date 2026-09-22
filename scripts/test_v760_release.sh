#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.6.0 release validation ==="
"$PY" -m pytest -q \
  "$ROOT/backend/tests/test_platform_core_connectivity_v640.py" \
  "$ROOT/backend/tests/test_unified_runtime_contract_adapter_v650.py" \
  "$ROOT/backend/tests/test_unified_research_session_bridge_v660.py" \
  "$ROOT/backend/tests/test_computation_execution_lineage_bridge_v670.py" \
  "$ROOT/backend/tests/test_scenario_uncertainty_runtime_v680.py" \
  "$ROOT/backend/tests/test_visual_reasoning_runtime_adapter_v690.py" \
  "$ROOT/backend/tests/test_predictive_intelligence_runtime_v6100.py" \
  "$ROOT/backend/tests/test_forensic_quantitative_reconstruction_v6110.py" \
  "$ROOT/backend/tests/test_research_state_reproduction_snapshot_v6120.py" \
  "$ROOT/backend/tests/test_core_aware_experience_v6130.py" \
  "$ROOT/backend/tests/test_platform_integration_certification_v6140.py" \
  "$ROOT/backend/tests/test_unified_execution_runtime_v700.py" \
  "$ROOT/backend/tests/test_unified_execution_object_model_v710.py" \
  "$ROOT/backend/tests/test_scientific_runtime_orchestrator_v720.py" \
  "$ROOT/backend/tests/test_dataset_variable_parameter_workspace_v730.py" \
  "$ROOT/backend/tests/test_numerical_methods_solver_runtime_v740.py" \
  "$ROOT/backend/tests/test_simulation_dynamical_systems_runtime_v750.py" \
  "$ROOT/backend/tests/test_engineering_systems_runtime_v760.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v760-engineering-systems-runtime.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='7.6.0'
assert c.get('/v760/status').json()['analysisCount']==9
m=c.get('/engineering/manifest').json(); assert m['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1'
r=c.post('/engineering/analyze',json={'analysisKey':'mechanical.axial-member','inputs':{'force_n':10000,'area_m2':0.001,'yield_strength_pa':250000000}}); assert r.status_code==200,r.text
d=r.json(); assert abs(d['result']['stressMPa']-10)<1e-9 and d['executionObject']['objectKind']=='single_execution'
p=c.post('/engineering/analyze',json={'analysisKey':'fluids.pipe-flow','inputs':{'diameter_m':0.05,'length_m':10,'density_kg_m3':998,'dynamic_viscosity_pa_s':0.001,'volumetric_flow_m3_s':0.001,'roughness_m':1e-5}}); assert p.status_code==200,p.text; assert p.json()['result']['pressureDropPa']>=0
s=c.post('/engineering/system/run',json={'systemKey':'deploy','analyses':[{'itemKey':'dc','analysisKey':'electrical.dc-circuit','inputs':{'voltage_v':12,'current_a':2}},{'itemKey':'thermal','analysisKey':'thermal.convection','inputs':{'coefficient_w_m2k':10,'area_m2':1,'surface_temp_c':50,'fluid_temp_c':20}}]}); assert s.status_code==200,s.text; assert s.json()['analysisCount']==2 and s.json()['automaticCrossDomainCouplingPerformed'] is False
print('PASS: Workbench v7.6.0 engineering systems runtime endpoints assembled')
PYVERIFY
echo "PASS: Workbench v7.6.0 release checks passed."
