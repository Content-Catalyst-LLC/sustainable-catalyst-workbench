# Sustainable Catalyst Workbench v3.0.1

## Production Activation and Interface Reliability

Workbench v3.0.1 is a stabilization release for the unified v3.0.0 interface. It does not add another specialist studio. It makes the primary public shortcode, studio registry, navigation, asset loading, diagnostics, and responsive behavior explicit and testable.

### Included

- Canonical ownership of `[sc_workbench]` after plugin initialization and `wp_loaded`.
- A single 11-studio registry shared by the primary selector and diagnostics.
- Runtime checks for missing shortcodes, blank output, module exceptions, empty mounts, and offline states.
- Keyboard tab navigation with Arrow keys, Home, and End.
- Hash-addressable studios such as `#workbench-studio-simulation`.
- Remembered project-specific studio selection.
- MutationObserver initialization for interfaces inserted by Gutenberg, Elementor, AJAX, or reusable blocks.
- Hidden-panel resize and visualization reflow events.
- File-modification asset versions for cache-busting.
- Visible activating, ready, unavailable, empty, offline, and error states.
- Mobile horizontal studio navigation and reduced-motion support.
- `[sc_workbench_diagnostics]` and the public WordPress production-status REST route.
- FastAPI v3.0.1 status, activation-audit, registry-validation, and interface-run-audit routes.
- Automated source, shortcode, browser-router, Python, PHP, JavaScript, Go, and secret-scan checks.

### Primary shortcode

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="full"]
```

### Diagnostics shortcode

```text
[sc_workbench_diagnostics]
```

### Compatibility

All v2.0.0-v3.0.0 specialist shortcodes and browser-storage records remain available. The v3.0.0 local runner remains compatible and is not replaced by this interface-only patch.
