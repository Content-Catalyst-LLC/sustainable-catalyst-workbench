# Workbench v6.14.0 → Platform Core v2.97 Certification Field Map

Core contract: `sc.research.platform-integration-certification.v1`

| Workbench v6.14 phase | Core endpoint | Exact Core data fields |
|---|---|---|
| Create suite | `POST /v1/research/integration-certification/suites` | `suite_key`, `title`, `contract_ref`, `contract_version`, `status`, `required_operations`, `required_capabilities`, `visibility`, `metadata`, `provenance`, `created_by` |
| Register product | `POST /v1/research/integration-certification/products` | `product_key`, `suite_id`, `product_ref`, `product_version`, `runtime_binding_ref`, `declared_capabilities`, `declared_object_types`, `visibility`, `metadata` |
| Register case | `POST /v1/research/integration-certification/cases` | `case_key`, `suite_id`, `operation`, `object_type`, `requirement`, `required`, `expected_evidence`, `visibility`, `metadata` |
| Create run | `POST /v1/research/integration-certification/runs` | `run_key`, `suite_id`, `product_id`, `executed_by`, `environment_ref`, `started_at`, `completed_at`, `status`, `visibility`, `metadata`, `provenance` |
| Record result | `POST /v1/research/integration-certification/case-results` | `run_id`, `case_id`, `status`, `observed_behavior`, `evidence_refs`, `executed_by`, `visibility`, `metadata` |
| Exchange check | `POST /v1/research/integration-certification/exchange-checks` | `run_id`, `source_product_ref`, `target_product_ref`, `exchange_ref`, `object_refs`, `status`, `evidence_refs`, `visibility` |
| Trace check | `POST /v1/research/integration-certification/trace-checks` | `run_id`, `object_ref`, `trace_type`, `expected_refs`, `observed_refs`, `status`, `evidence_refs`, `visibility` |
| Reproduction check | `POST /v1/research/integration-certification/reproduction-checks` | `run_id`, `project_ref`, `state_version_ref`, `reconstruction_plan_ref`, `status`, `evidence_refs`, `notes`, `visibility` |
| Evidence | `POST /v1/research/integration-certification/evidence` | `evidence_key`, `run_id`, `evidence_type`, `evidence_ref`, `content_hash`, `captured_by`, `visibility`, `metadata` |
| Revision | `POST /v1/research/integration-certification/revisions` | `suite_id`, `prior_state`, `revised_state`, `reason`, `created_by` |
| Snapshot | `POST /v1/research/integration-certification/snapshots` | `suite_id`, `provenance`, `created_by` |

Core returns authoritative `suite_id`, `product_id`, `case_id`, and `run_id`. Workbench v6.14 requires these IDs before preparing dependent requests.

Core run reports expose `declared_conformance`; Workbench consumes that value read-only and preserves Core's explicit limitation that conformance is runtime-contract evidence, not scientific-validity or product-quality certification.
