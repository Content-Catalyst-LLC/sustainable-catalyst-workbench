# Workbench v1.6.0 — Article-Embedded Calculators Near Formulas

Phase 6 turns the existing equation registry, placement assistant, and Workbench shortcode system into a practical near-formula calculator workflow.

## What changed

- Added backend formula embed planner: `POST /articles/formula-embed`.
- Added WordPress REST proxy: `/wp-json/sc-workbench/v1/formula-embed`.
- Added article-level shortcodes:
  - `[sc_workbench_formula_calculator ...]`
  - `[sc_formula_calculator ...]`
- Added an **Article Embeds** tab inside `[sc_workbench]`.
- Added near-formula shortcode generation to the Embed Shortcodes and Placement Assistant admin pages.
- Added front-end formula cards with actions for:
  - recommend embed
  - symbolic analysis
  - graph
  - engineering note
- Preserved the existing page-level Workbench shortcode recommendations.

## Recommended shortcode

```text
[sc_workbench_formula_calculator display="inline" formula="y = a*sin(b*x)" tool="graphable-function-explorer" title="Graphable Function near this formula"]
```

Use it directly below or beside the equation in the article.

## Display modes

```text
[sc_workbench_formula_calculator display="inline" formula="σ = F/A" tool="mechanical-systems-engineering-tool"]
[sc_workbench_formula_calculator display="compact" formula="y = a*sin(b*x)" tool="graphable-function-explorer"]
[sc_workbench_formula_calculator display="drawer" formula="NPV = sum(CF_t/(1+r)^t)" tool="economics-calculator"]
```

- `inline` is best for a small calculator immediately under a formula.
- `compact` is best for a primary article calculator.
- `drawer` is best for secondary calculators that should not interrupt reading.

## Admin workflow

1. Open **SC Workbench → Embed Shortcodes**.
2. Run **Scan Equations + Build Recommendations**.
3. Copy the **Near-formula shortcode**.
4. Paste it directly below the relevant formula in the article editor.
5. Review the calculator action and professional-boundary text before publishing.

## Backend behavior

The backend planner classifies formulas into broad embed kinds:

- `graph` for graphable formulas and parameterized functions.
- `symbolic` for general symbolic math and calculus notation.
- `engineering` for stress, force, beam, voltage, heat, pump, and engineering formulas.
- `calculator` for economics, energy, statistics, and other domain calculators.

The classification is deterministic and review-oriented. It does not claim that a formula has only one valid interpretation.

## Boundary

Article-embedded calculators are educational, analytical, and editorial support tools. They do not replace licensed engineering, safety-critical, legal, financial, medical, compliance, or assurance review.
