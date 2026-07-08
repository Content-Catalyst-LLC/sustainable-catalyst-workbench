# C++ Kernels Extension

Use this extension only for performance-critical numerical kernels, large simulations, graph algorithms, infrastructure networks, or embedded/edge-system models.

Recommended role:

```text
C++ = performance engine
```

Suggested integration:

- Write C++ kernels with clear input/output contracts.
- Bind into Python with pybind11.
- Let Python handle orchestration, validation, and explanation.
