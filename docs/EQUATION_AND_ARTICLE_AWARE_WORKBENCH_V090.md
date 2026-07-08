# v0.9.2 Equation and Article-Aware Workbench Layer

This release connects Sustainable Catalyst articles to the Workbench through a WordPress-side equation registry.

## What it adds

- WordPress database scanner for LaTeX in published public post types.
- Custom table: `wp_sc_workbench_equations`.
- Admin page: `SC Workbench → Equation Registry`.
- Shortcode modes: `[sc_workbench mode="auto"]` and `[sc_workbench article="article-slug"]`.
- Frontend Equations tab showing current-article equations.
- Equation analysis button for deterministic domain inference and Workbench tool recommendations.
- Backend route: `POST /equations/analyze`.

## Supported LaTeX patterns

```text
\( ... \)
\[ ... \]
$$ ... $$
[latex]...[/latex]
```

Single-dollar inline math is intentionally not scanned by default because ordinary writing, prices, and code examples create too many false positives.

## Workflow

1. Install/activate the v0.9.2 plugin.
2. Go to `SC Workbench → Equation Registry`.
3. Click `Scan / Rebuild Equation Registry`.
4. Add `[sc_workbench mode="auto"]` to article templates or article pages.
5. Open the Workbench Equations tab on an article to see detected equations and recommended tools.

## Safety and accuracy

Equation mappings are inferred from notation and nearby context. They should be reviewed, especially for ambiguous symbols. The system is educational and analytical support only; it does not provide licensed engineering, medical, legal, financial, architectural, or safety-critical approval.
