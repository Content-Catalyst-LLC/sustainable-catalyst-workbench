import math
import pytest

from app.v360 import (
    ClassificationEvaluationRequest,
    CrossValidationRequest,
    DatasetProfileRequest,
    DriftAuditRequest,
    ExperimentScaffoldRequest,
    FairnessAuditRequest,
    FairnessGroup,
    FeaturePlanRequest,
    ForecastRequest,
    LeakageAuditRequest,
    ModelCardRequest,
    RegressionEvaluationRequest,
    ReproducibilityRequest,
    SplitPlanRequest,
    audit_drift,
    audit_fairness,
    audit_leakage,
    build_experiment_scaffold,
    build_feature_plan,
    build_linear_trend_forecast,
    build_model_card,
    build_reproducibility_plan,
    build_split_plan,
    evaluate_classification,
    evaluate_regression,
    profile_dataset,
    summarize_cross_validation,
)


def test_dataset_profile_numeric_and_categorical():
    result = profile_dataset(DatasetProfileRequest(rows=[{"x": 1, "group": "A", "y": 2}, {"x": 3, "group": "B", "y": 4}], target="y", dataset_id="Demo"))
    assert result["profile"]["rowCount"] == 2
    assert result["profile"]["targetPresent"] is True
    x = next(item for item in result["profile"]["columns"] if item["name"] == "x")
    assert x["kind"] == "numeric" and x["mean"] == 2.0


def test_split_plan_counts_and_time_warning():
    result = build_split_plan(SplitPlanRequest(record_count=100, strategy="time"))
    assert sum(result["plan"]["counts"].values()) == 100
    assert result["plan"]["warnings"]


def test_feature_plan_excludes_target_identifier_and_protected():
    result = build_feature_plan(FeaturePlanRequest(columns=["id", "age", "group", "outcome"], target="outcome", identifiers=["id"], protected_attributes=["group"]))
    assert result["plan"]["candidateFeatures"] == ["age"]
    assert len(result["plan"]["excluded"]) == 3


def test_regression_metrics_are_correct():
    result = evaluate_regression(RegressionEvaluationRequest(y_true=[1, 2, 3], y_pred=[1, 2, 4]))
    assert result["evaluation"]["metrics"]["mae"] == pytest.approx(1 / 3)
    assert result["evaluation"]["metrics"]["rmse"] == pytest.approx(math.sqrt(1 / 3))


def test_classification_confusion_and_f1():
    result = evaluate_classification(ClassificationEvaluationRequest(y_true=["1", "1", "0", "0"], y_pred=["1", "0", "1", "0"], positive_label="1"))
    metrics = result["evaluation"]["metrics"]
    assert metrics["accuracy"] == 0.5
    assert metrics["confusionMatrix"] == {"truePositive": 1, "trueNegative": 1, "falsePositive": 1, "falseNegative": 1}


def test_cross_validation_summary_selects_lowest_rmse():
    result = summarize_cross_validation(CrossValidationRequest(folds=[{"rmse": .5}, {"rmse": .3}, {"rmse": .4}], primary_metric="rmse", direction="minimize"))
    assert result["summary"]["bestFold"] == 2
    assert result["summary"]["mean"] == 0.4


def test_linear_forecast_follows_trend():
    result = build_linear_trend_forecast(ForecastRequest(values=[2, 4, 6, 8], horizon=2))
    assert result["forecast"]["predictions"][0]["value"] == 10.0
    assert result["forecast"]["predictions"][1]["value"] == 12.0


def test_drift_audit_flags_shift():
    result = audit_drift(DriftAuditRequest(reference=[0, 0.1, -0.1, 0.05], current=[3, 3.1, 2.9, 3.05], warning_threshold=.1, critical_threshold=.2))
    assert result["audit"]["severity"] == "critical"
    assert result["audit"]["populationStabilityIndex"] > .2


def test_leakage_audit_blocks_target_and_post_outcome():
    result = audit_leakage(LeakageAuditRequest(features=["age", "outcome", "approved_after_review"], target="outcome", known_post_outcome_fields=["approved_after_review"]))
    assert result["audit"]["status"] == "blocked"
    assert result["audit"]["criticalCount"] == 2


def test_fairness_audit_reports_group_gap_and_small_groups():
    result = audit_fairness(FairnessAuditRequest(groups=[FairnessGroup(group="A", count=100, positive_rate=.6), FairnessGroup(group="B", count=10, positive_rate=.3)], minimum_group_size=30, warning_gap=.1, critical_gap=.2))
    assert result["audit"]["severity"] == "critical"
    assert result["audit"]["smallGroups"] == ["B"]
    assert result["audit"]["humanReviewRequired"] is True


def test_model_card_downgrades_unreviewed_approval():
    result = build_model_card(ModelCardRequest(model_name="Forecast", task="regression", algorithm="linear", approval_status="approved"))
    assert result["modelCard"]["approvalStatus"] == "review-required"
    assert result["modelCard"]["warnings"]
    assert result["modelCard"]["modelCardHash"]


def test_reproducibility_plan_contains_all_language_contracts():
    result = build_reproducibility_plan(ReproducibilityRequest(coefficients=[1.5, -.25], intercept=.5))
    plan = result["plan"]
    assert set(plan["snippets"]) == {"python", "r", "javascript", "rust"}
    assert plan["inputOrderingRequired"] is True


def test_high_stakes_experiment_requires_review_controls():
    result = build_experiment_scaffold(ExperimentScaffoldRequest(task="classification", target="eligible", high_stakes_context=True))
    assert result["experiment"]["humanReviewRequired"] is True
    assert any("qualified review" in control for control in result["experiment"]["controls"])


def test_supervised_scaffold_requires_target():
    with pytest.raises(ValueError):
        build_experiment_scaffold(ExperimentScaffoldRequest(task="deep-learning", target=""))
