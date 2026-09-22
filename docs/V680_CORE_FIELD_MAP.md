# Workbench v6.8.0 — Platform Core Scenario / Uncertainty Field Map

## Scenario request input

Core `ScenarioComputeRequestRecord.input_manifest_json` uses `scenario-compute-input-manifest-v1` with:

- `plan_id`
- `case_id`
- `project_entity_id`
- `model_entity_id`
- `model_version_entity_id`
- `scenario_entity_id`
- `execution_product`
- `parameter_values`
- `scenario_parameter_values`
- `parameter_overrides`
- `expected_outputs`
- `execution_contract`
- `output_contract`
- `case_hash`
- `core_execution`

Workbench consumes these fields without mutating the Core request.

## Scenario completion callbacks

Workbench prepares requests for Core's existing scenario endpoints:

- `POST /v1/scenario-compute/requests/{request_id}/attempts`
- `POST /v1/scenario-compute/requests/{request_id}/bind-run`
- `POST /v1/scenario-compute/requests/{request_id}/results`

The callback planner always records `executor_product=workbench` and `executed_by_core=false`.

## Uncertainty method compatibility

Workbench v6.8 mirrors Core's supported method names and output vocabulary:

- `monte-carlo`
- `latin-hypercube`
- `sobol-design`
- `morris-design`
- Sobol `A`, `B`, and `AB` output-vector analysis
- Morris trajectory elementary-effects analysis
- ensemble statistics with normalized weights
- empirical threshold exceedance probability

Numerical fields are computed by Workbench and explicitly marked as not computed by Core.
