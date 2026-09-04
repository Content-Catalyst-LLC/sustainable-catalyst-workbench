# Workbench v5.4.0 — Security Boundary

- User expressions are parsed by the existing restricted AST-to-SymPy parser.
- Python `eval()` and `exec()` are not used for graph expressions.
- At most 8 graph series, 1,001 samples per series, 201 value-table rows, and 8 parameters are accepted.
- Domain restrictions must be finite bounded intervals.
- Graph analysis is deterministic and returns structured JSON objects.
- No remote shell, arbitrary command execution, device programming, or unattended physical execution is authorized.
- Existing v5.3 physical prototype scaffolds remain export-only.
