from app.v301 import (
    EXPECTED_STUDIOS,
    ActivationAuditRequest,
    InterfaceEvent,
    InterfaceRunRequest,
    RegistryValidationRequest,
    StudioProbe,
    activation_audit,
    audit_interface_run,
    status,
    validate_registry,
)


def ready_probes():
    return [
        StudioProbe(
            key=key,
            shortcode=f"sc_workbench_{key}",
            registered=True,
            rendered=True,
            assets_loaded=True,
            mount_count=1,
            state="ready",
        )
        for key in EXPECTED_STUDIOS
    ]


def test_status_reports_all_studios():
    result = status()
    assert result["ok"] is True
    assert result["version"] == "3.0.1"
    assert result["expectedStudioCount"] == 11
    assert result["expectedStudios"] == list(EXPECTED_STUDIOS)


def test_clean_activation_audit_passes():
    request = ActivationAuditRequest(
        primary_shortcode_registered=True,
        router_loaded=True,
        page_builder="gutenberg",
        viewport_width=1440,
        studios=ready_probes(),
    )
    result = activation_audit(request)
    assert result["ok"] is True
    assert result["score"] == 100.0
    assert result["missingStudios"] == []
    assert result["unrenderedStudios"] == []


def test_activation_audit_exposes_failures():
    probes = ready_probes()
    probes[2] = probes[2].model_copy(update={"rendered": False, "state": "empty", "mount_count": 0})
    request = ActivationAuditRequest(
        primary_shortcode_registered=False,
        router_loaded=False,
        page_builder="elementor",
        viewport_width=390,
        studios=probes[:-1],
    )
    result = activation_audit(request)
    assert result["ok"] is False
    assert "documentation" in result["missingStudios"]
    assert "embedded" in result["unrenderedStudios"]
    assert result["viewport"]["mobileLayout"] is True
    assert result["score"] < 95


def test_registry_validation_detects_duplicates_and_missing():
    request = RegistryValidationRequest(
        expected_keys=list(EXPECTED_STUDIOS),
        registered_keys=list(EXPECTED_STUDIOS[:-1]),
        registered_shortcodes=["sc_workbench_unified", "sc_workbench_unified"],
    )
    result = validate_registry(request)
    assert result["ok"] is False
    assert result["missingKeys"] == ["documentation"]
    assert result["duplicateShortcodes"] == ["sc_workbench_unified"]


def test_interface_run_requires_every_studio():
    events = []
    for studio in EXPECTED_STUDIOS:
        events.extend(
            [
                InterfaceEvent(studio=studio, event="activate", success=True, duration_ms=2),
                InterfaceEvent(studio=studio, event="render", success=True, duration_ms=5),
            ]
        )
    result = audit_interface_run(InterfaceRunRequest(events=events))
    assert result["ok"] is True
    assert result["missingActivation"] == []
    assert result["missingRender"] == []
    assert result["maximumDurationMs"] == 5
