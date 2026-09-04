# Workbench v5.5.0 — Security Boundary

- User-entered locus expressions pass through `RestrictedSympyParser` from v5.1.
- Python `eval` and `exec` are not authorized or used.
- Geometry constraints are explicit allow-listed relation types.
- Constraint solving is bounded by a hard iteration limit.
- Affine transforms accept finite numeric matrices only.
- Construction objects reference validated point IDs.
- Browser geometry interaction changes mathematical state only; it does not authorize shell, filesystem, network-command, or device-programming operations.
- Remote shell, arbitrary command execution, automatic device programming, and unattended hardware execution remain unauthorized.
