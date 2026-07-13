# Workbench v3.8.0 local application

The local application runs the existing Workbench FastAPI service and a small
installable web shell on `http://127.0.0.1:8787/offline/`.

It never binds publicly unless the source is deliberately modified. The
launcher rejects non-loopback hosts.

## Manual launch

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r offline/requirements.txt
python offline/start_local_workbench.py
```

After dependencies have been installed, the application can operate without
Render. A platform-specific wheelhouse can be placed in `offline/wheelhouse`
for installations that must not contact a package index.
