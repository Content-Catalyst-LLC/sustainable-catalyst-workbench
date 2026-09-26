# Workbench v10.1.0 — Model & Dataset Registry Map

```text
Scientific AI Engineering Runtime (v10.0)
        │
        ├── Model Registry
        │     ├── model key + immutable version label
        │     ├── provider / model ID / task
        │     ├── artifact hash or source revision
        │     ├── license + provenance
        │     ├── compatibility metadata
        │     └── neutral evaluation state
        │
        ├── Dataset Registry
        │     ├── dataset key + immutable version label
        │     ├── SHA-256 dataset identity
        │     ├── format / schema / splits
        │     ├── license + provenance
        │     ├── compatibility metadata
        │     └── neutral evaluation state
        │
        ├── Registry Search / Version Listing
        │
        └── Immutable Experiment Registry Binding
              ├── v10 experiment hash
              ├── model record hash
              ├── dataset record hashes by role
              ├── identity/lineage verification
              └── Platform Core plan-only handoff
```

Registry versions are append-only/content-addressed. v10.1 does not auto-download, auto-execute, auto-select a preferred version, mutate experiments, infer scientific validity, or automatically dispatch to Platform Core.
