# v6.9.0 Core Visual Field Map

Workbench targets the following existing Platform Core visual contracts:

| Workbench v6.9 output | Platform Core surface | Contract / path |
|---|---|---|
| visual research manifest | Visual Reasoning Object Model | `/v1/visual-reasoning/objects` |
| semantic elements/layers | Visual Reasoning Object Model | `/v1/visual-reasoning/objects/{visual_entity_id}/*` |
| renderer-neutral scene | Visual Runtime & Scene Graph | `sc.visual-runtime.scene.v1` |
| scene composition | Interactive Renderer & View Composition | `sc.visual-runtime.composition.v1` |
| analytical grammar | Analytical Visualization Grammar | `sc.visual-runtime.grammar.v1` |
| coordinated state | Linked Views / Visual Query | `sc.visual-runtime.linked-views.v1`, `sc.visual-runtime.visual-query.v1` |
| unified visual workspace | Unified Visual Reasoning | `sc.visual-runtime.unified-reasoning.v1` |
| Workbench product binding | Cross-Product Visual Runtime Integration | `sc.visual-runtime.cross-product-integration.v1` |

Canonical IDs are always issued by Platform Core. Workbench uses those IDs only after they are returned by Core.
