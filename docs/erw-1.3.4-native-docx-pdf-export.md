# ERW 1.3.4 — Native DOCX & PDF Research Report Export

**Development branch / draft PR: tests, production build and browser acceptance pending.**

## Delivery and scientific scope
Authenticated, owner-scoped **saved** report snapshots can now be downloaded as real Microsoft Word (.docx) and PDF (.pdf) binaries, not HTML files renamed to different extensions. Export includes title, authors, manuscript sections, bibliography, linked saved tables, scientific equation **source notation**, and supported source-derived ERW 0.6 scenario line figures. Linked sources are checked against their saved object hashes and owner/project. Each report carries a DRAFT/unverified carbon-removal caveat. No publication.

**Deliberate limits:** Full math/TeX typesetting, all visualization grammars, faithful Word roundtrip with original layout, PDF source attachments and verified citations are not implemented. Unsupported plots are flagged in text rather than fabricated. The version reflects the **saved snapshot**, not unsaved edit-screen changes. Bibliographies are author-maintained and must be verified. The export is not a certification of net atmospheric CO₂ removal, additionality or permanence. Validate complex tables and long manuscripts visually before relying on them.

## Mac testing
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.4-native-docx-pdf-export
git switch feature/erw-1.3.4-native-docx-pdf-export
source .venv/bin/activate
python -m pip install 'python-docx>=1.1,<2' 'reportlab>=4.2,<5'
python -m py_compile backend/app/erw_v134.py backend/app/erw_v134_export.py backend/tests/test_erw_v134.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Transfer only after suite passes:
scp backend/app/erw_v134.py backend/app/erw_v134_export.py backend/tests/test_erw_v134.py backend/requirements.txt catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo backend first — safe staged deployment
Current baseline must be healthy ERW 1.3.3. The persistent /data mount, identity secrets, PDFs, and saved research projects must remain unchanged. A Python requirements update is mandatory for Docker to import Word/PDF libraries.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw134-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw133.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v134.py /tmp/erw_v134_export.py backend/app/
cp /tmp/test_erw_v134.py backend/tests/
cp /tmp/requirements.txt backend/requirements.txt
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.4 native DOCX and PDF research report export\nfrom app.erw_v134 import router as erw_v134_router\nfrom app.erw_v134_export import router as erw_v134_export_router\napp.include_router(erw_v134_router)\napp.include_router(erw_v134_export_router)\n"
if "from app.erw_v134 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.4 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v134.py backend/app/erw_v134_export.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw134 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw134 -c 'from app.erw_v134 import build_page; from app.erw_v134_export import make_pdf,make_docx; print("Composer:",len(build_page())); print("Native document libraries: PASS")'
```

Do not deploy until all checks pass. Native PDFs should be tested with an actual saved Wexford draft and user account.

```bash
cat > compose.erw134.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw134
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw134.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw134.yml up -d --no-build workbench
for i in $(seq 1 24); do
  STATUS=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $STATUS"
  [ "$STATUS" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.4/status; echo
curl -s -o /dev/null -w 'Composer HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.4/report
```

## Browser and artifact inspection
With existing SSH tunnel, open `http://127.0.0.1:18088/erw/v1.3.4/report`. Authenticate to Sustainable Catalyst, select Wexford project, **save snapshot after your last change**, choose that snapshot in Native Research Report Exports, download both formats. Open DOCX in Word/LibreOffice and PDF in Preview/Acrobat. Verify paragraph completeness, author names, table breaks, figure legibility, captions, original object hash and bibliography. Check no unsaved modifications leaked into export and no cross-owner access. Keep the file drafts confidential.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw133.yml up -d --no-build --force-recreate workbench
```
Preserve /data and never delete uploaded PDFs, Word source documents, research objects or snapshots.
