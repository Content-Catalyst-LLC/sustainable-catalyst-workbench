# ERW 0.2.0 — Geochemical Feedstock & Stoichiometry Engine

Extends ERW 0.1.0 on Workbench v14 without changing version, existing store, or routes. The four-oxide formula estimates **gross idealized carbonic-acid charge-balance capacity**, *not verified carbon dioxide removal*; uncorrected sulfate, phosphate, carbonate phases and incomplete assays are explicitly flagged. No false attribution of example composition to Cunningham or other sources.

## Method and scientific caveats
- Clarkson et al. (2024), https://doi.org/10.3389/fclim.2024.1345224 : review of modified Steinour maximum feedstock estimates and MRV issues.
- Isometric Feedstock Characterization v1.2, https://registry.isometric.com/module/rock-and-mineral-feedstock-characterization/1.2 : more complete adjusted Steinour equation (including corrections).
- This implementation computes **uncorrected, exploratory gross** capacity from CaO, MgO, Na2O, K2O only, each expressed as bulk feedstock wt%. It does **not** implement Isometric's full equation and is not crediting compliant.
- Requires explicit sourceKind, sampleId and sourceReference. Non-target oxides contribute to total assay mass but not computed capacity. Assay completeness and acid/carbonate correction status are emitted.
- Actual basalt weathering, field MRV, carbonic vs nitric/sulfuric acid partition, downstream CO2 leakage, carbonate correction, and life-cycle emissions are all outside this release.

## New API
GET /erw/v0.2.0/status
GET /erw/v0.2.0/method
POST /erw/v0.2.0/potential (stateless exploratory calculation)
POST /erw/v0.2.0/projects/potential (existing authenticated, owner-scoped Workbench project; persisted into existing calculation store)

## macOS test
```bash
cd ~/Downloads/sustainable-catalyst-workbench
git fetch origin feature/erw-0.2.0-geochemical-stoichiometry
git switch feature/erw-0.2.0-geochemical-stoichiometry
source .venv/bin/activate
PYTHONPATH=backend python -m pytest -o addopts="" -q backend/tests/test_erw_v010.py backend/tests/test_erw_v020.py
```
Test request (synthetic fixture only):
```bash
curl -fsS http://127.0.0.1:8098/erw/v0.2.0/potential -H 'Content-Type: application/json' -d '{"rockTonnes":"2000","assay":{"feedstockId":"BASALT-DEMO","sampleId":"SYN-001","compositionWtPct":{"CaO":"10","MgO":"5","Na2O":"3","K2O":"1"},"sourceKind":"hypothetical","sourceReference":"Synthetic test fixture; not real basalt assay","carbonateStatus":"unknown","sulfatePhosphateStatus":"unknown"}}'
```

## Contabo staged deployment
Existing deployed directory is /opt/sustainable-catalyst/workbench (not Git), Docker Compose context ./backend, container sc-workbench, port localhost:8088, /data persistent.
1. On Mac, scp only `backend/app/erw_v020.py` and `backend/tests/test_erw_v020.py` to Contabo /tmp.
2. On Contabo, back up backend and compose, copy those two files into backend/app and backend/tests. Add *exactly one* `from app.erw_v020 import router as erw_v020_router; app.include_router(erw_v020_router)` at the end of existing backend/app/main.py.
3. Verify Python compile, build uniquely tagged image `sustainable-catalyst-workbench:14.0.0-erw020`, verify import and status in disposable container.
4. Create additive `compose.erw020.yml` with `services: {workbench: {image: sustainable-catalyst-workbench:14.0.0-erw020}}`; run docker compose with both files, --no-build.
5. Verify existing /health, ERW v0.1.0/status, ERW v0.2.0/status and method. Execute actual bearer-token project save and package retrieval before certification.
6. Roll back with previous known healthy `compose.yml + compose.erw010.yml` using `--no-build`, without touching /data. No schema migration.
Do not print .env or session bearer tokens in logs.
