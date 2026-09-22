#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.9.0 release validation ==="
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
  "$ROOT/backend/tests/test_optimization_design_space_v770.py" \
  "$ROOT/backend/tests/test_model_validation_verification_v780.py" \
  "$ROOT/backend/tests/test_scientific_workflow_graph_v790.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py" "$ROOT/tests/test_v780_static.py" "$ROOT/tests/test_v790_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v790-scientific-workflow-graph.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='7.9.0'
assert c.get('/v790/status').json()['acyclicDependencyGraphs'] is True
graph={'graphKey':'deploy-v790','nodes':[
 {'nodeId':'eng','nodeType':'engineering','request':{'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.01,'length_m':1,'elastic_modulus_pa':200000000000}}},
 {'nodeId':'vv','nodeType':'validation','action':'benchmark','dependsOn':['eng'],'bindings':[{'sourceNodeId':'eng','sourcePath':'result','targetPath':'targetResult'}],'request':{'cases':[{'caseKey':'stress','actualPath':'stressPa','expected':100000,'absoluteTolerance':1e-9,'relativeTolerance':0}]}}
]}
r=c.post('/workflow-graph/run',json={'graph':graph}); assert r.status_code==200,r.text; d=r.json(); assert d['ok'] and d['completedNodeCount']==2 and d['automaticOutputSubstitutionPerformed'] is False
v=c.post('/workflow-graph/run/validate',json={'graphRun':d}); assert v.status_code==200 and v.json()['valid'] is True
p=c.post('/integration/core/workflow-graph/plan',json={'graphRun':d,'coreWorkflowId':'core-wf-v790'}); assert p.status_code==200,p.text; pp=p.json(); assert pp['coreWorkflowContract']=='sc.research.workflow-orchestration.v1' and len(pp['stageRegistrations'])==2 and pp['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v7.9.0 scientific workflow graph endpoints assembled')
PYVERIFY
echo "PASS: Workbench v7.9.0 release checks passed."
