# ERW 1.3.6 — Manuscript Structure & Workspace Navigation

**Draft development release, not yet tested on Mac or deployed.** Based on healthy ERW 1.3.5. All changes to a loaded report are in browser editor state until the researcher explicitly saves a NEW immutable snapshot. Existing records and original DOCX files are retained.

## Includes
- Explicit Word intake mode: replace an **empty** starter template or append imported content. Never silently discard populated sections. A failed replacement may already preserve the newly uploaded DOCX as an immutable source, but does not modify the active manuscript.
- Preview empty manuscript sections and explicitly apply cleanup in the current editor only. Populated sections are never automatically discarded, including headings with duplicate names.
- Transfer imported Word Bibliography into the dedicated bibliography field when empty, avoiding a second bibliography section. The researcher must verify its content and references; no automatic Harvard validation.
- In-page navigation to manuscript, Word import, claim evidence, audit and DOCX/PDF export. Stable alias `/erw/report` redirects to `/erw/v1.3.6/report`.
- Correct obsolete 1.3.0 availability banner.
- **Limits:** Word tables, figures, complex styles and native equations are not faithfully recovered. Human review and publication gates remain. Authors are not inferred automatically; enter and save them explicitly. Historical snapshots are not rewritten, and imported references require review.

## Mac
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git status --short
git fetch origin feature/erw-1.3.6-manuscript-structure-workspace
git switch feature/erw-1.3.6-manuscript-structure-workspace
source .venv/bin/activate
python -m py_compile backend/app/erw_v136.py backend/tests/test_erw_v136.py
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Only after every test passes:
scp backend/app/erw_v136.py backend/tests/test_erw_v136.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo — backend first, preserve /data
```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw136-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml "$BACKUP/"
for f in compose.erw121-identity.yml compose.erw135.yml; do
  [ ! -f "$f" ] || cp -a "$f" "$BACKUP/"
done
cp /tmp/erw_v136.py backend/app/
cp /tmp/test_erw_v136.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.3.6 manuscript structure and unified report entry\nfrom app.erw_v136 import router as erw_v136_router\napp.include_router(erw_v136_router)\n"
if "from app.erw_v136 import router" not in s:p.write_text(s.rstrip()+reg)
print("1.3.6 routes registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v136.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw136 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw136 -c 'from app.erw_v136 import build_page; print("Editor assembled:",len(build_page()))'
```

Stop if image smoke test fails. Retain `compose.erw135.yml` and the existing `/data` bind mount.

```bash
cat > compose.erw136.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw136
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw136.yml up -d --no-build workbench
for i in $(seq 1 24); do
  status=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $status"
  [ "$status" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.3.6/status; echo
curl -sS -o /dev/null -w 'Workspace HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.3.6/report
curl -sSI http://127.0.0.1:8088/erw/report | head -n 8
```

## Browser acceptance
Mac tunnel: `ssh -N -L 18088:127.0.0.1:8088 catalystadmin@94.72.113.77`. Use an alternate local port 18089 if 18088 is occupied.

Open `http://127.0.0.1:18088/erw/report`. Authenticate and select original Wexford project. Restore an existing saved manuscript, preview which sections are empty; only apply the cleanup after review. Confirm populated sections remain; correct Authors and Bibliography; explicitly Save draft snapshot and inspect the new version. Run Publication Readiness Audit again; exported Word/PDF should be independently checked. For a new DOCX upload, choose replace-empty only on an empty starter template; choose append if the current manuscript has content.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw135.yml up -d --no-build --force-recreate workbench
```
Keep /data and previous image intact.
