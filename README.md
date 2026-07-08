# Sustainable Catalyst Workbench v0.4.2

A compact, backend-first analytical Workbench for Sustainable Catalyst.

Version 0.4.2 corrects the Research Library integration approach:

- The Research Library remains compact, elegant, and pathway-centered.
- The Workbench appears as one small question-and-tool interface, not a giant map.
- Calculators run through a real Python/FastAPI analytics backend.
- R, Julia, Haskell, and C++ are supported as optional specialist bridges.
- Detailed SVG graphs are generated server-side and returned to WordPress.
- AI is scope-gated to the Sustainable Catalyst knowledge map and can use either a backend `.env` key or an optional encrypted WordPress-managed provider key for testing.

## Quick local backend start

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8088
```

## WordPress shortcodes

```text
[sc_workbench]
[sc_workbench_compact]
[sc_workbench topic="research-library"]
[sc_workbench_pathways]
```

## Recommended Research Library integration

Use only the compact section in `research-library/research-library-compact-workbench-section.html`. Do not paste a full topic map into the Research Library page.

## Security note

Best practice is to store provider keys on the backend in `.env`. Version 0.4.2 also supports a WordPress-managed provider key because the site owner requested it. The plugin encrypts the key before storage using WordPress salts when OpenSSL is available, but backend `.env` is still the preferred production approach.


### v0.4.2 Visual Analytics

The compact Workbench now includes a dedicated **Visualize** tab alongside Ask, Calculators, and Pathways. Visualizations are rendered by the Python analytics backend as SVG output and returned to WordPress. The included Visual Analytics Studio supports bar, line, scatter, histogram, and box-plot views with summary diagnostics.
