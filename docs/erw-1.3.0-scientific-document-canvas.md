# ERW 1.3.0 — Scientific Document Canvas & Rich-Text Authoring Foundation

## Implemented
A substantially improved report composition page at `/erw/v1.3.0/report` with document outline, responsive scholarly editing typography, edit/preview modes, print layout and the same owner-scoped Sustainable Catalyst login, tables, manuscript text, immutable draft snapshots, import-as-text and HTML export from 1.2.2. No new researcher identity, no database migration, no additional publication permissions.

This is a document-canvas **foundation**, not a full rich-text/WYSIWYG editor. Source-linked PDF upload, Harvard citation manager, native DOCX/PDF export, beautifully typeset equations and direct figure embedding are **not implemented**. Print/PDF still invokes browser printing only. A saved research object must exist under the current researcher's identity before figure/table linking. The earlier certification objects remain owned by their original isolated test identities and are not transferred.

## Mac
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.3.0-scientific-document-canvas
git switch feature/erw-1.3.0-scientific-document-canvas
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Continue only after all tests pass:
scp backend/app/erw_v130.py backend/tests/test_erw_v130.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backend first
Do not overwrite the existing session secret, identity database, research database, or enrollment file. Preserve a rollback image. Confirm mounted /data and disk free before build. Avoid destructive Docker prune.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw130-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw122.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v130.py backend/app/
cp /tmp/test_erw_v130.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.0 scientific document canvas\nfrom app.erw_v130 import router as erw_v130_router\napp.include_router(erw_v130_router)\n"
if "from app.erw_v130 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.3 route registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v130.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw130 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw130 -c 'from app.erw_v130 import canvas_page; print("Canvas assembled:",len(canvas_page()))'
```

Once page assembly is successful, confirm your current Compose environment overlays (do **not** lose `SCWB_IDENTITY_ENROLLMENT_KEY` or `SCWB_SESSION_SECRET`). Based on prior 1.2.1 configuration:

```bash
cat > compose.erw130.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw130
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw130.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw130.yml up -d --no-build workbench
for i in $(seq 1 24); do
  state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $state"
  [ "$state" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.0/status; echo
curl -s -o /dev/null -w 'Canvas HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.0/report
```

Then **Mac browser through existing SSH tunnel:** `http://127.0.0.1:18088/erw/v1.3.0/report`. Log in to Sustainable Catalyst, select existing Wexford project, edit abstract, click Document preview, return to Edit, save a draft snapshot, and reopen it. Compare export content to saved manuscript. Keep this login loopback/private; current identity system lacks full MFA/revocation/public SSO hardening.

### Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw122.yml up -d --no-build --force-recreate workbench
```
Never modify or delete `/data`. Rollback uses the preserved 1.2.2 image.

## Next gates
1. Real rich text with safe structured paragraphs, citations and page breaks.
2. Saved-source PDF upload and metadata validation; Harvard references.
3. Scientific research-object-driven SVG equation/figure embedding.
4. Actual editable DOCX and reproducible PDF export.
5. Browser end-to-end and scientific nonverification acceptance.
