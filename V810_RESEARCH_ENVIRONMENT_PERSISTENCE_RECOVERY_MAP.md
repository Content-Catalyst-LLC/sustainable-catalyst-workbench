# v8.1.0 Research Environment Persistence & Recovery Map

```text
v8.0 unified research environment
        ↓
 atomic save + optimistic revision check
        ↓
 append-only revision history
        ↓
 immutable checkpoints
        ↓
 integrity-validated recovery plan
        ↓
 recovery creates NEW revision
        ↓
 resumable unified research environment
```

The persistence layer stores state only. Scientific execution and Platform Core dispatch remain explicit responsibilities of their existing runtimes.
