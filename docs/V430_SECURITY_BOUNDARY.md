# Workbench v4.3.0 Data Security and Responsibility Boundary

- Connector definitions never store raw credentials or API secrets.
- Network sources require HTTPS and may be constrained by explicit hostname allowlists.
- Plans do not automatically fetch network data.
- Pipelines do not automatically overwrite source or derived datasets.
- Validation findings do not automatically delete or correct records.
- Dataset packages do not automatically upload, publish, import, or execute.
- Licensing, citation, freshness, quality, and fitness-for-use require human review.
- Local and offline snapshots remain private unless a user explicitly exports or transfers them.
