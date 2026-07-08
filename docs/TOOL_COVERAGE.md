# Tool Coverage v0.4.2

Built-in backend calculators and analytics:

- Ask the Workbench
- Linear System Solver
- Calculus Function Analyzer
- Statistics Analyzer
- Regression Analyzer
- Probability Distribution Calculator
- Differential Equation Simulator
- Economics Calculator
- Energy Systems Calculator
- Psychology Scale Analyzer
- Scientific Calculator
- Sustainability & Resilience Scorecard
- AI Governance Audit
- Haskell Rule Checker
- Qualitative Interpretation Matrix

The goal is not to display hundreds of fake tools. The goal is to provide compact tools that actually run and can grow into deeper domain-specific engines.

## v0.4.2 Visual Analytics

v0.4.2 adds a dedicated **Visualize** mode to the compact WordPress Workbench interface. The new Visual Analytics Studio renders backend-generated SVG charts through Python/matplotlib and supports:

- bar charts
- line charts
- scatter plots with optional fitted line diagnostics
- histograms with summary statistics
- box plots

The visualizations are not JavaScript-only charts. WordPress collects the inputs and displays the SVG. The Python analytics backend parses data, computes summary diagnostics, renders the chart, and returns the SVG output to the page.
