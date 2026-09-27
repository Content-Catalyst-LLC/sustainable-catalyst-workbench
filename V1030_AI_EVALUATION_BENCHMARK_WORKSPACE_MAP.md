# v10.3.0 AI Evaluation & Benchmark Workspace Map

```text
v10.0 AI Experiment
      |
v10.1 Model + Dataset Registry
      |
v10.2 Training Result / Registered Model
      |
      v
v10.3 Benchmark Suite
  - evaluation datasets
  - researcher-defined metrics
  - diagnostic slices
  - reproducibility settings
  - explicit baseline
      |
      +--> explicit evaluation execution plan (not authorized automatically)
      |
      v
Immutable Evaluation Results
  - overall metrics
  - dataset metrics
  - slice metrics
  - execution/result provenance
      |
      v
Baseline-relative Comparison
  - per-metric deltas
  - tolerance crossings
  - regression diagnostics
  - no aggregate winner
      |
      +--> Platform Core plan only
```
