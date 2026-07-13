#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLUGIN="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/sustainable-catalyst-workbench.php"
V260="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/includes/scwb-v260-multilanguage-runtime.php"
JS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/js/sc-workbench-v260.js"
CSS="$ROOT/wordpress-plugin/sustainable-catalyst-workbench/assets/css/sc-workbench-v260.css"
BACKEND="$ROOT/backend/app/main.py"
ROUTES="$ROOT/backend/app/v260.py"
RUNNER="$ROOT/runner-go/cmd/workbench-runner/main.go"
RV="$ROOT/runner-go/internal/runner/version.go"
for path in "$PLUGIN" "$V260" "$JS" "$CSS" "$BACKEND" "$ROUTES" "$RUNNER" "$RV"; do
  [[ -f "$path" ]] || { echo "Missing: $path"; exit 1; }
done
grep -q 'Version: 2.6.0' "$PLUGIN"
grep -q 'scwb-v260-multilanguage-runtime.php' "$PLUGIN"
grep -q 'v260_router' "$BACKEND"
grep -q 'const Version = "2.6.0"' "$RV"
for marker in sc_workbench_multilanguage_runtime sc_workbench_language_equivalence sc_workbench_numerical_benchmark sc_workbench_runtime_project_generator sc_workbench_reproducibility_validator sc_workbench_execution_audit; do
  grep -q "$marker" "$V260" || exit 1
done
for route in /runtime/catalog /equivalence/compare /numerical/benchmark /projects/generate /reproducibility/validate /execution/audit; do
  grep -q "$route" "$ROUTES" || exit 1
done
grep -q 'mux.HandleFunc("/multi-language-tools"' "$RUNNER"
grep -q 'mux.HandleFunc("/multi-language-task"' "$RUNNER"
for language in python javascript r sql go c cpp rust haskell assembly; do grep -q "\"$language\"" "$ROUTES" || exit 1; done
if command -v php >/dev/null; then
  php -l "$PLUGIN" >/dev/null
  php -l "$V260" >/dev/null
fi
if command -v node >/dev/null; then node --check "$JS"; fi
python3 -c 'from pathlib import Path; import sys; [compile(Path(f).read_text(), f, "exec") for f in sys.argv[1:]]' "$BACKEND" "$ROUTES"
PYTHONPATH="$ROOT" python3 - <<'PY'
from backend.app.v260 import AuditRequest,BenchmarkRequest,EquivalenceRequest,ExecutionRecord,ProjectRequest,ReproducibilityRequest,audit_execution,compare_equivalence,generate_project,numerical_benchmark,runtime_catalog,validate_reproducibility
catalog=runtime_catalog(); assert catalog['ok'] and all(x in catalog['languages'] for x in ['python','javascript','r','sql','go','c','cpp','rust','haskell','assembly'])
eq=compare_equivalence(EquivalenceRequest(calculation='energy',inputs={'power_kw':2.5,'hours':8},outputs={'python':20,'go':20.0000000001},absolute_tolerance=1e-6,relative_tolerance=1e-6)); assert eq['ok']
bench=numerical_benchmark(BenchmarkRequest(benchmark='cancellation',values=[1e16,1,-1e16])); assert bench['ok'] and bench['absoluteErrors'][bench['bestMethod']] <= bench['absoluteErrors']['naive']
project=generate_project(ProjectRequest(language='rust',project_name='energy-model',expression='power_kw * hours')); assert project['ok'] and 'main.rs' in project['files']
repro=validate_reproducibility(ReproducibilityRequest(records=[ExecutionRecord(language='python',runtime='3.12',output='20.0'),ExecutionRecord(language='go',runtime='1.24',output='20')],comparison_mode='numeric',tolerance=1e-9,required_languages=['python','go'])); assert repro['ok']
audit=audit_execution(AuditRequest(language='python',source_bytes=100,timeout_seconds=8,output_bytes=100,filesystem_mode='temporary',network_access='disabled',explicit_consent=True)); assert audit['ok']
print('v2.6.0 calculation checks passed.')
PY
if command -v go >/dev/null; then
  (cd "$ROOT/runner-go" && go test ./... && go vet ./...)
  [[ "$(cd "$ROOT/runner-go" && go run ./cmd/workbench-runner version)" == "2.6.0" ]]
  (cd "$ROOT/runner-go" && go run ./cmd/workbench-runner multi-language-tools >/dev/null)
fi
python3 -c 'from pathlib import Path; import re,sys; root=Path(sys.argv[1]); pats=[re.compile(r"AIza[0-9A-Za-z_-]{20,}"),re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}"),re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY")]; bad=[str(p) for p in root.rglob("*") if p.is_file() and ".git" not in p.parts and p.suffix.lower() not in {".zip",".png",".jpg",".pyc"} and any(x.search(p.read_text(errors="ignore")) for x in pats)]; (_ for _ in ()).throw(SystemExit("Potential secret in "+bad[0])) if bad else print("Push-safe secret scan passed.")' "$ROOT"
echo 'Workbench v2.6.0 release checks passed.'
