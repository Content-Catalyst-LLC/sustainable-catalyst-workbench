from app.engines.feature_built_engines import FEATURE_TOOL_IDS, feature_built_tool
from app.core.model_registry import get_tool


def test_v098_all_feature_tools_registered():
    assert len(FEATURE_TOOL_IDS) == 59
    missing = [tool_id for tool_id in FEATURE_TOOL_IDS if get_tool(tool_id) is None]
    assert missing == []


def test_v098_sample_feature_tools_run():
    samples = [
        'weighted-composite-index-builder',
        'predictive-forecasting-suite',
        'stock-flow-systems-simulator',
        'environmental-monitoring-threshold-tool',
        'risk-impact-resilience-calculator',
        'graphable-function-explorer',
        'electrical-circuit-tool',
        'lab-assay-dose-response-tool',
    ]
    for tool_id in samples:
        out = feature_built_tool(tool_id, {})
        assert out['ok'] is True
        assert out['tool']
        assert 'values' in out
