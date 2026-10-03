import tempfile, os
from memory.database import Database
from memory.conversation import ConversationMemory

def test_memory():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    try:
        db = Database(path)
        db.initialize()
        mem = ConversationMemory(db)
        mem.add(1, "user", "bonjour")
        assert mem.recent(1)[0]["content"] == "bonjour"
    finally:
        os.remove(path)
