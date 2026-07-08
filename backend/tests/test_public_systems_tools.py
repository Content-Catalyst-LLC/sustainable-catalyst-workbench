from app.engines.runner import run_tool


def test_environmental_monitoring_qaqc():
    out = run_tool('environmental-monitoring-qaqc-tool', {'values':'1,1.1,1.2,9,1.3','lower_threshold':'0','upper_threshold':'5'})
    assert out['ok'] is True
    assert out['values']['threshold_exceedances'] >= 1
    assert out['graphs']


def test_global_impact_matrix():
    out = run_tool('global-impact-assessment-matrix', {'scores':'climate=4;health=3;rights=4;uncertainty=5'})
    assert out['ok'] is True
    assert out['values']['weighted_score'] > 0


def test_law_health_metaphysics_tools():
    for tool_id in ['international-law-issue-mapper','legal-traditions-comparator','health-medical-public-health-tool','metaphysics-framework-tool']:
        out = run_tool(tool_id, {})
        assert out['ok'] is True
