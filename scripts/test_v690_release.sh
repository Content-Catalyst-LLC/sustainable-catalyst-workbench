#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench"
PYTHON_BIN="${SCWB_TEST_PYTHON:-python3}"
echo '=== Workbench v6.9.0 release validation ==='
grep -q 'APP_VERSION = "6.9.0"' "$ROOT/backend/app/release.py"
grep -q 'from app.v690 import router as v690_router' "$ROOT/backend/app/main.py"
grep -q 'Version: 6.9.0' "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q "define('SCWB_VERSION', '6.9.0')" "$PLUGIN/sustainable-catalyst-workbench.php"
grep -q 'sustainable-catalyst-workbench:6.9.0' "$ROOT/compose.yml"
grep -q 'sc.visual-runtime.scene.v1' "$ROOT/backend/app/v690.py"
grep -q 'sc.visual-runtime.grammar.v1' "$ROOT/backend/app/v690.py"
grep -q 'sc.visual-runtime.unified-reasoning.v1' "$ROOT/backend/app/v690.py"
grep -q 'httpx2>=2,<3' "$ROOT/backend/requirements.txt"
"$PYTHON_BIN" -m py_compile "$ROOT/backend/app/release.py" "$ROOT/backend/app/v640.py" "$ROOT/backend/app/v650.py" "$ROOT/backend/app/v660.py" "$ROOT/backend/app/v670.py" "$ROOT/backend/app/v680.py" "$ROOT/backend/app/v690.py" "$ROOT/backend/app/main.py"
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" -m pytest -q tests/test_visual_reasoning_runtime_adapter_v690.py tests/test_scenario_uncertainty_runtime_v680.py tests/test_computation_execution_lineage_bridge_v670.py tests/test_unified_research_session_bridge_v660.py tests/test_unified_runtime_contract_adapter_v650.py tests/test_platform_core_connectivity_v640.py)
(cd "$ROOT" && PYTHONPATH="$ROOT/backend:$ROOT" "$PYTHON_BIN" -m pytest -q tests/test_v690_static.py tests/test_v680_static.py tests/test_v670_static.py tests/test_v660_static.py tests/test_v650_static.py tests/test_v640_static.py)
if command -v php >/dev/null 2>&1; then php -l "$PLUGIN/sustainable-catalyst-workbench.php" >/dev/null; php -l "$PLUGIN/includes/scwb-v690-core-visual-reasoning-runtime.php" >/dev/null; fi
(cd "$ROOT/backend" && PYTHONPATH="$ROOT/backend" "$PYTHON_BIN" - <<'PY_VALIDATOR'
from fastapi.testclient import TestClient
from app.main import app
c=TestClient(app)
for path in ('/health','/runtime','/capabilities','/v680/status','/v690/status','/integration/core/visual-reasoning/manifest'):
 r=c.get(path); assert r.status_code==200,(path,r.status_code,r.text)
health=c.get('/health').json(); assert health['ok'] is True and health['version']=='6.9.0' and health['coreCompatible'] is True
caps=c.get('/capabilities').json(); assert caps['coreIntegration']['visualReasoningRuntimeAdapter'] is True
manifest=c.get('/integration/core/visual-reasoning/manifest').json(); assert manifest['version']=='6.9.0'; assert manifest['coreSceneContract']=='sc.visual-runtime.scene.v1'
payload={'projectEntityId':'project-release-probe','title':'Release probe','dataKind':'distribution','data':{'values':[1,2,3,4,5]},'sourceRef':'workbench:release-probe','coreExecutionId':'core-exec-release-probe'}
r=c.post('/integration/core/visual-reasoning/result/adapt',json=payload); assert r.status_code==200,r.text; m=r.json(); assert m['rendererNeutral'] is True and m['summary']['p50']==3
r=c.post('/integration/core/visual-reasoning/object/plan',json={'manifest':m}); assert r.status_code==200,r.text; d=r.json(); assert d['coreVisualEntityIdMustComeFromCore'] is True
r=c.post('/integration/core/visual-reasoning/scene/plan',json={'manifest':m,'coreVisualEntityId':'visual-release-probe'}); assert r.status_code==200,r.text; d=r.json(); assert d['coreSceneIdMustComeFromCore'] is True
r=c.post('/integration/core/visual-reasoning/grammar/plan',json={'manifest':m,'coreSceneId':'scene-release-probe'}); assert r.status_code==200,r.text; d=r.json(); assert d['coreCompositionIdMustComeFromCore'] is True
print('PASS: Workbench v6.9.0 Core visual reasoning runtime adapter endpoints assembled')
PY_VALIDATOR
)
echo 'PASS: Workbench v6.9.0 release checks passed.'
