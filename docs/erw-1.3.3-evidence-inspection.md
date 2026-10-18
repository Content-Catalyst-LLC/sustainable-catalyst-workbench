# ERW 1.3.3 — Claim-to-Source Linking & Evidence Inspection

## Scope and limits
- Owner-scoped evidence annotations link a researcher-entered claim to an uploaded ERW 1.3.2 PDF source fingerprint, a manuscript section ID, a page reference, optional manually entered excerpt, evidence class, assessment (supports / contradicts / context / uncertain), review note, and an explicit "I compared excerpt against the PDF" toggle.
- Evidence records are append-only saved Workbench calculation objects; source original PDF SHA-256 is bound and rechecked on detail read. No destructive migration. Existing Word import, scientific figure insertion, report snapshot deduplication, and Harvard citation UI remain.
- The source inspection panel reports evidence and original PDF filename. It does not parse PDF content or identify source pages automatically. A checked excerpt is a **researcher assertion**, not independent machine verification.
- Do not claim these annotations scientifically verify an ERW claim, validate carbon removal, or certify a citation. No publishing, third-party uploads, outbound communications, PDF OCR, automatic unsupported-claim scanning, native DOCX/PDF report export, or true in-text citation injection.

## Mac — retrieve and test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.3-claim-source-evidence
git switch feature/erw-1.3.3-claim-source-evidence
source .venv/bin/activate
python -m py_compile backend/app/erw_v133.py backend/app/erw_v133_evidence.py backend/tests/test_erw_v133.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Only after all tests pass:
scp backend/app/erw_v133.py backend/app/erw_v133_evidence.py backend/tests/test_erw_v133.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — install backend first
Requires currently running ERW 1.3.2 including separate snapshot picker fix. Confirm active image is healthy, existing identity Compose overlay, and persistent writable /data bind mount. Back up backend and compose, preserve all secrets, database contents and uploaded PDF bytes.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw133-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw132-pickerfix.yml; do
 [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v133.py /tmp/erw_v133_evidence.py backend/app/
cp /tmp/test_erw_v133.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.3 evidence links and inspection\nfrom app.erw_v133 import router as erw_v133_router\nfrom app.erw_v133_evidence import router as erw_v133_evidence_router\napp.include_router(erw_v133_router)\napp.include_router(erw_v133_evidence_router)\n"
if "from app.erw_v133 import router" not in s:
 p.write_text(s.rstrip()+reg)
print("ERW 1.3.3 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v133.py backend/app/erw_v133_evidence.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw133 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw133 -c 'from app.erw_v133 import build_page; print("Composer assembled:",len(build_page()))'
```

Stop on any failure; do not deploy broken image.

```bash
cat > compose.erw133.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw133
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw133.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw133.yml up -d --no-build workbench
for i in $(seq 1 24); do
 status=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
 echo "$status"
 [ "$status" = healthy ] && break
 sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.3/status; echo
curl -sS -o /dev/null -w 'Evidence composer HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.3/report
```

## Browser acceptance
With existing Mac SSH tunnel, open `http://127.0.0.1:18088/erw/v1.3.3/report`. Sign into your Sustainable Catalyst identity, select your Wexford project, upload or select a real source PDF from the existing PDF Library, click Inspect saved evidence to populate current section list, create a claim and page reference, save annotation, refresh and inspect. Check integrity fingerprints and whether researcher-reviewed excerpt toggle is accurate. Test another owner's account cannot inspect these records. Do not claim page text automatically checked.

## Rollback
Restore previous image while preserving /data:
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw132-pickerfix.yml up -d --no-build --force-recreate workbench
```
