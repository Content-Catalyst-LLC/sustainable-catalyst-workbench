# Backend Architecture

WordPress is the compact interface. The backend is the analytics engine.

```text
WordPress shortcode/UI
  -> WordPress REST proxy
  -> FastAPI backend
  -> Python analytics engines
  -> optional R / Julia / Haskell / C++ bridges
  -> SVG graphs + structured results
```

The first-class backend is Python because it provides the broadest ecosystem for scientific computing, statistics, graphs, AI routing, and data analysis.

Specialist language roles:

- Python: orchestration, analytics, graphing, AI routing.
- R: psychometrics, statistics, social-science methods.
- Julia: scientific simulation, differential equations, optimization.
- Haskell: formal rule validation, typed logic, scope constraints.
- C++: future high-performance kernels.

Version 0.4.1 includes Python implementations and bridge folders for R, Julia, Haskell, and C++.
