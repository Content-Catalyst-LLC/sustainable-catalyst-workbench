# Workbench v6.0.0 Security Boundary

The unified project layer is orchestration and record composition only.

It does not authorize:

- Python `eval` or `exec`;
- shell or subprocess execution;
- remote-shell access;
- automatic publication;
- automatic model certification;
- automatic hardware programming;
- automatic bitstream generation/loading;
- automatic external-service actions; or
- destructive project synchronization.

Payloads are restricted to bounded JSON-compatible values. Shared variable names are restricted identifiers. Project, provenance, history, export, and handoff records are content-hashed for reproducibility and integrity inspection.
