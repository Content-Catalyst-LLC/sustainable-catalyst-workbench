from backend.app.v440 import (
    BenchmarkInput, ExperimentMatrixInput, TrialRecord, TrialSummaryInput,
    CandidateComparisonInput, RegressionInput, ReproducibilityInput,
    LeaderboardEntry, LeaderboardInput, EvaluationGateInput,
    EvaluationPackageInput, status_record, normalize_benchmark,
    build_experiment_matrix, summarize_trials, compare_candidates,
    detect_regression, reproducibility_audit, build_leaderboard,
    build_evaluation_gate, build_evaluation_package,
)


def trial(candidate, value, seed=42, **kwargs):
    data=dict(candidate=candidate, metricValue=value, seed=seed, datasetHash="d", protocolHash="p", runtime="python", environmentHash="e")
    data.update(kwargs)
    return TrialRecord(**data)


def test_status_boundaries():
    result=status_record(); assert result["version"]=="4.4.0"; assert result["expectedStudioCount"]==26; assert not result["automaticExperimentExecutionAuthorized"]; assert not result["automaticLeaderboardPublicationAuthorized"]


def test_benchmark_stable_hash():
    payload=BenchmarkInput(title="Accuracy",metricName="rmse",direction="minimize",datasetHash="d",protocolHash="p")
    first=normalize_benchmark(payload); second=normalize_benchmark(payload); assert first["benchmarkHash"]==second["benchmarkHash"]; assert first["readyForExecutionPlanning"]


def test_high_stakes_benchmark_requires_review():
    result=normalize_benchmark(BenchmarkInput(title="Safety",metricName="failure-rate",direction="minimize",highStakes=True)); assert result["humanReviewRequired"]; assert any(x["code"]=="professional-review-required" for x in result["findings"])


def test_experiment_matrix_cartesian_product():
    payload=ExperimentMatrixInput(benchmarkId="b",candidates=["a","b"],parameterGrid={"mode":["x","y"]},seeds=[1,2],datasets=["d"])
    result=build_experiment_matrix(payload); assert result["projectedRuns"]==8; assert len(result["runs"])==8; assert result["ready"]


def test_experiment_matrix_blocks_limit():
    payload=ExperimentMatrixInput(benchmarkId="b",candidates=["a","b"],parameterGrid={"mode":[1,2,3]},seeds=[1,2],datasets=["d"],maxRuns=5)
    result=build_experiment_matrix(payload); assert not result["ready"]; assert result["runs"]==[]; assert any(x["code"]=="matrix-limit-exceeded" for x in result["findings"])


def test_trial_summary_statistics():
    result=summarize_trials(TrialSummaryInput(benchmarkId="b",metricName="score",trials=[trial("a",1),trial("a",3,43),trial("b",2)])); a=result["candidates"]["a"]; assert a["mean"]==2; assert a["median"]==2; assert a["minimum"]==1; assert a["maximum"]==3


def test_trial_summary_counts_failures():
    result=summarize_trials(TrialSummaryInput(benchmarkId="b",metricName="score",trials=[trial("a",1),trial("a",9,43,success=False)])); assert result["candidates"]["a"]["count"]==1; assert result["candidates"]["a"]["failureCount"]==1


def test_candidate_comparison_maximize():
    result=compare_candidates(CandidateComparisonInput(baseline={"mean":0.8,"stdev":0.02},candidate={"mean":0.85,"stdev":0.02},practicalThreshold=0.01)); assert result["result"]=="improved"; assert result["practicallySignificant"]; assert not result["automaticBaselineReplacementAuthorized"]


def test_candidate_comparison_minimize():
    result=compare_candidates(CandidateComparisonInput(baseline={"mean":10},candidate={"mean":8},direction="minimize",practicalThreshold=1)); assert result["alignedImprovement"]==2; assert result["result"]=="improved"


def test_regression_detection_blocks_high():
    result=detect_regression(RegressionInput(baselineValue=0.9,currentValue=0.8,direction="maximize",absoluteTolerance=0.01,percentTolerance=1,severity="high",label="accuracy")); assert result["regression"]; assert result["releaseBlocking"]


def test_regression_within_tolerance():
    result=detect_regression(RegressionInput(baselineValue=100,currentValue=99.5,direction="maximize",absoluteTolerance=1,percentTolerance=1)); assert not result["regression"]; assert result["severity"]=="none"


def test_reproducibility_requires_metadata():
    result=reproducibility_audit(ReproducibilityInput(trials=[TrialRecord(candidate="a",metricValue=1)])); assert not result["ready"]; assert any(x["code"]=="missing-seed" for x in result["findings"])


def test_reproducibility_detects_repeatability_failure():
    result=reproducibility_audit(ReproducibilityInput(trials=[trial("a",1),trial("a",1.1)],metricTolerance=0.01)); assert not result["ready"]; assert any(x["code"]=="repeatability-failure" for x in result["findings"])


def test_leaderboard_direction_and_ties():
    payload=LeaderboardInput(benchmarkId="b",metricName="rmse",direction="minimize",entries=[LeaderboardEntry(candidate="z",metricValue=2),LeaderboardEntry(candidate="a",metricValue=1),LeaderboardEntry(candidate="b",metricValue=1)])
    result=build_leaderboard(payload); assert [x["candidate"] for x in result["rows"]]==["a","b","z"]; assert result["rows"][0]["rank"]==result["rows"][1]["rank"]==1; assert result["provisional"]


def test_gate_blocks_without_reproducibility_and_approval():
    result=build_evaluation_gate(EvaluationGateInput(benchmark={"benchmarkId":"b"},reproducibility={"ready":False},requiredArtifacts=["summary"],availableArtifacts=[])); assert not result["ready"]; codes={x["code"] for x in result["blockers"]}; assert "reproducibility-not-ready" in codes; assert "human-approval-required" in codes


def test_gate_passes_human_controlled_evaluation():
    result=build_evaluation_gate(EvaluationGateInput(benchmark={"benchmarkId":"b"},reproducibility={"ready":True},requiredArtifacts=["summary"],availableArtifacts=["summary"],humanApproval=True,approver="Reviewer")); assert result["ready"]; assert result["state"]=="approved-for-human-controlled-use"; assert not result["automaticReleaseApprovalAuthorized"]


def test_evaluation_package_is_portable_and_nonexecuting():
    result=build_evaluation_package(EvaluationPackageInput(benchmark={},matrix={},summaries={})); assert result["portable"]; assert len(result["packageHash"])==64; assert not result["automaticExperimentExecutionAuthorized"]; assert not result["automaticLeaderboardPublicationAuthorized"]
