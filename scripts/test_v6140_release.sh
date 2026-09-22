#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${SCWB_TEST_PYTHON:-python3}"
export PYTHONPATH="$ROOT:$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "=== Workbench v6.14.0 release validation ==="
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
  "$ROOT/backend/tests/test_platform_integration_certification_v6140.py"
"$PY" -m pytest -q \
  "$ROOT/tests/test_v640_static.py" "$ROOT/tests/test_v650_static.py" "$ROOT/tests/test_v660_static.py" \
  "$ROOT/tests/test_v670_static.py" "$ROOT/tests/test_v680_static.py" "$ROOT/tests/test_v690_static.py" \
  "$ROOT/tests/test_v6100_static.py" "$ROOT/tests/test_v6110_static.py" "$ROOT/tests/test_v6120_static.py" \
  "$ROOT/tests/test_v6130_static.py" "$ROOT/tests/test_v6140_static.py"
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6100-predictive-intelligence-runtime.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6110-forensic-quantitative-reconstruction.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6120-research-state-reproduction-snapshot.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6130-core-aware-experience.php" >/dev/null
php -l "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v6140-platform-integration-certification.php" >/dev/null
if grep -q 'SCWB_DIR' "$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"; then
  echo "ERROR: unsafe SCWB_DIR bootstrap reference detected" >&2
  exit 1
fi
SCWB_REQUIRE_SERVICE_TOKEN=false "$PY" - <<'PY'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
status=c.get('/v6140/status'); assert status.status_code==200 and status.json()['version']=='6.14.0' and status.json()['declaredConformance'] is True
m=c.get('/integration/core/certification/manifest'); assert m.status_code==200 and m.json()['coreCertificationContract']=='sc.research.platform-integration-certification.v1'
r=c.get('/integration/core/certification/report/local'); assert r.status_code==200 and r.json()['declaredConformance'] is True and len(r.json()['reportHash'])==64
suite=c.post('/integration/core/certification/suite/prepare',json={}); assert suite.status_code==200 and suite.json()['automaticCoreDispatchAuthorized'] is False
product=c.post('/integration/core/certification/product/prepare',json={'coreSuiteId':'suite-release'}); assert product.status_code==200 and product.json()['request']['data']['product_version']=='6.14.0'
cases=c.post('/integration/core/certification/cases/prepare',json={'coreSuiteId':'suite-release'}); assert cases.status_code==200 and cases.json()['caseCount']==11
run=c.post('/integration/core/certification/run/prepare',json={'coreSuiteId':'suite-release','coreProductId':'product-release'}); assert run.status_code==200 and run.json()['automaticCorePersistenceAuthorized'] is False
print('PASS: Workbench v6.14.0 platform integration certification endpoints assembled')
PY
echo 'PASS: Workbench v6.14.0 release checks passed.'
