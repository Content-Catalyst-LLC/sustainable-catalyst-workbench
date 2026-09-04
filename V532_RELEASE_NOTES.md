# Workbench v5.3.2 — Compact Computational Showcase, Advanced Graph Presentation & Workbench Experience Redesign

## Homepage showcase
- Replaces the tall multi-instrument homepage block with one compact rotating stage.
- Five manual/automatic modes: Graph, CAS, Sound, Form, Prototype.
- Persistent **Open Workbench →** CTA and clickable Workbench identity.
- Hover/focus pause and reduced-motion support.

## Advanced Graph presentation
- Higher-density major/minor grid and stronger axis hierarchy.
- High-DPI smooth curves with discontinuity guards and subtle line glow.
- Sampled root/extrema presentation markers for the primary plotted series.
- Pointer trace readout, wheel zoom, reset view, and fullscreen canvas.
- Improved integral shading.
- 3D surface view gains richer depth rendering and drag-to-rotate presentation.

## Workbench experience
- New `[sc_workbench_experience]` and `[sc_workbench_experience_page]` shortcodes.
- Public page hierarchy: computational core → math as language → advanced Workbench navigator → governed boundary.
- Sound, Form, and Prototype surfaces are tabbed so only one large secondary instrument is visible at a time.

## Runtime
No numerical backend changes. The production FastAPI runtime remains v5.3.0 and does not require redeployment.
