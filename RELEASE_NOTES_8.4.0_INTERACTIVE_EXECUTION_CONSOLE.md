# Workbench v8.4.0 — Interactive Execution Console

v8.4.0 adds a durable project-scoped execution console above the certified v7 scientific runtimes and v8 project/persistence layers.

## Capabilities
- Prepare, queue, inspect, explicitly run, monitor, and cancel pending jobs.
- Dispatch only to allow-listed Workbench runtimes: unified execution, numerical solver, simulation, engineering, design-space optimization, workflow graph, and computational notebook.
- Persist job request/result hashes, project/environment anchors, lifecycle timestamps, revision history, and integrity hashes under the existing persistent `/data` store.
- Compare completed jobs without selecting a winner or inventing a scientific interpretation.
- Prepare two-phase Platform Core project/session binding plans without automatic dispatch or persistence.

## Execution boundary
There is no hidden background worker in this release. Scientific execution happens synchronously only when the explicit job run endpoint is called. Pending jobs may be cancelled; running-job preemption is not claimed. Arbitrary code and shell execution remain prohibited.

## Persistence
v8.1 remains authoritative for environment revision history. v8.2 remains authoritative for project state. v8.4 records execution-console jobs anchored to those project/environment identities.

No database migration is required.
