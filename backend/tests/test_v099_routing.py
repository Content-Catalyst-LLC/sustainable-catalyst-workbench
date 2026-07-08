from app.routers.routing import recommend_shortcode, ShortcodeRecommendRequest


def test_shortcode_recommendation_for_recurrence():
    res = recommend_shortcode(ShortcodeRecommendRequest(
        article_title='Feedback and Stock Flow Modeling',
        article_slug='feedback-stock-flow-modeling',
        equations=['S_{t+1} = S_t + I_t - O_t', 'x_{t+1}=f(x_t,u_t)'],
        context='stock flow feedback systems dynamics'
    ))
    assert res['ok'] is True
    assert 'sc_workbench' in res['embed_shortcode']
    assert res['recommended_tool_id']
    assert res['confidence'] in {'high', 'medium', 'low'}
