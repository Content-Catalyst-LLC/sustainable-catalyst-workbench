# Sustainable Catalyst Workbench v6.14.0
## Platform Integration Certification

Workbench v6.14.0 closes the v6.x Platform Core integration sequence by adding a deterministic certification layer over the integrations introduced in v6.4–v6.13.

The release targets Platform Core v2.97's `sc.research.platform-integration-certification.v1` contract. Workbench can now prepare caller-reviewed Core requests for certification suites, registered products, conformance cases, conformance runs, case results, exchange checks, trace checks, reproduction checks, evidence, revisions, and immutable certification snapshots.

### Local conformance report

`GET /integration/core/certification/report/local` assembles deterministic Workbench-side evidence across:

- Platform Core connectivity foundation
- unified runtime contract adapter
- unified research project/session bridge
- computation/execution lineage
- scenario and uncertainty runtime
- visual reasoning runtime adapter
- predictive intelligence runtime
- forensic quantitative reconstruction runtime
- research state, reproduction and snapshots
- Core-aware Workbench experience
- integration safety boundaries

The local report is descriptive evidence. It does not write to Core and does not represent scientific or product-quality certification.

### Core certification lifecycle

v6.14 implements an explicit Core-ID lifecycle:

1. prepare a certification suite request;
2. Core persists the suite and returns its authoritative suite ID;
3. prepare Workbench product and conformance-case registrations against that suite ID;
4. Core returns authoritative product/case IDs;
5. prepare a conformance run against Core-issued suite/product IDs;
6. Core returns the run ID;
7. prepare case results and exchange/trace/reproduction evidence against Core-issued run/case IDs;
8. consume Core run reports and suite bundles read-only;
9. prepare revision and immutable certification-snapshot requests.

Workbench never fabricates Core certification IDs and never dispatches or persists these requests automatically.

### Certification scope

The word certification in this release means **declared platform/runtime contract conformance evidence only**. v6.14 does not:

- certify scientific validity;
- certify product quality;
- authorize products;
- rank products;
- infer missing evidence;
- infer reproducibility;
- auto-resolve failed conformance cases;
- invoke products automatically; or
- determine truth.

### WordPress

Adds:

- `[sc_workbench_platform_certification_status]`
- `/wp-json/sc-workbench/v1/platform-certification/status`

The release gate retains the permanent Workbench bootstrap regression guard: any `SCWB_DIR` reference in the main plugin bootstrap fails release validation.

### Database

No Workbench database migration is required.
