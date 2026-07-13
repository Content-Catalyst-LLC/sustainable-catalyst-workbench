#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V270="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v270-visualization-dashboard.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v270.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v270.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v270.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RV="$ROOT/runner-go/internal/runner/version.go"
for path in "$PLUGIN" "$V270" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RV"; do
  [[ -f "$path" ]] || { echo "Missing: $path"; exit 1; }
done
grep -q 'Version: 2.7.0' "$PLUGIN"
grep -q "define('SCWB_VERSION', '2.7.0')" "$PLUGIN"
grep -q 'scwb-v270-visualization-dashboard.php' "$PLUGIN"
grep -q 'v270_router' "$BACKEND"
grep -q 'const Version = "2.7.0"' "$RV"
for marker in sc_workbench_scientific_visualization sc_workbench_engineering_dashboard sc_workbench_interactive_chart_studio sc_workbench_validation_overlay sc_workbench_system_state_view sc_workbench_visual_export_accessibility; do
  grep -q "$marker" "$V270" || exit 1
done
for route in /visualization/summary /distribution/histogram /dashboard/evaluate /validation/overlay /system-state/analyze /accessibility/describe; do
  grep -q "$route" "$ROUTES" || exit 1
done
grep -q 'mux.HandleFunc("/visualization-tools"' "$RUNNER"
grep -q 'mux.HandleFunc("/visualization-task"' "$RUNNER"
if command -v php >/dev/null; then
  php -l "$PLUGIN" >/dev/null
  php -l "$V270" >/dev/null
fi
if command -v node >/dev/null; then node --check "$JS"; fi
python3 -c 'from pathlib import Path; import sys; [compile(Path(f).read_text(), f, "exec") for f in sys.argv[1:]]' "$BACKEND" "$ROUTES"
PYTHONPATH="$ROOT" python3 - <<'PY'
from backend.app.v270 import AccessibleDescriptionRequest,DashboardMetric,DashboardRequest,HistogramRequest,SeriesSummaryRequest,StateEdge,StateNode,SystemStateRequest,ValidationOverlayRequest,accessible_description,analyze_system_state,distribution_histogram,evaluate_dashboard,validation_overlay,visualization_summary
summary=visualization_summary(SeriesSummaryRequest(values=[1,2,3,4,5],units='V')); assert summary['ok'] and summary['statistics']['mean']==3
hist=distribution_histogram(HistogramRequest(values=[1,1,2,3],bins=3)); assert hist['ok'] and sum(x['count'] for x in hist['bins'])==4
dash=evaluate_dashboard(DashboardRequest(metrics=[DashboardMetric(key='temperature',label='Temperature',value=42,warning_high=55,critical_high=70),DashboardMetric(key='latency',label='Latency',value=35,warning_high=25,critical_high=50)])); assert dash['overallStatus']=='warning'
overlay=validation_overlay(ValidationOverlayRequest(observed=[1,2.1,2.9],predicted=[1,2,3],uncertainty=[.1,.1,.1])); assert overlay['ok'] and overlay['metrics']['rmse']<.1
state=analyze_system_state(SystemStateRequest(nodes=[StateNode(id='sensor',state='normal'),StateNode(id='controller',state='warning')],edges=[StateEdge(source='sensor',target='controller')])); assert state['ok'] and state['statusCounts']['warning']==1
a11y=accessible_description(AccessibleDescriptionRequest(title='Response',chart_type='line',y=[1,2,4],units='V')); assert a11y['ok'] and '3 observations' in a11y['description']
print('v2.7.0 visualization calculation checks passed.')
PY
if command -v go >/dev/null; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.7.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner visualization-tools >/dev/null)
fi
python3 -c 'from pathlib import Path; import re,sys; root=Path(sys.argv[1]); pats=[re.compile(r"AIza[0-9A-Za-z_-]{20,}"),re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY")]; bad=[str(p) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() not in {".zip",".png",".jpg",".pyc"} and any(x.search(p.read_text(errors="ignore")) for x in pats)]; (_ for _ in ()).throw(SystemExit("Potential secret in "+bad[0])) if bad else print("Push-safe secret scan passed.")' "$ROOT"
echo 'Workbench v2.7.0 release checks passed.'
