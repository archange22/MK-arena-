from ai.engine import NovaEngine

class Dummy: pass

def test_nova_detection():
    e = NovaEngine(Dummy(), Dummy())
    assert e.is_called("NOVA bonjour")
    assert e.is_called("NoVa bonjour")
    assert not e.is_called("renova")
