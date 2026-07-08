from app.engines.runner import run_tool
from app.core.model_registry import list_tools


def test_expanded_research_tool_registry():
    tools = list_tools()
    ids = {t['id'] for t in tools}
    assert len(tools) >= 100
    for tool_id in ['cognitive-psychology-tool','behavioral-economics-tool','systems-thinking-tool','story-myth-meaning-tool','predictive-modeling-tool','limits-to-growth-system-dynamics-tool']:
        assert tool_id in ids


def test_psychology_thinking_meaning_systems_run():
    for tool_id in ['cognitive-psychology-tool','choice-architecture-nudging-tool','moral-psychology-tool','systems-thinking-tool','futures-thinking-tool','beauty-aesthetics-meaning-tool','systems-modeling-tool','predictive-modeling-tool']:
        out = run_tool(tool_id, {}, 'analyst')
        assert out['ok'] is True
        assert out['values']
        assert out['graphs']


def test_limits_to_growth_runs():
    out = run_tool('limits-to-growth-system-dynamics-tool', {}, 'expert')
    assert out['ok'] is True
    assert out['graphs']
    assert 'final_resource_index' in out['values']
