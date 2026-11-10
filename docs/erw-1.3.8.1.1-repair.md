# ERW 1.3.8.1.1 — Research Object Discovery & Visualization Repair

**Draft implementation; no certification claims until tests, deployment and real Wexford browser acceptance pass.**

## What changed
- Added `/erw/v1.3.8.1.1/projects/{project_id}/discover`, which reads all saved calculations for the authenticated project, not only the ERW 0.6 visual-package schema.
- Each object is marked `chart-ready`, `hash-invalid`, `unsupported-verification-status`, or `no-compatible-scenario-series`; no silent filtering.
- Hash-valid, unverified saved ERW scenario series with an existing `scenario-trajectories` view can be plotted without writing or duplicating a visual package. This is a read-only *view*, not a migrated or minted research object. No synthetic data is substituted.
- New `/erw/v1.3.8.1.1/report` page adds working Discover/Plot controls, source hash, SVG and CSV exports and explicit empty states. Original 1.3.8.1 controls remain for compatibility; use the new **Saved research objects — discovery & visual inspection** panel.
- No model execution, confidence-interval calculation, verified CDR, data migration, stored data mutation, or automatic DOCX/PDF insertion.
- If existing calculations contain no saved `scenario-trajectories` numerical points, this build diagnoses that reality rather than pretending to have sourced graphics.

## Mac — source checkout and testing
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin fix/erw-1.3.8.1.1-discovery-visualization
git switch fix/erw-1.3.8.1.1-discovery-visualization
source .venv/bin/activate
python -m py_compile backend/app/erw_v13811_repair.py backend/app/erw_v13811_ui.py backend/tests/test_erw_v13811.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py backend/tests/test_erw_style_engine.py
```
Do not erase or stash unrelated untracked files. If Git reports checkout conflicts, inspect and reconcile them first.

Only after tests pass:
```bash
scp backend/app/erw_v13811_repair.py backend/app/erw_v13811_ui.py backend/tests/test_erw_v13811.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backup and backend-first build
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw13811-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw1381.yml compose.erw138-png.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v13811_repair.py /tmp/erw_v13811_ui.py backend/app/
cp /tmp/test_erw_v13811.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.8.1.1 read-only research object discovery repair\nfrom app.erw_v13811_repair import router as erw_v13811_repair_router\nfrom app.erw_v13811_ui import router as erw_v13811_ui_router\napp.include_router(erw_v13811_repair_router)\napp.include_router(erw_v13811_ui_router)\n"
if "from app.erw_v13811_repair import router" not in s:p.write_text(s.rstrip()+reg)
print("1.3.8.1.1 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v13811_repair.py backend/app/erw_v13811_ui.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw13811 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw13811 -c 'from app.erw_v13811_ui import build_page; from app.erw_v13811_repair import status; assert "sc13811discover" in build_page(); print(status())'
```

Only after smoke tests pass:
```bash
cat > compose.erw13811.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw13811
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw13811.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw13811.yml up -d --no-build workbench
for i in $(seq 1 24); do
  state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "$state"
  [ "$state" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.8.1.1/status; echo
curl -sS -o /dev/null -w 'UI HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.8.1.1/report
```

## Wexford end-to-end acceptance
From Mac, start/maintain tunnel `ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77`.
Open `http://127.0.0.1:18088/erw/v1.3.8.1.1/report`, log in, choose project `baf85d6f-8821-451f-87f6-5a90ccfd5f56`, then click **Discover saved project objects**. Confirm inventory number, inspect status reasons, and if an object is chart-ready select it and click **Plot eligible saved source**. Inspect SVG/CSV and source hash. If no object is chart-ready, report the counts/reasons; this is evidence a genuine saved compatible series is needed. This release cannot certify an actual Wexford chart without such a series.

## Rollback
Use the *actual previously running* Compose override/image, for example:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw1381.yml up -d --no-build --force-recreate workbench
```
Never delete `/data`, reset the research project, or prune Docker volumes.
