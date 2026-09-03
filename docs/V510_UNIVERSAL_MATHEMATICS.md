# Workbench v5.1.0 — Universal Mathematics & CAS Engine Foundation

v5.1.0 establishes a canonical mathematics layer beneath Workbench and future Lab handoffs.

## What is new

- Restricted-AST mathematical parser: user input is translated into SymPy objects without Python `eval` or `exec`.
- Canonical, content-hashed math objects with exact text, decimal representation, LaTeX, free-symbol metadata, precision, and operation provenance.
- Exact arithmetic and symbolic simplification, expansion, and factorization.
- Equation and small-system solving.
- Symbolic differentiation, indefinite/definite integration, limits, and series.
- Symbolic substitution and arbitrary-precision numeric evaluation.
- Mathematics Studio shortcode: `[sc_workbench_mathematics]`.
- Python backend health and compute wiring through a configurable backend origin.
- Browser-facing status distinguishes backend CAS availability from local interface availability.

## Backend routes

- `GET /v510/status`
- `POST /v510/parse`
- `POST /v510/compute`
- `POST /v510/calculus`
- `POST /v510/solve`
- `POST /v510/substitute`

## WordPress backend URL

The Mathematics Studio reads the backend base URL from, in order:

1. `SCWB_WORKBENCH_BACKEND_URL` WordPress constant.
2. `scwb_workbench_backend_url` filter.
3. Browser origin when no explicit value exists.

For a same-origin reverse proxy, no special setting is required. For a dedicated Workbench API hostname, define the constant in `wp-config.php`, for example:

```php
define('SCWB_WORKBENCH_BACKEND_URL', 'https://workbench-api.example.org');
```

The backend permits `https://sustainablecatalyst.com`, `https://www.sustainablecatalyst.com`, localhost and loopback by default. Override with the `SCWB_ALLOWED_ORIGINS` environment variable when required.

## Scope

This is the foundation build, not the final TI-Nspire parity release. Graph-linked objects, matrix studio depth, probability/statistics parity, geometry, and Workbench-to-Lab math-object handoff remain later v5.x milestones.
