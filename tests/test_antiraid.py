from security.antiraid import AntiRaidManager
import time

def test_antiraid_detection():
    manager = AntiRaidManager(max_joins=3, window_seconds=5)
    now = time.time()
    
    # 2 joins -> pas de raid
    assert not manager.record_join(1, timestamp=now)
    assert not manager.record_join(1, timestamp=now + 1)
    assert not manager.is_in_lockdown(1)

    # 3e join dans la fenêtre -> raid déclenché !
    assert manager.record_join(1, timestamp=now + 2)
    assert manager.is_in_lockdown(1)
