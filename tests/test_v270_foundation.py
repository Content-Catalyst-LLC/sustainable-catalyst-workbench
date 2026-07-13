from backend.app.v270 import (
    AccessibleDescriptionRequest,
    DashboardMetric,
    DashboardRequest,
    HistogramRequest,
    SeriesSummaryRequest,
    StateEdge,
    StateNode,
    SystemStateRequest,
    ValidationOverlayRequest,
    accessible_description,
    analyze_system_state,
    distribution_histogram,
    evaluate_dashboard,
    validation_overlay,
    visualization_summary,
)


def test_visualization_summary_and_histogram():
    summary = visualization_summary(SeriesSummaryRequest(values=[1, 2, 3, 4, 5], units="V"))
    assert summary["ok"] is True
    assert summary["statistics"]["mean"] == 3
    histogram = distribution_histogram(HistogramRequest(values=[1, 1, 2, 3], bins=3))
    assert histogram["ok"] is True
    assert sum(item["count"] for item in histogram["bins"]) == 4


def test_dashboard_and_validation_overlay():
    dashboard = evaluate_dashboard(DashboardRequest(metrics=[
        DashboardMetric(key="temperature", label="Temperature", value=42, warning_high=55, critical_high=70),
        DashboardMetric(key="latency", label="Latency", value=35, warning_high=25, critical_high=50),
    ]))
    assert dashboard["overallStatus"] == "warning"
    overlay = validation_overlay(ValidationOverlayRequest(
        observed=[1.0, 2.1, 2.9], predicted=[1.0, 2.0, 3.0], uncertainty=[0.1, 0.1, 0.1]
    ))
    assert overlay["ok"] is True
    assert overlay["metrics"]["rmse"] < 0.1


def test_state_graph_and_accessible_description():
    state = analyze_system_state(SystemStateRequest(
        nodes=[StateNode(id="sensor", state="normal"), StateNode(id="controller", state="warning")],
        edges=[StateEdge(source="sensor", target="controller")],
    ))
    assert state["ok"] is True
    assert state["statusCounts"]["warning"] == 1
    accessible = accessible_description(AccessibleDescriptionRequest(
        title="Response", chart_type="line", y=[1, 2, 4], units="V"
    ))
    assert accessible["ok"] is True
    assert "3 observations" in accessible["description"]
