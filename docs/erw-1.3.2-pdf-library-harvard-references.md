# ERW 1.3.2 — PDF Source Library & Harvard Reference Manager

**Stacked on draft ERW 1.3.1. Tests and production deployment pending.**

## Delivered
- Signed-in Sustainable Catalyst user can upload a PDF (20 MiB limit), preserved byte-for-byte in the persistent Workbench `/data/erw-pdf-sources` directory under hashed user/project namespace. Every PDF has a SHA-256 digest and owner-scoped saved source record.
- Private project PDF listing and authenticated original PDF retrieval, with SHA-256 integrity check.
- Harvard-style author/date reference creation from **researcher-entered, researcher-reviewed metadata**, saved as immutable citation approval object referencing PDF source hash.
- Citation panel in report canvas: PDF upload, source selection, metadata fields, explicit review checkbox, citation generation, and manual bibliography insertion. Reports saved through the existing append-only snapshot API.
- The 1.3.1 completed Word upload, figure/equation preview, Sustainable Catalyst login and research ownership are retained.

## Truth and security limits
- **PDF is not parsed for text, page anchors, DOI or author metadata in this release.** No OCR, DOI API, Crossref verification, automatic reference reconciliation, citation-to-claim matching or source-page linking yet.
- Harvard is a configurable future service; current formatter is a generic Harvard-style draft and is NOT independently certified against UCD's required variant.
- Bibliographic metadata is user-reviewed only, not externally validated.
- No automatic manuscript in-text citation placement; approved references are appended on demand to the bibliography editor.
- No DOCX or PDF **report generation** yet; browser Print/PDF and HTML export are unchanged. Uploaded PDF storage is not report export.
- Basic %PDF header and %%EOF trailer checks do **not** constitute deep PDF malware scanning or content security verification. Keep this interface behind existing loopback SSH tunnel, enforce authenticated access, apply upload limits and monitor storage growth. Production public upload needs malware scanning, quotas, MIME inspection, and robust PDF parsing safeguards.
- Nothing verifies net durable atmospheric removal; no publishing or outbound submission.

## Mac — fetch and test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.2-pdf-library-harvard-references
git switch feature/erw-1.3.2-pdf-library-harvard-references
source .venv/bin/activate
python -m py_compile backend/app/erw_v132.py backend/app/erw_v132_sources.py backend/tests/test_erw_v132.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Only after the complete suite passes:
scp backend/app/erw_v132.py backend/app/erw_v132_sources.py backend/tests/test_erw_v132.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backend first (after 1.3.1 is healthy)
Verify existing persistent /data mount and free space; preserve current image and secret config.
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw132-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw131.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v132.py /tmp/erw_v132_sources.py backend/app/
cp /tmp/test_erw_v132.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.2 PDF Source Library and Harvard Reference Manager\nfrom app.erw_v132 import router as erw_v132_router\nfrom app.erw_v132_sources import router as erw_v132_sources_router\napp.include_router(erw_v132_router)\napp.include_router(erw_v132_sources_router)\n"
if "from app.erw_v132 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.2 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v132.py backend/app/erw_v132_sources.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw132 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw132 -c 'from app.erw_v132 import build_page; print("Report assembled:",len(build_page()))'
```

Do not proceed if compilation, module import, or page assembly fails. Existing identity variables must remain mounted from `compose.erw121-identity.yml`. Confirm no environment secret values are printed with Compose config output.

```bash
cat > compose.erw132.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw132
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw132.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw132.yml up -d --no-build workbench
for i in $(seq 1 24); do
  state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $state"
  [ "$state" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.2/status; echo
curl -s -o /dev/null -w 'Report page HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.2/report
```

## Browser acceptance
Open `http://127.0.0.1:18088/erw/v1.3.2/report` on Mac with SSH tunnel open. Log in as your Sustainable Catalyst researcher identity and use the existing Wexford project. Upload a **copy** of a real research PDF, verify it appears in the PDF list, enter and review metadata, generate the Harvard reference, insert it into bibliography and save/reopen a report snapshot. Check that another signed-in identity cannot access the PDF or citation. Do not paste secrets or access tokens into chat.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw131.yml up -d --no-build --force-recreate workbench
```
**Never delete /data or the PDF upload directory during rollback.**

## Follow-on
ERW 1.3.3 page-level evidence/claim linking; ERW 1.3.4 native DOCX and PDF report export.
