# Workbench v7.3.0 Data Workspace Object Map

| Object | Canonical reference | Integrity field | Purpose |
|---|---|---|---|
| Workspace | `sc://workbench/data-workspace/<hash>` | `workspaceHash` | Research input context |
| Dataset | `sc://workbench/dataset/<hash>` | `datasetHash` | Bounded inline/reference-first tabular input |
| Variable | `sc://workbench/variable/<hash>` | `variableHash` | Typed scalar/column/derived variable |
| Parameter set | `sc://workbench/parameter-set/<hash>` | `parameterSetHash` | Named bounded parameter collection |
| Parameter | `sc://workbench/parameter/<hash>` | `parameterHash` | Scalar model/analysis parameter |
| Assumption | `sc://workbench/assumption/<hash>` | `assumptionHash` | Declared methodological/model assumption |

Execution binding plans materialize only explicitly declared bindings into a v7.2 orchestrator request. Dataset refs remain reference-first; inline dataset content is never silently injected into a runtime payload.
