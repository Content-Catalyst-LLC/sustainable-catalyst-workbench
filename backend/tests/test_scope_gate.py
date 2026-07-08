from app.core.scope_gate import check_scope


def test_scope_gate_accepts_site_topic():
    result = check_scope("How should I evaluate AI governance risk?")
    assert result["in_scope"] is True


def test_scope_gate_rejects_unrelated_topic():
    result = check_scope("What celebrity gossip happened today?")
    assert result["in_scope"] is False
