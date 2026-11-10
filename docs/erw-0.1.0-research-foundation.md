# ERW 0.1.0 — Workbench v14 research foundation

**Scope:** A minimal enhanced-rock-weathering research extension, using existing Workbench v12.2 persistent projects and saved calculations. No database migrations; no new persistence store; no new authentication authority; no CO2-removal prediction.

## Repository reconciliation

- Workbench `backend/app/release.py` identifies v14.0.0; README still mentions v10.4.0 and is stale.
- Existing `v1220` provides session-owned project and calculation storage.
- Existing `v1340` provides research sessions; `v1400` provides calculation workflow composition.
- Existing `v270`, `v290`, `v11150`, and `v11170` cover visualization, documentation, uncertainty, and calculation provenance respectively.
- This release intentionally adds an additive API at `/erw/v0.1.0/` and does not mutate Core/Library/Workspace.
- GitHub source review does not certify production routes; certify with smoke checks below.

## Endpoints

- GET `/erw/v0.1.0/status`: extension identity.
- GET `/erw/v0.1.0/template`: source-linked hypothetical Wexford project specification.
- POST `/erw/v0.1.0/projects` `{"confirmHypothetical":true}`: creates owner-scoped project in existing Workbench storage (requires valid Workbench bearer session).
- POST `/erw/v0.1.0/calculations/mass` `{"projectId":"<id>","areaHa":"100","doseTonnesPerHa":"20"}`: evaluates 2000 t basalt with Decimal arithmetic and stores the result in existing calculation storage.
- GET `/erw/v0.1.0/projects/<id>/package`: JSON research bundle with deterministic content hash; no publication side effects.

## macOS development check

```bash
git clone https://github.com/Content-Catalyst-LLC/sustainable-catalyst-workbench.git
cd sustainable-catalyst-workbench
git fetch origin feature/erw-0.1.0-research-foundation
git switch feature/erw-0.1.0-research-foundation
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r backend/requirements.txt
PYTHONPATH=backend pytest -q backend/tests/test_erw_v010.py
PYTHONPATH=backend uvicorn app.main:app --host 127.0.0.1 --port 8098
```

`curl -fsS http://127.0.0.1:8098/erw/v0.1.0/template` verifies public template. Use an authenticated Workbench session for protected project/create/save/package calls.

## Contabo deployment procedure (stage, then promote)

```bash
ssh catalystadmin@YOUR_CONTABO_HOST
cd /path/to/your/workbench/repository
git fetch origin feature/erw-0.1.0-research-foundation
git switch feature/erw-0.1.0-research-foundation
source backend/.venv/bin/activate  # use your actual virtualenv path
PYTHONPATH=backend pytest -q backend/tests/test_erw_v010.py
# Rebuild/restart Workbench using the existing documented compose/systemd process.
# Do not replace .env, credentials, DB volume, or service definitions.
curl -fsS https://YOUR_WORKBENCH_HOST/erw/v0.1.0/status
```

**Deploy gate:** Verify authentication and owner scoping, 100 ha × 20 t/ha = 2000 tonnes, save/retrieve round trip, package hash stability and unchanged existing Workbench v14 routes before promoting. Roll back to prior Git ref and restart existing service if gates fail.

**Not included:** scientific oxide-capacity calculations, geochemical weathering kinetics, uncertainty distributions, maps, academic figure renderer or DOCX/PDF writer. Those follow in ERW 0.2.0+.
