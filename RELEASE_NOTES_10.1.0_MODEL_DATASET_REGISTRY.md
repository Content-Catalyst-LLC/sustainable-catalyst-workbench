# Workbench v10.1.0 — Model & Dataset Registry

Adds immutable, versioned, content-addressed model and dataset records to the v10 Scientific AI Engineering foundation.

## Capabilities
- Immutable model versions with provider/model/task identity, artifact hashes or source revisions, licensing, provenance, compatibility metadata, tags, and neutral evaluation state.
- Immutable dataset versions with SHA-256 data identity, dataset references, formats, schemas, dimensions, split definitions, licensing, provenance, compatibility metadata, tags, and neutral evaluation state.
- Protection against silently reusing the same key/version label for different content.
- Project-scoped listing and filtered registry search.
- Immutable AI-experiment registry bindings that verify model/dataset identity without mutating the v10.0 experiment object.
- Plan-only Platform Core handoff for models, datasets, and experiment bindings.

## Scientific and execution boundaries
The registry does not download models or datasets, execute training or inference, select a preferred model or dataset, declare scientific validity, overwrite immutable versions, mutate existing AI experiments, or automatically persist governed objects into Platform Core.
