from backend.app.v260 import (
    AuditRequest,
    BenchmarkRequest,
    EquivalenceRequest,
    ExecutionRecord,
    ProjectRequest,
    ReproducibilityRequest,
    audit_execution,
    compare_equivalence,
    generate_project,
    numerical_benchmark,
    runtime_catalog,
    validate_reproducibility,
)


def test_runtime_catalog_includes_requested_languages():
    result = runtime_catalog()
    assert result["ok"] is True
    for language in ("python", "javascript", "r", "sql", "go", "c", "cpp", "rust", "haskell", "assembly"):
        assert language in result["languages"]


def test_equivalent_energy_results_pass():
    result = compare_equivalence(EquivalenceRequest(
        calculation="energy",
        inputs={"power_kw": 2.5, "hours": 8},
        outputs={"python": 20.0, "go": 20, "rust": 20.0000000001},
        absolute_tolerance=1e-6,
        relative_tolerance=1e-6,
    ))
    assert result["ok"] is True


def test_stable_sum_improves_cancellation_case():
    result = numerical_benchmark(BenchmarkRequest(values=[1e16, 1.0, -1e16], benchmark="cancellation"))
    assert result["ok"] is True
    assert result["absoluteErrors"][result["bestMethod"]] <= result["absoluteErrors"]["naive"]


def test_project_generation_produces_test_vector():
    result = generate_project(ProjectRequest(language="rust", project_name="energy-model", expression="power_kw * hours"))
    assert result["ok"] is True
    assert "main.rs" in result["files"]
    assert "test-vectors.json" in result["files"]


def test_reproducibility_numeric_outputs():
    result = validate_reproducibility(ReproducibilityRequest(
        records=[
            ExecutionRecord(language="python", runtime="3.12", output="20.000000"),
            ExecutionRecord(language="go", runtime="1.24", output="20"),
        ],
        comparison_mode="numeric",
        tolerance=1e-9,
        required_languages=["python", "go"],
    ))
    assert result["ok"] is True


def test_audit_rejects_unrestricted_execution():
    result = audit_execution(AuditRequest(
        language="python",
        source_bytes=100,
        timeout_seconds=8,
        output_bytes=100,
        filesystem_mode="unrestricted",
        network_access="disabled",
        explicit_consent=True,
    ))
    assert result["ok"] is False
