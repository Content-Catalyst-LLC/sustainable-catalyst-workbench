# Workbench v9.4.0 — Uncertainty & Sensitivity Study Composer

Workbench v9.4.0 adds researcher-authored uncertainty models, deterministic sampling plans, and neutral sensitivity analysis over completed computational campaigns.

## Added
- Monte Carlo, Latin hypercube, and Sobol sampling plans.
- Uniform, normal, lognormal, triangular, and discrete uncertainty distributions.
- Seeded/content-addressed sample manifests for reproducibility.
- Output uncertainty summaries with confidence-aligned quantiles.
- Pearson, Spearman, and standardized-regression sensitivity statistics.
- Persistent content-addressed uncertainty/sensitivity studies.
- Campaign provenance and result-hash lineage.
- Platform Core binding plans without automatic dispatch.

## Scientific boundaries
The composer does not select distributions automatically, rank a preferred parameter, infer causal importance, declare convergence, choose a preferred model, infer scientific validity, run jobs automatically, or dispatch to Platform Core automatically.
