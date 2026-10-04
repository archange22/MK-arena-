"""Discord actions tool (channels, roles, messages)"""
class DiscordTool:
    def __init__(self, client=None):
        self.client = client

    async def send_message(self, channel_id: int, content: str):
        if self.client:
            ch = self.client.get_channel(channel_id)
            if ch:
                await ch.send(content)
