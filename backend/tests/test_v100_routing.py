from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_v100():
    data = client.get('/health').json()
    assert data['ok'] is True
    assert data['version'] in {'1.3.0', '1.4.0'}

def test_shortcode_recommend_includes_display_mode():
    payload = {
        'article_title': 'Feedback Loops and Risk',
        'article_slug': 'feedback-loops-risk',
        'equations': ['x_{t+1} = f(x_t, u_t)', 'R = P(H) \\times C(H)'],
        'context': 'systems modeling risk resilience feedback',
        'preferred_display': 'drawer',
    }
    data = client.post('/routing/shortcode-recommend', json=payload).json()
    assert data['ok'] is True
    assert 'display="drawer"' in data['embed_shortcode']
    assert data['display_mode'] == 'drawer'
    assert 'suggested_placement' in data
