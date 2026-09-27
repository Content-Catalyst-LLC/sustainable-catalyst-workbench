# Workbench v10.2.0 — Training & Fine-Tuning Experiment Runtime Map

```text
v10.0 AI Engineering Experiment
          │
          ▼
v10.1 Registry Binding
   ┌──────┴────────┐
   │               │
Base Model      Dataset Versions
   │               │
   └──────┬────────┘
          ▼
v10.2 Training Run Specification
   ├── Fine-tuning method
   ├── Hyperparameters + deterministic seed
   ├── Environment / adapter / dependency lock
   ├── Evaluation schedule
   ├── Checkpoint policy
   └── Resource budget
          │
          ▼
Explicit Execution Plan (authorized=false)
          │
          ├── append-only progress events
          ├── evaluation metrics
          └── checkpoint lineage
          │
          ▼
Immutable Training Result
          │
          ├── Derived Model Registry Plan → v10.1 registry
          └── Platform Core Plan → governed research/evidence layer
```

Workbench owns AI-engineering execution contracts and training provenance. Platform Core remains authoritative for governed research/evidence semantics. A completed training run is not automatically a preferred or scientifically valid model.
