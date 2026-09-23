#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v7.12.0 release validation ==="
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
  "$ROOT/backend/tests/test_reproducible_experiment_engineering_package_v7120.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py" "$ROOT/tests/test_v700_static.py" \
  "$ROOT/tests/test_v710_static.py" "$ROOT/tests/test_v720_static.py" "$ROOT/tests/test_v730_static.py" \
  "$ROOT/tests/test_v740_static.py" "$ROOT/tests/test_v750_static.py" "$ROOT/tests/test_v760_static.py" \
  "$ROOT/tests/test_v770_static.py" "$ROOT/tests/test_v780_static.py" "$ROOT/tests/test_v790_static.py" \
  "$ROOT/tests/test_v7100_static.py" "$ROOT/tests/test_v7110_static.py" "$ROOT/tests/test_v7120_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7110-visual-scientific-computing-workspace.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v7120-reproducible-experiment-engineering-package.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then echo 'ERROR: SCWB_DIR bootstrap regression detected' >&2; exit 1; fi
"$PY" - <<'PYVERIFY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
assert c.get('/health').json()['version']=='7.12.0'
m=c.get('/repro-package/manifest').json(); assert m['ok'] and m['coreContract']=='sc.research.reproducible-package.v1'
spec={'packageKey':'release-v7120','title':'Release Package','projectEntityId':'project:release','packageKind':'mixed','components':[
 {'componentKey':'notebook','componentType':'notebook-run','componentRef':'sc://workbench/notebook/release','payload':{'notebookRunHash':'nb-release','cells':[]}},
 {'componentKey':'external-dataset','componentType':'dataset','componentRef':'sc://dataset/release','contentHash':'a'*64,'required':True}
], 'environments':[{'environmentKey':'workbench','environmentType':'workbench','environmentRef':'sc://workbench/runtime/7.12.0','versionRef':'7.12.0'}]}
r=c.post('/repro-package/build',json={'package':spec}); assert r.status_code==200,r.text; p=r.json(); assert p['integrityManifest']['allRequiredComponentsHashed'] is True
v=c.post('/repro-package/validate',json={'reproduciblePackage':p}); assert v.status_code==200 and v.json()['valid'] is True
replay=c.post('/repro-package/replay/plan',json={'reproduciblePackage':p,'mode':'replay'}); assert replay.status_code==200 and replay.json()['replayPerformed'] is False
core=c.post('/integration/core/repro-package/plan',json={'reproduciblePackage':p,'coreProjectEntityId':'core-project-v7120'},headers={'X-SC-Gateway-Service':'workbench','X-SC-Core-Version':'3.0'}); assert core.status_code==200,core.text; plan=core.json(); assert plan['coreContract']=='sc.research.reproducible-package.v1' and plan['corePackageIdMustComeFromCore'] is True and plan['automaticCoreDispatchAuthorized'] is False
print('PASS: Workbench v7.12.0 reproducible experiment and engineering package endpoints assembled')
PYVERIFY
echo "PASS: Workbench v7.12.0 release checks passed."
