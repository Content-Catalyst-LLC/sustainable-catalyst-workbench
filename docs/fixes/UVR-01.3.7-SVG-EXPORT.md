# UVR-01.3.7 — recovered server export and display precision

Production exposes an authenticated SVG endpoint absent from Git history at UVR #35 head `17118f0`. Read-only inspection found `/app/app/graph_svg.py` and the extra route in `v1350.py` in image `sha256:d62871ffa9b2acf5a6b1e87ecc0fdc3bea7a7d6905caaf454a3c3bb591c7bbdb` (`sc-workbench:uvr-01-3-5-candidate`). Source hashes before recovery:

- `v1350.py`: `84117047772d740e477a9fbff059cd579dec99550e5a0af95135b8f28bf8d2d8`
- `graph_svg.py`: `abe80e1ddfdb71b2cb7a288804f9f6c5841df18c0c4ec05ba03e0aed933278ad`

No source-file writable-layer changes were reported. No source revision label or Git checkout identifies the originating commit. This is recovered image source, not a claim to know its original build revision. The recovery commit is separate from the numerical correction. Only code was copied; no credentials, research data or deployment configuration.

The exported y-range previously expanded only exactly equal extrema. The 401-sample identity `sin(x)**2 + cos(x)**2` contains binary64 values from `0.9999999999999998` to `1.0000000000000002`; autoscaling amplified that spread to 410 px. Corrected export spread is 0.0 px at two-decimal SVG coordinate precision, with all original values retained.

Browser and JS report utilities share `display-range.mjs`. Python uses the same formula, tested against shared fixtures and normalized browser SVG point geometry. Noise threshold is `32 * epsilon * max(abs(min),abs(max))`; near-constant display span is `max(1e-12,abs(center)*0.2)`. This is a display policy, not a scientific uncertainty estimate. A floor is deliberately absent from the noise threshold to preserve real variation at `1e-30`. No sample replacement, storage mutation or symbolic simplification was added.

Authentication, owner lookup, source/render hashes, XML escaping and response security headers are recovered unchanged. Core already supplies renderer/specification and provenance contracts but explicitly does not draw SVG or calculate visualization scales; this fix uses existing Workbench export code.

## Validation

From repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
PYTHONPATH=backend .venv/bin/python -m pytest -q backend/tests/test_uvr_svg_export_precision.py
node --test standalone-app/tests/uvr-*.test.*
git diff --check
```

Results on development Mac and isolated Raspberry Pi worktree: **18 Python tests passed; 58 Node tests passed**. Tests use synthetic owned projects and temporary SQLite. Coverage includes constants/noise, true small and tiny variation, cross-language geometry, deterministic hashes, input preservation, invalid samples/identity, XML safety, authenticated route, invalid/missing session, foreign owner 404, security headers and unchanged saved graph. Existing Pydantic schema-name warning remains; local Mac also reports the installed httpx/TestClient deprecation. No production tests involving research data were run.

New CI runs the focused Python suite and existing UVR Node suites. CI success must be checked on the final PR SHA separately; local/Pi results are not CI claims.

## Scope and release boundary

Single-view numerical parity is verified. Existing export flattens multiple views into one chart while the browser displays separate cards; annotations, markers, viewport/scales and linked multi-panel fidelity need a separate reviewed contract change. Do not label this patch universal browser/export feature equivalence.

The Pi is development/testing/sync/backup only. No production files, DB, services or configuration were changed. This source recovery does not reconcile every other addition in the production image: a full candidate source manifest is required before building a replacement, to avoid losing unmerged ERW features. Do not deploy a main-based image just because its version is also 14.0.0.

After approval, deploy to Contabo only, pairing the reviewed backend with matching frontend `math-renderer.js` and its new `display-range.mjs` import. Preserve previous image by immutable ID and previous asset set; retain current data mount/configuration. Validate static import delivery and synthetic graph/export/auth behavior. Rollback restores the previous image and frontend pair; no schema migration or data rollback is introduced. Deployment, merge and rollback remain separately approval-gated.
