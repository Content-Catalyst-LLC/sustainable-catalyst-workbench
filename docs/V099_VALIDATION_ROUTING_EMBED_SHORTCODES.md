# Sustainable Catalyst Workbench v0.9.9

## Validation, routing, and calculator embed shortcodes

v0.9.9 adds a page-level routing layer that analyzes the equation registry and recommends calculator-specific shortcodes for formula-heavy articles.

### WordPress admin

Open:

```text
SC Workbench → Embed Shortcodes
```

Use:

```text
Build Shortcode Recommendations
```

or:

```text
Scan Equations + Build Recommendations
```

The dashboard groups indexed equations by article, selects the strongest matching Workbench calculator, assigns a confidence level, and generates an embeddable shortcode.

### Calculator-specific shortcode

```text
[sc_workbench mode="tool" tool="systems-modeling-tool" article="article-slug" title="Systems Modeling Tool for this article"]
```

This opens the Workbench directly to the calculator tab and preselects the recommended tool.

### CSV export

The Embed Shortcodes admin page exports a CSV containing article title, slug, equation count, primary domain, recommended tool, confidence, validation status, and shortcode.

### Backend route

The backend also includes:

```text
POST /routing/shortcode-recommend
```

for equation-to-shortcode routing from supplied equations.

### Editorial note

Recommendations are deterministic and should be reviewed before public placement, especially where notation is generic or an article spans multiple domains.
