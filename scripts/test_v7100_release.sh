#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.10.0 release validation ==="
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
  "$ROOT/backend/tests/test_scientific_workflow_graph_v790.py" \
  "$ROOT/backend/tests/test_interactive_computational_notebook_v7100.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py" "$ROOT/tests/test_v780_static.py" "$ROOT/tests/test_v790_static.py" "$ROOT/tests/test_v7100_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7100-interactive-computational-notebook.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='7.10.0'
assert c.get('/v7100/status').json()['hiddenInterpreterState'] is False
nb={'notebookKey':'deploy-v7100','cells':[
 {'cellId':'eng','cellType':'engineering','request':{'analysisKey':'mechanical.axial-member','inputs':{'force_n':1000,'area_m2':0.01,'length_m':1,'elastic_modulus_pa':200000000000}}},
 {'cellId':'vv','cellType':'validation','action':'benchmark','dependsOn':['eng'],'bindings':[{'sourceNodeId':'eng','sourcePath':'result','targetPath':'targetResult'}],'request':{'cases':[{'caseKey':'stress','actualPath':'stressPa','expected':100000,'absoluteTolerance':1e-9,'relativeTolerance':0}]}}
]}
r=c.post('/notebooks/run',json={'notebook':nb}); assert r.status_code==200,r.text; d=r.json(); assert d['ok'] and d['completedExecutableCellCount']==2 and d['hiddenInterpreterStateUsed'] is False
v=c.post('/notebooks/run/validate',json={'notebookRun':d}); assert v.status_code==200 and v.json()['valid'] is True
p=c.post('/notebooks/replay/plan',json={'notebookRun':d}); assert p.status_code==200 and p.json()['replayPerformed'] is False
g=c.post('/notebooks/workflow-graph/plan',json=nb); assert g.status_code==200 and len(g.json()['graph']['nodes'])==2
cp=c.post('/integration/core/notebook-workflow/plan',json={'notebookRun':d,'coreWorkflowId':'core-nb-v7100'}); assert cp.status_code==200,cp.text; pp=cp.json(); assert pp['coreWorkflowContract']=='sc.research.workflow-orchestration.v1' and len(pp['stageRegistrations'])==2 and pp['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v7.10.0 interactive computational notebook endpoints assembled')
PYVERIFY
echo "PASS: Workbench v7.10.0 release checks passed."
