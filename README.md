# Sustainable Catalyst Workbench v7.3.0

Current release: **Workbench v7.3.0 — Dataset, Variable & Parameter Workspace**. v7.3.0 adds a content-addressed, unit-aware research-input workspace above the v7.0 execution engine, v7.1 execution objects, and v7.2 runtime orchestrator. It defines bounded dataset objects, variables, parameter sets, assumptions, safe derived scalar values, explicit execution bindings, and two-phase Platform Core computation-lineage plans. It performs no arbitrary code execution, hidden data fetching, automatic persistence, automatic runtime dispatch, or automatic Core writes.

# Sustainable Catalyst Workbench v7.2.0

Current release: **Workbench v7.2.0 — Scientific Runtime Orchestrator**. v7.2.0 adds deterministic runtime routing above the v7.0 unified execution engine and v7.1 execution-object model. It selects bounded local adapters for symbolic mathematics, numerical computing, simulation, controls/signals, measurement, electronics/digital hardware, uncertainty, predictive analysis, forensic reconstruction, and energy execution; preserves content-addressed execution objects; supports dependency-aware orchestrated workflows; exposes plan-only R/Julia/ML adapter handoffs; and prepares two-phase Platform Core research-workflow records against `sc.research.workflow-orchestration.v1`. Arbitrary code, subprocess execution, automatic external dispatch, and automatic Core persistence remain prohibited.

# Sustainable Catalyst Workbench v7.1.0

Current release: **Workbench v7.1.0 — Unified Execution Object Model**. v7.1.0 formalizes every unified Workbench execution and workflow as a portable, content-addressed execution object with deterministic identity, declared inputs, parameters, runtime/environment identity, dependency edges, outputs, provenance, integrity validation, explicit metadata-only revisions, and two-phase Platform Core binding plans. Specialist execution remains in Workbench; object persistence, replay, scientific-validity certification, ranking, and truth determination are not performed automatically.

# Sustainable Catalyst Workbench v6.8.0

Current release: **Workbench v6.8.0 — Scenario & Uncertainty Compute Runtime Integration**. v6.8.0 connects Platform Core scenario-compute and uncertainty-compute handoffs to Workbench's specialist numerical execution plane. It adds deterministic Monte Carlo/LHS sampling, Sobol/Morris design and post-processing, ensemble statistics, empirical exceedance probabilities, Core scenario-request consumption, deterministic affine scenario execution, Core callback planning, and v6.7 computation-lineage handoffs. Core remains authoritative for scenario definitions, uncertainty semantics, provenance, and research context; Workbench performs the numerical computation and does not automatically dispatch or persist to Core.

# Sustainable Catalyst Workbench v6.7.0

Current release: **Workbench v6.7.0 — Computation, Analysis & Execution Lineage Bridge**. v6.7.0 maps externally executed Workbench computation into Platform Core's `sc.research.computation-analysis-execution-lineage.v1` contract. Workbench prepares Core execution registration, exact input/parameter/assumption/environment/ordered-step/output/dependency/verification lineage requests, unified-session execution bindings, revisions, and immutable snapshot requests. Platform Core remains a provenance and lineage registry; specialist computation remains Workbench-owned.

# Sustainable Catalyst Workbench v6.6.0

Current release: **Workbench v6.6.0 — Unified Research Project & Session Bridge**. v6.6.0 binds canonical Workbench computational projects into Platform Core 3.0 unified research runtime sessions using a two-phase lifecycle: Workbench first prepares the Core session request, Core returns the authoritative session ID, and Workbench then prepares product/object/execution/visual/validation/package/handoff bindings against that ID. Workbench remains the specialist computation authority and does not automatically persist Core state.

# Sustainable Catalyst Workbench v6.5.0

Current release: **Workbench v6.5.0 — Unified Runtime Contract Adapter**. v6.5.0 builds on the v6.4 Core connectivity foundation by implementing deterministic adapters for `sc.research.unified-runtime-contract.v1`: contract validation, Workbench product-binding declarations, canonical project/object reference mapping, inbound Core exchange-envelope consumption, and outbound Core-compatible exchange/invocation/result request construction. Core still does not directly execute Workbench specialist code, and v6.5 does not automatically persist or dispatch to Core.

# Sustainable Catalyst Workbench v6.0.0

Current capability release: **Unified Computational Workbench**. v6.0.0 links specialist mathematics and engineering results into canonical computational projects with shared variables, linked objects, provenance, append-only history, portable exports, and explicit cross-platform handoffs. The backend runtime advances to v6.0.0 and must be redeployed.

# Sustainable Catalyst Workbench v5.9.0

Current capability release: **FPGA, PYNQ & Digital Logic Workbench**. v5.9.0 adds restricted Boolean logic, truth tables, minimization, Karnaugh maps, deterministic FSM validation, digital timing waveforms, pre-synthesis resource estimates, Verilog/VHDL and testbench scaffolds, and PYNQ overlay planning. The backend runtime advances to v5.9.0 and must be redeployed.

# Sustainable Catalyst Workbench v5.8.0

Current capability release: **Electronics & Embedded Systems Studio**. v5.8.0 adds bounded circuit/RLC analysis, ADC/DAC quantization, PWM/timer and sampling planning, digital-bus estimates, sensor transfer models, GPIO allocation, and export-only MCU/FPGA scaffolds.

# Sustainable Catalyst Workbench v5.7.0

## v5.7.0 — Signals, Systems & Control Mathematics

Workbench v5.7.0 adds FFT spectrum and harmonic analysis, bounded digital filter design, transfer-function and Bode analysis, pole/zero and root-locus inspection, state-space controllability/observability analysis, discrete convolution, and PID closed-loop simulation with performance metrics. The backend runtime advances to v5.7.0 and must be redeployed.

## v5.6.0 — Numerical Methods & Scientific Computing

Workbench v5.6.0 adds bounded numerical root finding, integration and finite-difference differentiation, interpolation, initial-value ODE solvers, linear algebra, least squares, and bounded multivariable optimization. Numerical methods expose tolerances and diagnostics and preserve canonical reproducible result objects. The backend runtime advances to v5.6.0 and must be redeployed.

## v5.5.0 — Dynamic Geometry & Interactive Mathematics

Workbench v5.5.0 makes mathematics directly manipulable. It adds draggable geometry, bounded constraints, live measurements, algebra ↔ geometry linkage, affine/matrix transformations, conic families, expression-linked loci, and canonical reproducible geometry objects. The backend runtime advances to v5.5.0 and must be redeployed.

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

## Workbench v7.4.0 — Numerical Methods & Solver Runtime

v7.4.0 adds a canonical numerical solver layer over the bounded v5.6 numerical engine and the v7.0–v7.3 execution/object/orchestration/data-workspace stack. It provides explicit solver selection, normalized convergence/residual/error diagnostics, refinement studies, workspace-to-solver binding plans, execution-object provenance, and two-phase Platform Core computation-lineage planning.
