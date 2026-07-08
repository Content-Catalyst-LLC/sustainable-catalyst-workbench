# Sustainable Catalyst Workbench v1.0.0

Stable Workbench Core, Placement Assistant, and Validation Dashboard.

## Purpose

v1.0.0 stabilizes the Workbench as a production-oriented Sustainable Catalyst platform layer. It does not simply add more calculators. It improves routing quality, shortcode placement, display modes, validation visibility, and editorial workflow around formula-heavy articles.

## Major features

### Stable shortcode display modes

Use the same calculator engine in four page layouts:

```text
[sc_workbench mode="tool" display="inline" tool="systems-modeling-tool"]
[sc_workbench mode="tool" display="compact" tool="systems-modeling-tool"]
[sc_workbench mode="tool" display="full" tool="systems-modeling-tool"]
[sc_workbench mode="tool" display="drawer" tool="systems-modeling-tool"]
```

Recommended usage:

- `inline`: small embed beside or under a formula.
- `compact`: main calculator embed inside an article section.
- `full`: standalone calculator page.
- `drawer`: secondary/collapsible calculator for long pages.

### Article Calculator Placement Assistant

Admin path:

```text
SC Workbench → Placement Assistant
```

The assistant reads equation-derived shortcode recommendations and provides:

- article title and permalink;
- recommended calculator;
- suggested placement near formulas;
- display mode;
- confidence level;
- copy-ready shortcode.

### Validation Dashboard

Admin path:

```text
SC Workbench → Validation Dashboard
```

The dashboard summarizes:

- indexed equations;
- articles/pages represented;
- shortcode recommendation quality;
- weak matches needing review;
- calculator validation categories.

### Tool Catalog

Admin path:

```text
SC Workbench → Tool Catalog
```

REST endpoint:

```text
/wp-json/sc-workbench/v1/tool-catalog
```

Provides calculator IDs, domains, validation status, and shortcode forms.

### Placement and routing endpoints

```text
/wp-json/sc-workbench/v1/placement-assistant
/wp-json/sc-workbench/v1/validation-summary
/wp-json/sc-workbench/v1/tool-catalog
```

## Editorial workflow

1. Run the Equation Registry scan.
2. Build shortcode recommendations.
3. Open Placement Assistant.
4. Copy the recommended shortcode into the article near the formula.
5. Prefer high-confidence recommendations first.
6. Use drawer mode for secondary calculators on long pages.

## Stabilization direction

v1.0.0 is the baseline for future calculator upgrades. New calculators should now be added through validated tool specs, sample inputs, expected outputs, warnings, and article-placement guidance.
