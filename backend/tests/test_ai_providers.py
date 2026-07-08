from app.core.ai_provider import provider_status, answer_question


def test_supported_provider_status_contains_clean_stack():
    status = provider_status()
    assert status['supported_providers'] == ['disabled', 'gemini', 'deepseek', 'openai']


def test_gemini_without_key_falls_back_to_registry():
    out = answer_question(
        'How should Sustainable Catalyst analyze environmental monitoring data?',
        'research-library',
        provider_override='gemini',
        provider_keys={},
    )
    assert out['ok'] is True
    assert out['provider'] == 'gemini'
    assert 'provider key' in out['answer'].lower()


def test_deepseek_without_key_falls_back_to_registry():
    out = answer_question(
        'Map an international law issue about transboundary water pollution.',
        'research-library',
        provider_override='deepseek',
        provider_keys={},
    )
    assert out['ok'] is True
    assert out['provider'] == 'deepseek'
    assert 'provider key' in out['answer'].lower()
