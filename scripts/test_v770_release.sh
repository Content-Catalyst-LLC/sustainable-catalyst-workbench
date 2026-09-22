#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.7.0 release validation ==="
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
  "$ROOT/backend/tests/test_engineering_systems_runtime_v760.py" \
  "$ROOT/backend/tests/test_optimization_design_space_v770.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v770-optimization-design-space.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='7.7.0'
assert c.get('/v770/status').json()['paretoFrontier'] is True
m=c.get('/design-space/manifest').json(); assert m['coreComputationLineageContract']=='sc.research.computation-analysis-execution-lineage.v1'
space={'designSpaceKey':'deploy','variables':[{'variableKey':'x','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5},{'variableKey':'y','lowerBound':0,'upperBound':4,'initial':1,'gridPoints':5}],'objectives':[{'objectiveKey':'cost','expression':'x**2+y**2','goal':'minimize','weight':1},{'objectiveKey':'performance','expression':'x+2*y','goal':'maximize','weight':0.2}],'constraints':[{'constraintKey':'min','expression':'x+y','relation':'>=','rhs':1}]}
e=c.post('/design-space/explore',json={'designSpace':space,'maxPoints':100}); assert e.status_code==200,e.text; assert e.json()['pointCount']==25
p=c.post('/design-space/pareto',json=e.json()); assert p.status_code==200,p.text; assert p.json()['frontierPointCount']>=1
r=c.post('/design-space/optimize',json={'designSpace':space}); assert r.status_code==200,r.text; d=r.json(); assert d['result']['evaluation']['feasible'] is True and d['executionObject']['objectKind']=='single_execution'
print('PASS: Workbench v7.7.0 optimization and design-space endpoints assembled')
PYVERIFY
echo "PASS: Workbench v7.7.0 release checks passed."
