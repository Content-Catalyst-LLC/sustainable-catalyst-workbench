# v6.0.0 Unified Computational Workbench

## Objective

Workbench v6.0.0 provides a canonical project layer above the specialist v5.x engines. Instead of treating a symbolic result, graph, geometry construction, numerical solve, control model, electronics plan, or FPGA artifact as an isolated result, Workbench can represent each as a content-hashed computational object in one project.

## Project model

A v6 computational project contains:

1. project identity and metadata;
2. shared variables with optional units and source-object links;
3. specialist computational objects;
4. explicit object dependencies and data-flow links;
5. provenance operations and source records;
6. append-only history events;
7. portable export manifests; and
8. cross-platform handoff packets.

Project validation detects missing shared variables and unresolved object dependencies. Link validation detects duplicate links, missing objects, self-links, and graph cycles. Acyclic graphs receive a deterministic topological order.

## Shared variables

Shared variables use restricted identifier names and typed JSON-compatible values. Locked variables reject overrides. The project layer does not evaluate arbitrary expressions; specialist engines remain responsible for bounded computation.

## Provenance and history

Operations and history events form deterministic hash chains. These chains make the order and parent relationship of project changes inspectable without claiming cryptographic identity or external certification.

## Portability

Exports are deterministic project manifests. Handoff packets can target Lab, Decision Studio, Knowledge Library, Research Librarian, Site Intelligence, Workspace, or offline continuation. Import on the target side remains an explicit action.
