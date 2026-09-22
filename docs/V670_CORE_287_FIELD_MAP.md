# v6.7.0 Core v2.87 field map

Workbench v6.7.0 maps directly to Platform Core's `/v1/research/computation-lineage` service.

- Execution: `execution_key`, `title`, `execution_type`, `runtime_kind`, `status`, `visibility`, `project_ref`, `protocol_id`, `method_plan_ref`, `external_run_ref`, `command_or_entrypoint`, `code_ref`, `source_revision`, timestamps, provenance, metadata.
- Input: `input_key`, `input_type`, `object_ref`, `version_ref`, `content_hash`, role, selector.
- Parameter: `parameter_key`, value, unit, source reference, sensitivity role.
- Assumption: `assumption_key`, statement text, protocol assumption reference, evidence references.
- Environment: `environment_key`, type, runtime name/version, OS/arch, container image, environment hash, dependency manifest, packages, hardware.
- Step: `step_key`, `sequence`, `step_type`, tool/operation/code references, input/output references, parameters.
- Output: `output_key`, `output_type`, object/version references, content hash, schema, metadata.
- Research binding: output reference → target type/reference + declared relation.
- Dependency: upstream execution/output reference + relation.
- Verification: verification type/status + evidence.
- Lifecycle: revision and immutable snapshot requests.

Core-issued execution IDs are required for all phase-two lineage records.
