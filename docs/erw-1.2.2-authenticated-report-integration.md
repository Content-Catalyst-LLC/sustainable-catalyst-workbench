# ERW 1.2.2 — Authenticated Research Workspace & Report Integration

Stacked on 1.2.1. Sustainable Catalyst account login is used directly inside the ERW report editor, retaining the signed bearer token **in page memory only** (no storage, URL parameter or visible token field). After login, the editor queries owner-scoped projects and chooses the user's Wexford project based on the recorded onboarding metadata. No ownership migration takes place.

## What this build adds
- New `GET /erw/v1.2.2/report`: sign in and continue straight into the existing research report editor.
- New `GET /erw/v1.2.2/my/research-context`: authenticated Sustainable Catalyst account's projects only.
- New `GET /erw/v1.2.2/projects/{project_id}/report-drafts`: owner-scoped, digest-consistent v1.2.0 report snapshots.
- Open previously saved report snapshots (creates new append-only snapshot on next Save); in-memory import of pasted manuscript as an editable new section.
- Retains existing project-scoped source, table, report and export operations, and hypothetical/unverified scientific safeguards.
- Sign out of tab clears the bearer token and project selectors.

## Known limitations
This is a direct **same-origin account login in the ERW report page**, not SSO for the other Sustainable Catalyst products. Token expires after one hour. There is no persisted login, refresh/revocation flow, MFA, password reset or protected public credential login deployment. Keep behind SSH tunnel or a properly secured access gateway. Browser/network transport should be HTTPS outside loopback. Account enrollment remains invitation-only. Draft reopen relies on the existing ERW v1.2.0 source integrity check. Imported manuscript is a text section, **not automatic styled DOCX or PDF import**. Visualization/equation inserts remain provenance placeholders unless existing SVGs are separately exported. 1.2.2 does **not** provide native DOCX or publication-quality composite figures. Those are explicit next acceptance gates.

## Mac instructions
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.2.2-authenticated-report-integration
git switch feature/erw-1.2.2-authenticated-report-integration
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# After PASS:
scp backend/app/erw_v122.py backend/tests/test_erw_v122.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo deployment (requires 1.2.1 healthy)

Check backup/disk capacity first. Do not output or alter `SCWB_SESSION_SECRET` or enrollment key. Do not change database ownership or delete volumes.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
docker inspect sc-workbench --format '{{json .Mounts}}'
df -h /
BACKUP="$HOME/workbench-erw122-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw121.yml compose.erw121-identity.yml "$BACKUP/"
cp /tmp/erw_v122.py backend/app/
cp /tmp/test_erw_v122.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path("backend/app/main.py")
s=p.read_text()
reg="\n# ERW 1.2.2 authenticated report workspace\nfrom app.erw_v122 import router as erw_v122_router\napp.include_router(erw_v122_router)\n"
if "from app.erw_v122 import router" not in s:p.write_text(s.rstrip()+reg)
print("ERW 1.2.2 router registered")
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v122.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw122 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw122 -c 'from app.erw_v122 import build_page; print("Authenticated report page assembled:",len(build_page()))'
```

Only after the page assembles without assertion errors and the existing data/env mounts are verified:

```bash
cat > compose.erw122.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw122
EOF
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw122.yml config --quiet
docker compose -f compose.yml -f compose.erw121-identity.yml -f compose.erw122.yml up -d --no-build workbench
for i in $(seq 1 24); do
  state=$(docker inspect sc-workbench --format '{{.State.Health.Status}}')
  echo "Health: $state"
  [ "$state" = healthy ] && break
  sleep 5
done
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.2.2/status; echo
curl -s -o /dev/null -w 'Report page HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.2.2/report
```

**Browser acceptance** (Mac with existing SSH tunnel): open `http://127.0.0.1:18088/erw/v1.2.2/report`. Sign in with new Sustainable Catalyst account, do **not** use WordPress credentials. Check Wexford project `baf85d6f-8821-451f-87f6-5a90ccfd5f56` auto-selected; load research objects; import manuscript text; save draft snapshot; select/open saved draft; check table save/export. Previously saved certification objects belong to other test users: empty visuals are expected until new objects are generated/imported under your real account. Do not assume model results are already in your new Wexford project.

Security note: sign-out clears in-page bearer state but does not revoke already issued tokens server-side; never present this as full SSO or hardened public login. Production acceptance requires tests and real browser checks.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw121.yml -f compose.erw121-identity.yml up -d --no-build --force-recreate workbench
```
Leave the /data mount untouched.

## Next visual reporting gate
Polished native scientific SVG views from measured or modeled research objects; scenario comparison with uncertainty, pathway/MRV diagrams, typeset equations, legible tables, Wexford report visual composition and real DOCX/PDF export. No verified carbon removal claims.
