"""Real-time WebSocket event broadcaster"""
import json
from typing import Set

class WebSocketBroadcaster:
    def __init__(self):
        self.connections: Set = set()

    def add_client(self, client):
        self.connections.add(client)

    def remove_client(self, client):
        self.connections.discard(client)

    async def broadcast(self, event_type: str, data: dict):
        payload = json.dumps({"event": event_type, "data": data})
        for c in list(self.connections):
            try:
                await c.send_text(payload)
            except Exception:
                self.connections.discard(c)
