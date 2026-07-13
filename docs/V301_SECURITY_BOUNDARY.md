# Workbench v3.0.1 Security and Reliability Boundary

This patch changes public WordPress activation, routing, diagnostics, and backend audit records. It does not broaden local execution privileges.

- The canonical shortcode renders only registered Workbench modules.
- Module exceptions are converted into visible interface errors rather than exposed as blank panels.
- Diagnostics report availability and state; they do not expose secrets, private project data, or arbitrary filesystem information.
- The WordPress production-status endpoint reports shortcode registration only.
- The FastAPI audit routes evaluate user-supplied status records and do not execute code.
- The existing Go Runner remains loopback-only, paired, origin-bound, and allowlisted.
- No general shell endpoint is introduced.
