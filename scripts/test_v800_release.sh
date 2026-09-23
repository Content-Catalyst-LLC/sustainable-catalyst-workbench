#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v8.0.0 release validation ==="
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
  "$ROOT/backend/tests/test_unified_computational_research_environment_v800.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py" "$ROOT/tests/test_v780_static.py" "$ROOT/tests/test_v790_static.py" \
  "$ROOT/tests/test_v7100_static.py" "$ROOT/tests/test_v7110_static.py" "$ROOT/tests/test_v7120_static.py" \
  "$ROOT/tests/test_v800_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7120-reproducible-experiment-engineering-package.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v800-unified-computational-research-environment.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='8.0.0'
m=c.get('/research-environment/manifest').json(); assert m['ok'] and m['version']=='8.0.0' and m['coreContracts']['unifiedResearchSession']=='sc.research.unified-research-scientific-investigation-runtime.v1'
spec={'environmentKey':'release-v800','title':'Unified Research Environment','projectEntityId':'project:release','activeSurface':'notebook','components':[
 {'componentKey':'notebook','componentType':'notebook-run','payload':{'notebookRunHash':'nb-release','cellRuns':[]}},
 {'componentKey':'visual','componentType':'visual-workspace','componentRef':'sc://workbench/visual/release','contentHash':'a'*64},
 {'componentKey':'package','componentType':'reproducible-package','componentRef':'sc://workbench/package/release','contentHash':'b'*64}
]}
r=c.post('/research-environment/build',json={'environment':spec}); assert r.status_code==200,r.text; env=r.json(); assert env['state']['componentCount']==3
v=c.post('/research-environment/validate',json={'researchEnvironment':env}); assert v.status_code==200 and v.json()['valid'] is True
surf=c.post('/research-environment/surface/plan',json={'researchEnvironment':env,'surface':'simulation','action':'prepare-run','requestPayload':{'simulationKind':'scalar-dynamic'}}); assert surf.status_code==200 and surf.json()['executionPerformed'] is False
snap=c.post('/research-environment/snapshot/plan',json={'researchEnvironment':env}); assert snap.status_code==200 and snap.json()['packageBuildPerformed'] is False and snap.json()['targetPath']=='/repro-package/build'
core=c.post('/integration/core/research-environment/plan',json={'researchEnvironment':env,'coreProjectEntityId':'core-project-v800'},headers={'X-SC-Gateway-Service':'workbench','X-SC-Core-Version':'3.0'}); assert core.status_code==200,core.text; plan=core.json(); assert plan['phase']=='prepare-session' and plan['coreSessionIdMustComeFromCore'] is True and plan['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v8.0.0 unified computational research environment endpoints assembled')
PYVERIFY
echo "PASS: Workbench v8.0.0 release checks passed."
