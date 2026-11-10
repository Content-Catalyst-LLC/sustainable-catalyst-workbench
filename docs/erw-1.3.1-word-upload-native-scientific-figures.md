# ERW 1.3.1 — Source-backed scientific figures & completed Word document upload

## Capabilities
- The authenticated 1.3.0 document canvas now has an Upload completed Word document control. Accepts normal .docx up to 8 MiB with protected, owner-scoped byte intake. Retains exact original bytes under `/data/erw-word-documents`, stores SHA-256/file metadata as an immutable calculation/source record in the Workbench project, and imports document Heading-styled sections and plain-text paragraphs into **editable** manuscript sections.
- Existing 1.2 report source inserts for saved ERW 0.6 visualization and 0.7 equation objects now render inline SVG in document preview and downloaded HTML. Source data is fetched using the signed account token from existing owner-scoped, hash-integrity-checked endpoints. Modeled results are labeled hypothetical/unverified.
- All saved drafts, research objects and identity live in existing Workbench database/session boundary; no WordPress dependency. No migrations or deletion.

**Limitations:** Plain text/heading extraction does not faithfully import tables, images, footnotes, references, track changes, page formatting, section layout, Word equations or embedded figures. Those require subsequent development and manual verification. Word file import does NOT overwrite the existing report; it appends editable sections. An original copy is preserved in persistent /data. This build does not yet have original DOCX download or Word-round-trip editing. No native DOCX export, programmatic PDF, PDF source uploads, Harvard reference engine, chart uncertainty shading, mathematical TeX typesetting, or unverified evidence promotion. SVGs are rendered only for correctly stored ERW 0.6 and 0.7 source objects. A newly created Wexford project with no visualization objects cannot magically display charts: save research calculations/visual objects under the logged-in account first. Keep the account login restricted to localhost tunnel until security hardening.

## Mac: get branch and test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.1-native-scientific-figures
git switch feature/erw-1.3.1-native-scientific-figures
source .venv/bin/activate
python -m py_compile backend/app/erw_v131.py backend/app/erw_v131_import.py backend/tests/test_erw_v131.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Continue only after complete test pass:
scp backend/app/erw_v131.py backend/app/erw_v131_import.py backend/tests/test_erw_v131.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo backend deployment
**Backend first.** Preserve the current 1.3.0 Docker image and all /data mounts. Do not expose account-enrollment keys or reset `SCWB_SESSION_SECRET`. Space may have been reclaimed from Docker build cache, but repeated builds will increase usage again.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw131-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw130.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v131.py /tmp/erw_v131_import.py backend/app/
cp /tmp/test_erw_v131.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.1 source-backed scientific figures and Word upload\nfrom app.erw_v131 import router as erw_v131_router\nfrom app.erw_v131_import import router as erw_v131_import_router\napp.include_router(erw_v131_router)\napp.include_router(erw_v131_import_router)\n"
if "from app.erw_v131 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3.1 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v131.py backend/app/erw_v131_import.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw131 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw131 -c 'from app.erw_v131 import build_page; print("Composed page bytes:",len(build_page()))'
```

Confirm the original container mounted `/opt/sustainable-catalyst/workbench/data:/data` as read/write before deploying. Validate compose config without displaying secrets:

```bash
cat > compose.erw131.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw131
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw131.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw131.yml up -d --no-build workbench
for i in $(seq 1 24); do
  state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $state"
  [ "$state" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.1/status; echo
curl -s -o /dev/null -w 'Composer HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.1/report
```

## Browser verification
From Mac with the existing SSH tunnel, open `http://127.0.0.1:18088/erw/v1.3.1/report`; sign in with Sustainable Catalyst account; select Wexford project; upload a copy of your completed .docx manuscript (not the only original); confirm section import and save a **new** draft snapshot. Check export/preview and linked saved 0.6/0.7 source objects. Ensure figure captions and calculations display hypothetical/unverified. Check that original document remains in /data without external publication. Do not mistake a DOCX import for a DOCX export.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw130.yml up -d --no-build --force-recreate workbench
```
Do not remove /data; imported source records remain after rollback.
