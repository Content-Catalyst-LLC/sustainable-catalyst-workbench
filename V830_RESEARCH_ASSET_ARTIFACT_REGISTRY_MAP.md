# Workbench v8.3.0 — Research Asset & Artifact Registry Map

```text
v8.2 Research Project Workspace
          |
          +--> active persisted environment (v8.1 authority)
          |
          v
v8.3 Project Asset Indexer
          |
          +--> environment components
          +--> execution objects
          +--> explicit external assets
          |
          v
Content-addressed Research Asset Registry
          |
          +--> asset key / type / title
          +--> stable reference
          +--> content hash / asset hash
          +--> tags / media type / size
          +--> environment revision/hash anchor
          +--> provenance / metadata
          +--> append-only asset revision history
          |
          +--> text/type/tag/hash search
          |
          v
Platform Core two-phase object-binding plan
```

The registry is an index, not a second scientific object store. It never rewrites v8.1 environment history or v8.2 project state and does not automatically execute, fetch, publish or dispatch research work.
