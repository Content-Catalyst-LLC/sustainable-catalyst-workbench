# v8.4.0 Interactive Execution Console Map

```text
v8.2 Research Project
        ↓
Prepare Job
        ↓
prepared → queued → explicit run → running → completed/failed
   ↓        ↓
 cancel   cancel
        ↓
Persisted request/result hashes + lifecycle history
        ↓
Inspect / Monitor / Compare
        ↓
Optional two-phase Platform Core plan
```

Supported runtime kinds: unified, solver, simulation, engineering, design-space, workflow, notebook.

The console coordinates existing bounded runtimes; it does not replace them and does not authorize hidden execution, arbitrary code, shell commands, automatic Core writes, scientific validity certification, or running-job preemption.
