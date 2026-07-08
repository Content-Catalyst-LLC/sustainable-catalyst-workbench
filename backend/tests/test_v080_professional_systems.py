from app.engines.runner import run_tool
from app.core.model_registry import list_tools


def test_v080_registry_growth_and_major_domains():
    tools = list_tools()
    ids = {t['id'] for t in tools}
    assert len(tools) >= 68
    assert 'predictive-analytics-forecasting-tool' in ids
    assert 'economics-forecasting-scenario-tool' in ids
    assert 'fpga-digital-systems-tool' in ids
    assert 'structural-engineering-tool' in ids
    assert 'astrophysics-research-calculator' in ids


def test_predictive_and_economics_tools_run():
    for tool_id in ['predictive-analytics-forecasting-tool','time-series-diagnostics-tool','economics-forecasting-scenario-tool','econometrics-policy-model-tool']:
        out = run_tool(tool_id, {}, 'analyst')
        assert out['ok'] is True
        assert out['values']
        assert out['graphs']


def test_professional_systems_tools_run():
    for tool_id in ['fpga-digital-systems-tool','power-systems-engineering-tool','mechanical-systems-engineering-tool','structural-engineering-tool','civil-infrastructure-planning-tool','urban-planning-analytics-tool','architecture-building-science-tool','astrophysics-research-calculator']:
        out = run_tool(tool_id, {}, 'expert')
        assert out['ok'] is True
        assert out['values']
        assert 'disclaimer' in out
