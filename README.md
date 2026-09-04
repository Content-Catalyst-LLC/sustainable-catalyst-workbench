# Sustainable Catalyst Workbench v5.4.0

## v5.4.0 — Advanced Graph Mathematics II

Workbench v5.4.0 adds multi-expression graph objects, domain-restricted piecewise construction, derivative overlays, roots/extrema/intersections, tangent and normal construction, discontinuity and asymptote analysis, inequality regions, value tables, and direct zoom/pan/trace interaction. The backend runtime advances to v5.4.0 and must be redeployed.


## v5.3.3 — Homepage & Workbench Experience Integration Hardening

Workbench v5.3.3 locks down the compact homepage Computational Instrument and the redesigned public Workbench experience. It removes the carousel's vertical `scrollIntoView()` side effect, constrains feature movement to the horizontal rail, adds a front-page guard against accidentally rendering the tall legacy v5.3.0 showcase, integrates the compact homepage placement contract into the plugin CSS, and synchronizes the visible interface release identity to v5.3.3. The certified FastAPI backend remains v5.3.0; no backend redeploy is required.

## v5.3.2 — Compact Computational Showcase, Advanced Graph Presentation & Workbench Experience Redesign

Workbench v5.3.2 turns the homepage Computational Instrument into a compact rotating showcase, upgrades the Graph Mathematics presentation with higher-density scientific rendering and direct interaction, and adds a new `[sc_workbench_experience]` surface for rebuilding the public `/workbench/` page around live computation rather than a long capability catalog. The certified FastAPI backend remains v5.3.0; no backend redeploy is required for this interface release.

## Interactive Graph Mathematics


## v5.3.0 — Computational Blackboard, Creative Mathematics & Physical Prototyping

Workbench v5.3 adds deterministic blackboard translation, creative mathematics, music/acoustics mathematics, a physical prototype bench for Arduino/ESP32/Raspberry Pi/PYNQ/Verilog/VHDL, a distinct homepage computational instrument, and an advanced dark presentation for Graph Mathematics.

Workbench v5.2.0 turns the v5.1 restricted CAS into a linked graphing environment. It adds Cartesian, parametric, polar, implicit/contour, vector-field, and 3D surface graph objects; live parameters; derivative and definite-integral overlays; roots, extrema, and intersections; and a dedicated Graph Mathematics studio.

The graph engine inherits the v5.1 restricted AST parser. User expressions do not authorize arbitrary Python, shell access, automatic publication, or remote command execution.

### Canonical endpoints

- `GET /v520/status`
- `POST /v520/graph`
- `POST /v520/analyze`
- `POST /v520/vector-field`
- `POST /v520/surface`

### WordPress

- `[sc_workbench_graph_mathematics]`
- `[sc_workbench_vector_field]`
- `[sc_workbench_surface_graph]`

## v5.1.0 Universal Mathematics & CAS Engine Foundation

**Universal Mathematics & CAS Engine Foundation**

Workbench v5.1.0 begins the calculator-gap closure with a secure symbolic mathematics core built on SymPy. It adds exact arithmetic, algebra/CAS operations, equation and system solving, differentiation, integration, limits, series, substitution, arbitrary-precision evaluation, canonical math objects, and a dedicated Mathematics Studio.

Primary shortcode:

```text
[sc_workbench topic="workbench" title="Sustainable Catalyst Workbench" display="full"]
```

Mathematics Studio:

```text
[sc_workbench_mathematics project="default" title="Universal Mathematics"]
```

See `V510_RELEASE_NOTES.md`, `docs/V510_UNIVERSAL_MATHEMATICS.md`, and `docs/V510_SECURITY_BOUNDARY.md`.

## v5.0.0 Integrated Platform

The Integrated Platform studio coordinates canonical projects, surface registries, portfolios, workflows, integrity audits, governance gates, deployment plans, dossiers, and portable packages across the Sustainable Catalyst ecosystem.
