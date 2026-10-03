from ai.engine import NovaEngine


class Dummy:
    pass


def test_nova_detection():
    engine = NovaEngine(Dummy(), Dummy())
    assert engine.is_called("nova bonjour")
    assert engine.is_called("NOVA bonjour")
    assert engine.is_called("NoVa bonjour")
    assert engine.is_called("tu peux demander à nova ?")
    assert not engine.is_called("renova")
    assert not engine.is_called("novaissance")


def test_remove_call():
    engine = NovaEngine(Dummy(), Dummy())
    assert engine.remove_call("NOVA bonjour") == "bonjour"
    assert engine.remove_call("NoVa c'est quoi le tournoi ?") == "c'est quoi le tournoi ?"
