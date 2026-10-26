# Workbench Development Status

Last verified: 2026-10-26

## Working

- ARM64 Docker image build
- FastAPI startup
- Local HTTP API
- Exact scientific calculation smoke test
- Reproducible package build
- Deterministic replay verification
- Package tamper rejection
- V10 certification and regression suite: 13 passing

## Known warning

Pydantic warns that ReplayEnvelope.schema shadows
a BaseModel attribute in v11.17.

This warning did not fail the recovery-specific tests.

## Not yet certified

- Full Workbench scientific feature suite
- Persistent development data workflows
- Integration with Workspace and Research Lab
- Complete backward compatibility of reconstructed v10.11
- Production deployment

## Preservation

Recovery commit: 58ef258

Branch: fix/workbench-v10110-reproducibility

The Pi repair must be pushed to an appropriate private
GitHub branch before off-device preservation is complete.
