# Workbench v8.1.0 — Research Environment Persistence & Recovery

v8.1.0 makes the v8 unified computational research environment durable. It adds an atomic file-backed persistence store, optimistic current-revision checks, append-only revision records, immutable checkpoints, revision/checkpoint recovery planning, and non-destructive recovery that creates a new revision. The default persistent store is `/data/research-environments`, mounted from the Workbench runtime `./data` directory.

Recovery never launches scientific computation, notebook replay, workflow execution, or Platform Core dispatch. Stored revisions and checkpoints are content-addressed and integrity-validated before use. No database migration is required.
