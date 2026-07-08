from app.engines.runner import run_tool


def test_advanced_physical_engineering_and_lab_tools_run():
    for tool_id in [
        'nuclear-physics-calculator', 'particle-physics-calculator', 'neurophysics-calculator',
        'rocket-science-calculator', 'electronics-engineering-calculator', 'rf-antenna-calculator',
        'full-stack-engineering-tool', 'lab-science-calculator', 'clinical-research-calculator'
    ]:
        out = run_tool(tool_id, {}, 'guided')
        assert out['ok'] is True
        assert out['values']
        assert 'disclaimer' in out
