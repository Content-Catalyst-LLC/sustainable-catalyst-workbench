# Workbench v10.2.0 — Training & Fine-Tuning Experiment Runtime

v10.2.0 adds the first explicit AI model-training lifecycle to Sustainable Catalyst Workbench. Training runs are content-addressed research objects that resolve a v10.0 AI experiment against v10.1 immutable model/dataset registry records before training can be prepared.

## Capabilities

- Registry-backed training and fine-tuning run specifications
- Full fine-tuning, supervised fine-tuning, continued pretraining, LoRA, QLoRA, adapters, prompt tuning, linear probes, and custom methods
- Deterministic seed/hyperparameter manifests
- Runtime/environment identity and dependency-lock hashes
- Evaluation schedules and checkpoint policies
- CPU/GPU/wall-time/cost/checkpoint budgets
- Explicit, non-authorized execution plans for downstream runtime adapters
- Append-only progress/evaluation/checkpoint event lineage
- Immutable training results linked to external Workbench jobs/results
- Explicit derived-model registration plans back into the v10.1 registry
- Platform Core handoff plans for training runs/results

## Research boundaries

The release does not automatically download models/datasets, execute training, call external providers, run arbitrary code, promote checkpoints or trained models, select a preferred model, infer scientific validity, or persist governed Platform Core objects.
