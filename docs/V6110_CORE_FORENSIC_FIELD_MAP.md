# v6.11 Core Open Forensics field map

| Workbench concern | Platform Core target |
|---|---|
| Quantitative reconstruction state | `GET /v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions` |
| Workbench handoff | `GET /v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/handoff/workbench` |
| External specialist result | `POST /v1/open-forensics/investigations/{investigation_id}/quantitative-handoffs/{handoff_id}/results` |
| Reproduction package | `POST /v1/open-forensics/investigations/{investigation_id}/quantitative-reconstructions/{reconstruction_id}/reproduction-packages` |
| Timeline context | `GET /v1/open-forensics/investigations/{investigation_id}/timeline` |
| Spatial/temporal evidence context | `GET /v1/open-forensics/investigations/{investigation_id}/spatial-temporal-evidence` |
| Competing-hypothesis context | `GET /v1/open-forensics/investigations/{investigation_id}/hypothesis-matrix` |

Workbench sends result bindings with `external_result_ref`, `output_manifest`, descriptive `metrics`, SHA-256 `content_hash`, optional `evidence_item_id`, provenance, and metadata. IDs identifying investigations, reconstructions, handoffs, evidence, and Core lineage executions remain Core-issued.
