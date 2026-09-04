# Workbench v5.3.3 — Homepage & Workbench Experience Integration Hardening

The v5.3.3 interface contract separates carousel state from document navigation. Automatic rotation may change the active feature and horizontally center a feature tab when necessary, but it must never move the document viewport.

## Homepage invariants

- no `scrollIntoView()` in the rotating homepage runtime;
- no `window.scrollTo()` or location-hash mutation from automatic rotation;
- initial render performs no rail scrolling;
- rail centering uses the rail element's own horizontal `scrollTo()` only when content overflows;
- hover and keyboard focus continue to pause automatic rotation;
- reduced-motion preferences disable automatic rotation;
- the **Open Workbench →** CTA remains persistent.

## Integration invariants

The plugin styles the `.cch-workbench-showcase` / `.cch-workbench-showcase__inner` homepage wrapper and also supports a bare `[sc_workbench_homepage_instrument]` directly under `.cc-home-v4`.

The legacy `[sc_workbench_v530_showcase]` shortcode remains compatible away from the front page, but resolves to the compact v5.3.3 homepage instrument on the front page.
