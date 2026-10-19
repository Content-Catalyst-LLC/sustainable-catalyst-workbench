# WI-01 — Wexford Research Recovery Baseline

Status: evidence-collection candidate; **not deployed**. Source assets remain private.

Observed on Contabo 2026-10-19: sc-workbench healthy (sustainable-catalyst-workbench:14.0.0-erw13811); Lab and Platform Core healthy. Workbench persistent mount /opt/sustainable-catalyst/workbench/data -> /data. Project baf85d6f-8821-451f-87f6-5a90ccfd5f56. Observed one PDF and four Word files in owner-scoped paths; do not infer contents or which manuscript is newest. SQLite files: workbench-v12.sqlite3, scwb-identity-v121.sqlite3, erw010-predeploy.sqlite3.

Workspace source baseline v3.84.1 at b0f1122, production Workspace baseline deferred. PostgreSQL owner-isolation check pending. Do not mix Workspace and Workbench release numbers.

Authority: Workbench owns ERW documents and calculations; Lab owns scientific methods; Workspace owns its persistent research state; Core owns canonical cross-product governance; Library owns its sources. All handoffs are untested until verified.

Acceptance gates:
1. Inventory owner-scoped source and document paths without altering files.
2. Record SHA-256 checksums; report missing and inaccessible files.
3. Independently perform a consistent SQLite online backup, securely store it outside live data, and verify restore integrity; raw file hash is not a backup.
4. Open the DOCX revisions before determining the current manuscript.
5. Validate authenticated cross-product APIs before promoting any integration claim.
6. Keep all private manuscript drafts and PDF sources out of public GitHub.
7. No service restarts, migrations, production writes, deletion or publication in WI-01.

The complete WI-01 inventory script, tests, and manifest template are delivered as a separate ZIP artifact in the build handoff. Nothing in this branch should be deployed before review.