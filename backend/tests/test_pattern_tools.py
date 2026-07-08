from app.engines.runner import run_tool
from app.core.model_registry import list_tools

def test_pattern_domain_present():
    domains = {t['domain'] for t in list_tools()}
    assert 'Pattern, Geometry, Design, Music, and AI' in domains

def test_music_frequency_runs():
    out = run_tool('music-frequency-calculator', {'mode':'midi_to_frequency','midi':'69'})
    assert out['ok'] is True
    assert round(out['values']['frequency_hz'], 4) == 440.0

def test_color_contrast_runs():
    out = run_tool('color-contrast-calculator', {'foreground':'#111111','background':'#ffffff'})
    assert out['ok'] is True
    assert out['values']['contrast_ratio'] > 10

def test_vector_geometry_runs():
    out = run_tool('vector-geometry-calculator', {'a':'1,0','b':'0,1'})
    assert out['ok'] is True
    assert round(out['values']['angle_degrees']) == 90

def test_ai_metrics_runs():
    out = run_tool('ai-classification-metrics-calculator', {'tp':50,'fp':10,'tn':80,'fn':5})
    assert out['ok'] is True
    assert out['values']['f1'] > 0.8
