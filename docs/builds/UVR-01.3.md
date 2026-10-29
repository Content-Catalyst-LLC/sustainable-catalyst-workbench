# UVR-01.3 — Research Reporting Integration

## Objective
Attach saved Workbench scientific graphs to research report figures, preserving project and research-session ownership, graph identity, caption, source references, and revision metadata. Initial consumers: Wexford ERW and UCD Sustainable Development Metrics research reports.

## Existing capabilities confirmed
Workbench frontend already creates, retrieves, updates, annotates, and renders saved graphs using `/standalone/v1/graph-studio/graphs` and lists them under `/standalone/v1/projects/{project_id}/graphs`. UVR-01.2 verified persistence and access isolation in the Pi development environment.

## UVR-01.3 milestones
1. **Figure reference contract** (started): pure versioned record pointing to an existing graph; reject project and session mismatches; never label graph output scientifically verified merely because it renders.
2. **Authenticated export endpoint** (pending): produce a server-backed figure artifact (prefer SVG + metadata JSON, optionally PNG) from the saved render specification. Enforce graph/project owner, no cross-project links; include source and unit metadata when supplied; do not invent it.
3. **Report attachment bridge** (pending): discover the actual Research Reporting Studio storage/API contract before integration. Store a link or immutable artifact in the report project, not a detached unsourced image. Recheck graph revision and session lineage when exporting.
4. **Wexford and Metrics workflows** (pending): attach a figure to each research report with caption, dataset citations, methodology and reproducibility object IDs; keep scientific qualifications visible.
5. **Acceptance** (pending): unauthorized access denied; render-to-artifact/reopen integrity; multiple graphs; project/session association; deterministic artifact hash; reporter workflow; regression tests; rollback. Pi dev tests first, then review PR and separate production approval.

## No unsupported promises
A figure reference is not yet a render/export/report attachment. No production files, databases, or services are modified by this branch. UVR-01.1 and UVR-01.2 remain prerequisite PRs.

## Local tests
`node --test standalone-app/tests/uvr-01-3-report-figure-reference.test.mjs`
