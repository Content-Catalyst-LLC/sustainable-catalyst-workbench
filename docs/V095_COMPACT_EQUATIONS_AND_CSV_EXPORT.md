# Workbench v0.9.5: Compact Equation Display and CSV Export

This release keeps the v0.9.x equation registry but changes the Research Library display path so the page does not expand into many analyzer cards.

## Changes

- Research Library mode now shows a compact equation summary by default.
- Equation previews must be opened intentionally.
- Only one selected equation analyzer is shown at a time.
- Added Equation Registry CSV export from WordPress admin.
- CSV includes article title, slug, permalink, normalized equation, raw equation, suggested domain, suggested tools, context, hash, and timestamps.

## Recommended shortcodes

Research Library:

```text
[sc_workbench mode="library" topic="research-library" title="Ask the Sustainable Catalyst Workbench"]
```

Article pages:

```text
[sc_workbench mode="auto"]
```

## CSV export

WordPress Dashboard → SC Workbench → Equation Registry → Download CSV Report.
