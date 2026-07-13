# Workbench v2.7.0 Security and Integrity Boundary

- Visualization and dashboard calculations run in the browser by default.
- Saved records remain in browser storage unless the user exports them.
- The local Go Runner binds only to `127.0.0.1:8787`.
- Runner access requires a one-time pairing code and an origin-bound bearer token.
- Visualization discovery reports only allowlisted executable availability and version output.
- The runner exposes no arbitrary shell endpoint.
- PNG export is produced in the browser from the generated SVG.
- User-supplied titles, labels, states, and table values are escaped before HTML/SVG rendering.
- Large datasets are capped or summarized in exported interface records to reduce browser and output risk.
