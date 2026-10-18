# ERW 1.3.5 — End-to-End Scientific Publication Readiness Audit

Status: **development branch; tests and Contabo deployment pending**.

## Purpose
This build adds a non-destructive, owner-scoped readiness audit for a **saved** Wexford manuscript. It checks report integrity (via v1.3.4), nonempty manuscript, author attribution, bibliography, owner-scoped linked source integrity, uploaded PDF inventory, evidence annotations, and optional binary DOCX/PDF smoke generation.

No change to existing data or credentials, no outbound activity and no database migrations. Existing Word import, PDF library, Harvard entry form, evidence annotations, figure/table links, and native export remain. Audit endpoints do not publish reports.

**Important:** "End-to-end" is a technical readiness audit, **not** acceptance certification. Human-rendered DOCX/PDF acceptance, PDF source-page text verification, UCD-specific Harvard style and scientific evidence sufficiency remain explicitly unverified. `publicationCertified=false`, `publicationEnabled=false`, and `verifiedCDR=false` are permanent release invariants. Readiness output does not assert actual net atmospheric carbon removal.

## Mac — fetch, compile and run test suite
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.5-publication-certification
git switch feature/erw-1.3.5-publication-certification
source .venv/bin/activate
python -m py_compile backend/app/erw_v135.py backend/app/erw_v135_ui.py backend/tests/test_erw_v135.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Transfer only if full test suite passes
scp backend/app/erw_v135.py backend/app/erw_v135_ui.py backend/tests/test_erw_v135.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backend-first and safe rollback
Baseline: deployed ERW 1.3.4 with `python-docx` and ReportLab, healthy `sc-workbench`, identity overlay and read/write `/data` mount.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw135-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw134.yml; do
 [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v135.py /tmp/erw_v135_ui.py backend/app/
cp /tmp/test_erw_v135.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.5 publication readiness certification audit\nfrom app.erw_v135 import router as erw_v135_router\nfrom app.erw_v135_ui import router as erw_v135_ui_router\napp.include_router(erw_v135_router)\napp.include_router(erw_v135_ui_router)\n"
if "from app.erw_v135 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.5 audit routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v135.py backend/app/erw_v135_ui.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw135 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw135 -c 'from app.erw_v135_ui import build_page; from app.erw_v135 import status; print("Audit UI:",len(build_page())); print(status())'
```

Continue only if smoke test succeeds and all existing data mounts are unchanged.

```bash
cat > compose.erw135.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw135
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw135.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw135.yml up -d --no-build workbench
for i in $(seq 1 24); do
 status=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
 echo "$status"
 [ "$status" = healthy ] && break
 sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.5/status; echo
curl -s -o /dev/null -w 'Audit composer HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.5/report
```

## Browser audit
Open `http://127.0.0.1:18088/erw/v1.3.5/report` with your Mac SSH tunnel active, sign in to your Sustainable Catalyst account, open your Wexford project and a **saved** report snapshot. Under Publication readiness audit, click Load saved versions and Run read-only audit. Examine each PASS or PENDING gate. Export and inspect the actual DOCX and PDF separately. Preserve the original Word manuscript as deadline-safe fallback.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw134.yml up -d --no-build --force-recreate workbench
```
Never remove /data or its PDF/Word source documents and research snapshots.

## Next build block
1.3.6 — Manuscript Import & Structure Repair: clear distinction between *replace empty starter template* and *append*. Guard against doubled Abstract and Bibliography sections; keep original source unmodified.
