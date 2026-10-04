import logging
import discord

logger = logging.getLogger(__name__)


class NovaEvents:
    def __init__(self, client):
        self.client = client

    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot or not after.guild:
            return
        # Re-synchroniser si dans la catégorie tournoi
        category_id = getattr(self.client.settings, "tournament_category_id", None)
        if category_id and after.channel.category_id == category_id:
            self.client.indexer.index_message(
                guild_id=after.guild.id,
                channel_id=after.channel.id,
                message_id=after.id,
                content=after.content,
            )
