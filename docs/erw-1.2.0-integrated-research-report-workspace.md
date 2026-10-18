# ERW 1.2.0 — Integrated Research Report Workspace and Research Tables

First scoped report-authoring release. Based on the ERW 1.1.0 backend; source stored in `backend/app/erw_v120.py`.

## Scope

- Authenticated project listing and project research-object catalog.
- Owner-scoped, immutable draft manuscript snapshots, section editing and source-linked insertion records.
- **First-class research tables**: columns, rows, captions, optional saved research-source references, evidence status; stored as content-hashed Workbench calculation objects.
- Report preview renders saved table contents, not retyped Word tables.
- Client-side HTML download (open in Word), browser Print → Save PDF.
- Scientific figure/equation objects have reference placeholders in report preview at this stage; existing ERW 1.1 Explorer SVG export remains a separate workflow.
- No native DOCX/PDF programmatic backend export, equation typesetting, unsaved recovery, citation verification, outbound publication, automatic submission, or WordPress integrated SSO.
- Historical certification projects created under separate signed-session subjects remain inaccessible to other owners.
- Table authoring does not independently verify values, citations, measurements, or actual CO₂ removal. Sources are optional; references enforce ownership and stored-object hash consistency only.

## Mac preflight

```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.2.0-integrated-research-report-workspace
git switch feature/erw-1.2.0-integrated-research-report-workspace
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py backend/tests/test_erw_v030.py backend/tests/test_erw_v040.py backend/tests/test_erw_v050.py backend/tests/test_erw_v060.py backend/tests/test_erw_v070.py backend/tests/test_erw_v080.py backend/tests/test_erw_v090.py backend/tests/test_erw_v100.py backend/tests/test_erw_v110.py backend/tests/test_erw_v120.py
# Do not deploy until tests pass.
scp backend/app/erw_v120.py backend/tests/test_erw_v120.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo backend deployment (run on VPS, not Mac)

```bash
cd /opt/sustainable-catalyst/workbench
BACKUP="$HOME/workbench-erw120-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw110.yml "$BACKUP/"
cp /tmp/erw_v120.py backend/app/
cp /tmp/test_erw_v120.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
registration='\n# ERW 1.2.0 research report workspace and tables\nfrom app.erw_v120 import router as erw_v120_router\napp.include_router(erw_v120_router)\n'
if 'from app.erw_v120 import router' not in s:p.write_text(s.rstrip()+registration)
print('ERW 1.2 registration present')
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v120.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw120 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw120 -c 'from app.erw_v120 import status; print(status())'
cat > compose.erw120.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw120
EOF
docker compose -f compose.yml -f compose.erw120.yml config --quiet
docker compose -f compose.yml -f compose.erw120.yml up -d --no-build workbench
for i in $(seq 1 24); do
  STATUS=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "$STATUS"; [ "$STATUS" = healthy ] && break
  sleep 5
done
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.2.0/status; echo
curl -fsS -o /dev/null -w 'Explorer HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.2.0/report
```

On **Mac** (new terminal, do not run inside SSH):

```bash
ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77
```

Open `http://127.0.0.1:18088/erw/v1.2.0/report`. Provide a valid Workbench signed-session token, select a project, and create a table.

**Acceptance gates still required:** test suite passes, new backend healthy, unauthorized listing rejected, owner-scoped projects/tables, invalid source references rejected, table visible in draft preview, HTML download opens in Word, old ERW routers operational. Do not claim production certification before these pass.

**Rollback** (does not delete saved research database):

```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw110.yml up -d --no-build --force-recreate workbench
```
