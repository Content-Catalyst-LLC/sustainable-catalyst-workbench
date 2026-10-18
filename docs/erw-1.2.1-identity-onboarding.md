# ERW 1.2.1 — Sustainable Catalyst Identity & Research Workspace Onboarding

## Scope and limitations
Sustainable Catalyst–owned account registry independent of WordPress, password-derived hashes with per-account random salt, restricted enrollment key, rate-limited failed logins (per account), signed Workbench sessions using the existing v12.1 session authority, idempotent hypothetical Wexford project creation. All accounts use stable `sc:<UUID>` identifiers and the same v12.2 project ownership service. Login tokens remain in onboarding-tab memory; they are not written to localStorage or copied to URLs.

**Critical limitations:** This is a **restricted initial account foundation**, not a full production identity provider or cross-product SSO. No password reset, MFA, credential recovery, email verification, IP-level rate limiting, account deletion, server-side token revocation, or token handoff to the v1.2.0 report editor. The report editor still requires a separate bearer token input; don't reuse password as token. A long-lived login system should not be publicly exposed until those gates are addressed. Deploy only behind loopback/SSH tunnel or a trusted access layer. The enrollment key must never be pasted into this chat or put in browser URLs. Do not migrate anonymous certification projects across identities or edit their SQLite ownership manually. No existing WordPress account is automatically a Sustainable Catalyst account.

**Scientific and design gate:** The Wexford paper should showcase polished native Sustainable Catalyst scientific figures, equations and tables created from the saved model's actual data (publication-ready typography, crisp SVG, captions, units, colorblind-readable graphics, explicit hypothetical/uncertainty/verification labeling). The v1.2.1 build does **not** implement such a final renderer. Existing v1.1 charting and v1.2 table preview remain preliminary and must be visually validated before report submission. Never substitute AI-generated images for scientific figures or make unverified CDR claims.

## Mac tests
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-1.2.1-sustainable-catalyst-identity-onboarding
git switch feature/erw-1.2.1-sustainable-catalyst-identity-onboarding
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v*.py
# Only continue after PASS:
scp backend/app/erw_v121.py backend/tests/test_erw_v121.py catalystadmin@94.72.113.77:/tmp/
ssh catalystadmin@94.72.113.77
```

## Contabo production staging
Use existing Workbench /data persistent mount. Confirm on server `docker inspect sc-workbench --format '{{json .Mounts}}'` before deploying. **Never start without confirming /data persistence.** Existing v12.1 session secret should be stable; introducing a different secret will invalidate existing signed sessions. If a durable session secret is already configured, preserve it.

```bash
cd /opt/sustainable-catalyst/workbench
docker inspect sc-workbench --format '{{json .Mounts}}'
docker system df
df -h /
BACKUP="$HOME/workbench-erw121-predeploy-$(date +%Y%m%d-%H%M%S)"
mkdir -m 700 -p "$BACKUP"
cp -a backend compose.yml compose.erw120.yml "$BACKUP/"
cp /tmp/erw_v121.py backend/app/
cp /tmp/test_erw_v121.py backend/tests/
python3 - <<'PY'
from pathlib import Path
p=Path('backend/app/main.py')
s=p.read_text()
reg='\n# ERW 1.2.1 standalone identity and onboarding\nfrom app.erw_v121 import router as erw_v121_router\napp.include_router(erw_v121_router)\n'
if 'from app.erw_v121 import router' not in s:p.write_text(s.rstrip()+reg)
print('ERW 1.2.1 route registration present')
PY
python3 -m py_compile backend/app/main.py backend/app/erw_v121.py
docker build -t sustainable-catalyst-workbench:14.0.0-erw121 -f backend/Dockerfile backend
docker run --rm --entrypoint python sustainable-catalyst-workbench:14.0.0-erw121 -c 'from app.erw_v121 import status; print(status())'
```

The identity endpoints require both `SCWB_SESSION_SECRET` (>= 32 characters) and `SCWB_IDENTITY_ENROLLMENT_KEY` (>= 24 characters). Configure these through your existing secure Compose environment/secret injection procedure and protect them with restrictive file permissions. Do not print or log the values. Verify both keys exist without echoing their content; do not overwrite existing signing key. Disable public access to the enrollment route until authentication hardening. The identity database defaults to `/data/scwb-identity-v121.sqlite3` in the existing persistent volume.

When secrets and /data persistence are **confirmed**, complete:

```bash
cat > compose.erw121.yml <<'EOF'
services:
  workbench:
    image: sustainable-catalyst-workbench:14.0.0-erw121
EOF
# NOTE: Compose override above does not configure the required secrets.
# Use your existing protected Compose environment method before proceeding.
docker compose -f compose.yml -f compose.erw121.yml config --quiet
docker compose -f compose.yml -f compose.erw121.yml up -d --no-build workbench
docker inspect sc-workbench --format '{{.Config.Image}} | {{.State.Health.Status}}'
curl -fsS http://127.0.0.1:8088/health; echo
curl -fsS http://127.0.0.1:8088/erw/v1.2.1/status; echo
curl -fsS -o /dev/null -w 'Onboarding HTTP %{http_code}\n' http://127.0.0.1:8088/erw/v1.2.1/onboarding
```

On Mac, leave tunnel open and visit `http://127.0.0.1:18088/erw/v1.2.1/onboarding`. Use a newly created Sustainable Catalyst account (invitation key required). Do not enter your WordPress password. Use the onboarding button to create a new hypothetical Wexford project under your permanent Sustainable Catalyst identity.

## Acceptance gates still pending
All ERW tests pass; healthy backend; persistent /data mount; both secrets configured; restricted enrollment and account login; repeat onboarding remains idempotent; wrong password denied and account locked after five failures; anonymous session cannot onboard; project ownership segregated; old ERW API endpoints and research packages remain intact. Visual quality and full report workflow are a separate acceptance gate.

## Rollback
```bash
cd /opt/sustainable-catalyst/workbench
docker compose -f compose.yml -f compose.erw120.yml up -d --no-build --force-recreate workbench
```
Keep `/data` untouched. Rollback does not migrate identities or old research objects.
