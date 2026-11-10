# Recovery of `backend/app/v10110.py` from the running production image

**Why:** `backend/app/main.py` on `main` imports `app.v10110`, and `app/v10120.py` imports six names
from it, but the file was never committed. `main` could not import or start. The running production
service has the file.

## Source of the recovered file

| Item | Value |
|---|---|
| Host | Contabo `vmi3544820` (read-only inspection, 2026-11-10 UTC) |
| Container | `sc-workbench`, compose project `workbench`, service `workbench`, started 2026-10-30T00:04:29Z, healthy |
| Image | `sc-workbench:uvr-01-3-7`, id/digest `sha256:89f98ee050cf7077e4bae8dd4641a8bd24e31018b94bb67efd54adc1d4a76f7f`, amd64, created 2026-10-30T00:02:09Z, no OCI labels |
| Layer that added the file | `COPY . .` (5.74 MB), built 2026-10-19 |
| Container drift | `docker diff sc-workbench` lists only `A /data` (bind mount). `/app` equals the image |
| Extraction | `docker cp sc-workbench:/app -` streamed as tar to an isolated local directory. No exec, restart or write in the container |
| `app/v10110.py` sha256 | `fbd98adb83e0e851c66ef5ddb74960a2897cef8b223f9e2730a5c4dfd77af25b` (same in the container and locally; committed byte-identical) |
| `tests/test_reproducible_computational_package_v10110.py` sha256 | `a074549f7d1f74077ee27b4ac0c5fd4d7fe88041358a22ab42ce8a55886c22ea` (committed byte-identical, then version asserts updated in a separate commit) |

## Comparison with repository history

- No commit on any branch contains this blob. `fix/workbench-v10110-reproducibility`
  (and `pi/baseline-1.0-workbench`) has a different 193-line reconstruction (`ac4b2255…`) with
  different schema names. It is not the deployed module and is not used here.
- `release.py` (14.0.0), `v10100.py`, `v10102.py`, `v10120.py` and `v510.py` are byte-identical
  between `main` and production. The recovered module's imports exist with matching signatures, and it
  exports everything `v10120.py` imports.
- The module reports `VERSION = APP_VERSION` (14.0.0). Nothing reverts the application to 10.11.0.

## Review

No credentials, environment reads, file paths, hosts, subprocesses or network I/O. Its routes are
`GET /v10110/status`, `GET /computational-packages/environment`, and
`POST /computational-packages/{build,replay,verify}`. The POST routes execute calculations through
the existing v10.10 engine, with the same posture as other Workbench compute routes (no auth at this
layer).

## Production is not `main`

Production's `/app` is `main` plus `graph_svg.py` (UVR-01.3.7, draft PR #36), the ERW modules from
draft branches (35 `erw_*.py`, `feature/erw-1.3.9.0-unified-report` and later), and a matching
`main.py`, `requirements.txt` (`python-docx`, `reportlab`), and this file. An image built from `main`
does **not** include the ERW or UVR SVG endpoints that production serves. This recovery adds only
`v10110.py`; the other drift is recorded, not merged.
