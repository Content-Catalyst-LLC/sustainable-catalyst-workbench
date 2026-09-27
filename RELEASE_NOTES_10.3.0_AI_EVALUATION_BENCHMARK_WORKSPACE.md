# Workbench v10.3.0 — AI Evaluation & Benchmark Workspace

Workbench v10.3.0 adds registry-backed, content-addressed AI evaluation and benchmarking on top of v10.0–v10.2.

## Capabilities
- immutable benchmark suite specifications;
- v10.1 registry-backed evaluation datasets and model references;
- researcher-defined metric direction, target, unit, and regression tolerance;
- deterministic seeds, repeats, environment refs, and dependency-lock identity;
- diagnostic dataset and slice metrics;
- immutable model evaluation records;
- explicit evaluation execution plans;
- baseline-relative metric regression detection;
- multi-model comparison without automatic ranking;
- Platform Core evaluation handoff planning.

## Boundaries
A benchmark metric or regression flag is a quantitative diagnostic, not an automatic scientific conclusion. v10.3 does not automatically execute inference, rank models, select a winner, promote a model, approve production deployment, infer scientific validity, or create governed Core objects.
