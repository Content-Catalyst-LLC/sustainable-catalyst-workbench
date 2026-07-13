# Sustainable Catalyst Prototyping Workbench v2.6.0

## Multi-Language Engineering Runtime Studio

Version 2.6.0 adds a transparent, auditable multi-language engineering runtime layer across the existing Code Studio, simulation, instrumentation, embedded-device, robotics, and hardware workflows.

### New studios

- Multi-Language Engineering Runtime Studio
- Language Equivalence and Result Validation Studio
- Numerical Stability and Runtime Benchmark Studio
- Multi-Language Project Generator
- Cross-Runtime Reproducibility Validator
- Local Execution Safety and Audit Studio

### Supported runtime profiles

- Python
- JavaScript / Node.js
- R
- SQL / SQLite
- Go
- C11
- C++17
- Rust
- Haskell
- Assembly project profiles

### Engineering and validation capabilities

- Equivalent calculation templates and cross-language output comparison
- Absolute and relative tolerance checks
- Energy, quadratic, vector dot-product, and linear-regression reference calculations
- Naive, Kahan, and pairwise summation benchmarks
- High-precision decimal references for cancellation and accumulation review
- Generated source projects with test vectors and validation checklists
- Numeric, exact-text, and canonical-JSON reproducibility comparisons
- Runtime-version, duration, exit-code, and required-language coverage records
- Execution-boundary audits for source size, output size, timeout, filesystem, network, and consent
- Browser-local, versioned JSON exports

### Local runner

The v2.6.0 runner adds discovery and structured execution for Python, JavaScript, R, SQL, Go, C, C++, Rust, and Haskell. Assembly remains a project/profile workflow rather than direct browser-triggered execution.

The runner remains loopback-only, origin-paired, disabled for native execution by default, temporary-directory based, output limited, and free of an arbitrary shell endpoint.

### Compatibility

All v2.0.0–v2.5.0 shortcodes, local-storage namespaces, FastAPI routes, saved records, runner protections, and project data remain available.
