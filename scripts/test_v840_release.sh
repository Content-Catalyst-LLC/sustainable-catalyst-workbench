#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export SCWB_RESEARCH_ENVIRONMENT_STORE="${SCWB_RESEARCH_ENVIRONMENT_STORE:-${TMPDIR:-/tmp}/scwb-v840-release-store}"
rm -rf "$SCWB_RESEARCH_ENVIRONMENT_STORE"
echo "=== Workbench v8.4.0 release validation ==="
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
  "$ROOT/backend/tests/test_interactive_computational_notebook_v7100.py" \
  "$ROOT/backend/tests/test_visual_scientific_computing_workspace_v7110.py" \
  "$ROOT/backend/tests/test_reproducible_experiment_engineering_package_v7120.py" \
  "$ROOT/backend/tests/test_unified_computational_research_environment_v800.py" \
  "$ROOT/backend/tests/test_research_environment_persistence_recovery_v810.py" \
  "$ROOT/backend/tests/test_unified_research_project_workspace_v820.py" \
  "$ROOT/backend/tests/test_research_asset_artifact_registry_v830.py" \
  "$ROOT/backend/tests/test_interactive_execution_console_v840.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py" "$ROOT/tests/test_v780_static.py" "$ROOT/tests/test_v790_static.py" \
  "$ROOT/tests/test_v7100_static.py" "$ROOT/tests/test_v7110_static.py" "$ROOT/tests/test_v7120_static.py" \
  "$ROOT/tests/test_v800_static.py" "$ROOT/tests/test_v810_static.py" "$ROOT/tests/test_v820_static.py" "$ROOT/tests/test_v830_static.py" "$ROOT/tests/test_v840_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v840-interactive-execution-console.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
import os,tempfile
from fastapi.testclient import TestClient
from app.main import app
os.environ['SCWB_RESEARCH_ENVIRONMENT_STORE']=tempfile.mkdtemp(prefix='scwb-v840-release-')
c=TestClient(app)
assert c.get('/health').json()['version']=='8.4.0'
m=c.get('/execution-console/manifest').json(); assert m['ok'] and m['version']=='8.4.0' and m['capabilities']['durableProjectExecutionJobs'] is True
spec={'environmentKey':'release-v840-env','title':'Release Environment','projectEntityId':'release-v840-project','components':[]}
env=c.post('/research-environment/build',json={'environment':spec}).json()
assert c.post('/research-environment/persistence/save',json={'researchEnvironment':env,'expectedCurrentRevision':0,'reason':'release-check'}).status_code==200
ws=c.post('/research-projects/build',json={'project':{'projectKey':'release-v840-project','title':'Release Project','activeEnvironmentKey':'release-v840-env','activeEnvironmentRevision':1}}).json()
assert c.post('/research-projects/save',json={'workspace':ws,'expectedProjectRevision':0,'reason':'release-check'}).status_code==200
job=c.post('/execution-console/jobs/prepare',json={'projectKey':'release-v840-project','runtimeKind':'solver','request':{'problemKind':'root','problem':{'expression':'x**2-4','variable':'x','bracket':[0,3]},'solverKey':'root.brentq'}}); assert job.status_code==200,job.text
jid=job.json()['jobId']; run=c.post(f'/execution-console/jobs/{jid}/run',json={'expectedJobRevision':1,'reason':'release-run'}); assert run.status_code==200,run.text
assert run.json()['status']=='completed' and run.json()['scientificExecutionPerformed'] is True
print('PASS: Workbench v8.4.0 interactive execution console endpoints assembled')
PYVERIFY
echo "PASS: Workbench v8.4.0 release checks passed."
