# v6.8.0 Scenario & Uncertainty Compute Runtime Integration

## Purpose

Platform Core defines and governs scenario and uncertainty research objects. Workbench executes numerical designs and analyses that Core intentionally does not execute itself.

## Scenario lifecycle

1. Core prepares a scenario compute request and `scenario-compute-input-manifest-v1`.
2. Workbench consumes the request as read-only context.
3. A Workbench-owned numerical method executes against the declared parameters.
4. Workbench emits deterministic result hashes and a v6.7 computation-lineage registration plan.
5. After Core returns a computation execution ID, Workbench can build input/parameter/environment/step/output/verification lineage requests and bind the execution to a v6.6 research session.
6. Workbench can prepare, but never automatically dispatch, Core scenario attempt/model-run/result-binding callbacks.

## Uncertainty runtime

Supported methods are Monte Carlo, Latin hypercube, Sobol design/index analysis, Morris design/elementary-effects analysis, ensemble statistics, and empirical threshold exceedance probability.

Sampling is deterministic for a declared seed. Result manifests identify Workbench as the calculator and explicitly state that Core did not execute the model.

## Security boundary

The v6.8 bridge does not execute arbitrary source code, shell commands, notebooks, or serialized functions supplied by Core. The built-in scenario executor is an explicit affine evaluator over numeric parameter values. More sophisticated Workbench-native model adapters can be added later under the same governed boundary.
