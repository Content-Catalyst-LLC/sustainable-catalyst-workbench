# Workbench Extension SDK v1

## Manifest

Every extension declares a stable ID, semantic version, publisher, core compatibility range, capability scopes, hook subscriptions, dependencies, optional hostname allowlists, package hash, signature metadata, license, and repository.

## Capability model

Capabilities are deny-by-default and must be selected from the published registry. Write, network, device-planning, evaluation-write, and Lab-write capabilities require explicit security review. Wildcards are rejected.

## Hooks

Hooks use symbolic handlers, JSON input/output schemas, timeouts, retry limits, idempotency declarations, and capability scopes. Hook contracts do not execute handlers automatically.

## Lifecycle

Install, activate, deactivate, update, and uninstall are planned separately. Compatibility, integrity, signature, backup, and human-approval checks are recorded before an external runtime may execute the action.

## Packaging

Packages preserve manifest, source-file hashes, documentation, tests, compatibility reports, security audits, and a stable package hash. Import, installation, activation, and registry publication remain explicit.
