# Workbench v8.9.0 — Interactive Scientific Figure & Visualization Composer

Workbench v8.9.0 adds a provenance-preserving scientific figure composition layer over completed Workbench execution jobs and the v8.8 comparative-analysis metric model.

## What ships

- project-scoped source catalog for completed execution runs;
- request/result scalar metric discovery with explicit coverage counts;
- deterministic multi-panel figure specifications;
- explicit bar, line, scatter, point and table marks;
- explicit x/y metric selection rather than automatic scientific encoding;
- linked-selection metadata across source jobs;
- source-job request/result/job hashes embedded in the figure provenance manifest;
- renderer-neutral figure contract for responsive client presentation;
- JSON and panel-row CSV export planning plus client-side SVG preview/export contract;
- two-phase Platform Core visual-object binding plans.

## Scientific boundary

The composer is an analytical presentation layer. It does not rewrite execution results, rank models, select a winner, infer scientific validity, infer causality, infer statistical significance, or silently choose scientific encodings. Missing metrics remain missing rather than being coerced into synthetic values.

## Deployment correction

The v8.9 Contabo deployment verifier uses the Workbench service's actual local port, `127.0.0.1:8088`. This corrects the v8.8 deployment-script verification defect that checked port `8000` even though the container was healthy on `8088`.

No database migration is required. Existing persistent Workbench state remains under the established `/data` mount.
