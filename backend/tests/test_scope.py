from app.core.scope_gate import classify_scope

def test_scope_includes_engineering():
    assert classify_scope('beam bending in sustainable architecture')['in_scope'] is True

def test_scope_rejects_unrelated():
    assert classify_scope('celebrity gossip about actors')['in_scope'] is False
