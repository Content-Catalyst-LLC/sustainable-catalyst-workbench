# Workbench v9.3.0 — Statistical Analysis & Diagnostic Workspace

v9.3.0 adds an explicit statistical analysis layer over completed Workbench execution jobs and v9.2 computational campaigns.

## Research workflow

1. Select a project and optional computational campaign or completed execution jobs.
2. Specify an explicit numeric result metric path.
3. Optionally specify grouping or numeric predictor parameter paths.
4. Select one or more statistical methods explicitly.
5. Compute descriptive statistics, confidence intervals, diagnostics, test statistics, correlations, or regression diagnostics.
6. Save the result as an immutable content-addressed statistical analysis record.
7. Prepare a two-phase Platform Core binding plan without automatic dispatch.

## Supported methods

- descriptive statistics and mean confidence intervals
- distribution diagnostics (skewness, excess kurtosis, MAD, range)
- Shapiro-Wilk normality statistic
- Levene variance diagnostic
- one-sample t statistic
- Welch independent-samples t statistic
- one-way ANOVA statistic with eta-squared
- Kruskal-Wallis statistic
- Pearson and Spearman correlations
- simple linear regression with residual RMSE, MAE, mean residual, Durbin-Watson, and optional residual Shapiro statistic

## Scientific boundaries

Workbench calculates requested statistics but does not choose methods automatically, label results significant/non-significant, accept or reject hypotheses, infer causality, declare scientific validity, select a preferred model, author research interpretation, or dispatch to Platform Core automatically.
