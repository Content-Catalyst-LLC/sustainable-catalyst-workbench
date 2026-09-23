# v7.12.0 Reproducible Experiment & Engineering Package Map

```text
Datasets / Parameters / Assumptions
Notebooks / Workflow Graphs
Executions / Solvers / Simulations / Engineering / Optimization
V&V Evidence / Visual Workspaces
Environment / Artifacts / Lineage
                 ↓
      v7.12 Reproducible Package
                 ↓
  Content-addressed Component Manifest
                 ↓
       Integrity Manifest + Hashes
                 ↓
       Replay Plan / Export Plan
                 ↓
 Platform Core sc.research.reproducible-package.v1
```

The runtime is reference-preserving and content-addressed. Required external components must declare a content hash. Embedded components are re-hashed and verified. No replay, filesystem export, Core dispatch, or scientific certification is automatic.
