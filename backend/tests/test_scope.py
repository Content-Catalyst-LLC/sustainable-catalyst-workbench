from app.core.scope_gate import is_in_scope

def test_scope_energy():
    ok, _ = is_in_scope("calculate energy emissions")
    assert ok

def test_scope_out():
    ok, _ = is_in_scope("celebrity gossip")
    assert not ok
