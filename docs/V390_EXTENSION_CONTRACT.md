# Workbench Extension Contract 1.0

Stability: stable
Compatibility floor: Workbench 3.9.0

## Public integration surfaces

- Versioned JSON schemas
- WordPress shortcodes and REST routes
- Browser events such as `scwb:project-changed` and `scwb:studio-activated`
- Content-hashed project, evidence, handoff, review, Lab, offline, and evaluation records

## Compatibility rules

- Stable schemas are additive within the 1.x contract.
- Removals require a documented deprecation period.
- Breaking changes require a new contract major version.
- Extensions must not bypass capability checks, nonces, consent gates, or human review.
- Extensions must preserve browser-local and offline-safe behavior where applicable.
