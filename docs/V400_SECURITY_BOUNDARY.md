# Workbench v4.0.0 Security Boundary

The Connected Scientific and Engineering Workbench coordinates records and
workflows; it is not an unrestricted orchestration engine.

## Explicitly prohibited

- Arbitrary command or shell execution
- Remote shell access
- Automatic public publication
- Automatic destructive synchronization
- Automatic device flashing, reset, or power control
- Safety-control bypasses
- Autonomous high-stakes decisions
- Claims of engineering, scientific, legal, medical, accessibility, security,
  privacy, or regulatory certification

## Required controls

- Private WordPress records require an authenticated user with editing access.
- Destructive sync resolution requires a verified backup.
- Required integrations block a connected-release manifest when unavailable.
- Traceability gaps and failed evaluations block release readiness.
- Human approval is mandatory for a connected-release manifest.
- Offline services remain restricted to loopback hosts.
- Portable bundles require explicit export and import.
