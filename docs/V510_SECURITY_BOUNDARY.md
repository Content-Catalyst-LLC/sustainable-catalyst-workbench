# Workbench v5.1.0 — Mathematics Security Boundary

The Mathematics Engine accepts mathematical expressions, not Python programs.

- No `eval`, `exec`, imports, attributes, subscripts, comprehensions, lambdas, assignments, or arbitrary function calls are accepted.
- Mathematical functions are selected from an explicit allow-list.
- Expression length, AST node count, solve-system size, numeric precision, derivative order, and series order are bounded.
- The API does not authorize shell access, filesystem access, network access, package installation, arbitrary code execution, or automatic high-stakes decisions.
- Symbolic mathematics can still be computationally expensive. Production deployments should also enforce reverse-proxy request-size and request-time limits.
