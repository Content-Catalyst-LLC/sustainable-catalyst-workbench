from fastapi.testclient import TestClient
from app.main import app
from app.engines.article_embeds import article_formula_embed_analyzer, infer_formula_embed

client = TestClient(app)


def test_formula_embed_planner_recommends_graph_embed():
    out = article_formula_embed_analyzer({
        'formula': 'y = a*sin(b*x)',
        'article_title': 'Oscillation and Systems Modeling',
        'display': 'inline'
    })
    assert out['ok'] is True
    assert out['version'] == '1.6.0'
    assert out['values']['embed_kind'] == 'graph'
    assert 'sc_workbench_formula_calculator' in out['values']['near_formula_shortcode']
    assert 'formula=' in out['values']['near_formula_shortcode']
    assert out['shortcodes']['drawer']


def test_formula_embed_planner_recommends_engineering_embed():
    out = infer_formula_embed('sigma = F/A', 'normal stress force area engineering')
    assert out['embed_kind'] == 'engineering'
    assert 'mechanical-systems-engineering-tool' in out['recommended_tool_ids']


def test_formula_embed_api_endpoint():
    res = client.post('/articles/formula-embed', json={
        'formula': 'NPV = sum(CF_t/(1+r)^t)',
        'context': 'discount rate return investment payback',
        'display': 'drawer'
    })
    assert res.status_code == 200
    data = res.json()
    assert data['ok'] is True
    assert data['values']['recommended_tool_id']
    assert 'drawer' in data['shortcodes']
    assert data['values']['suggested_placement']
