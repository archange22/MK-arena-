import logging
import discord
from discord.ext import commands
from discord import app_commands
import config

logger = logging.getLogger("bot")

class ChachaBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(
            command_prefix=config.PREFIX,
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        # Charger les extensions Cogs modulaires
        extensions = [
            "cogs.general",
            "cogs.tickets",
        ]
        for ext in extensions:
            try:
                await self.load_extension(ext)
                logger.info("Extension chargée : %s", ext)
            except Exception as e:
                logger.error("Impossible de charger l'extension %s : %s", ext, e)

        # Enregistrement des vues persistantes (boutons opérationnels après redémarrage)
        from cogs.tickets import TicketPanelView, TicketControlView
        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())

        # Synchronisation globale des commandes slash
        try:
            await self.tree.sync()
            logger.info("Commandes slash synchronisées avec succès.")
        except Exception as e:
            logger.error("Erreur lors de la synchronisation des commandes slash : %s", e)

    async def on_ready(self):
        logger.info("Connecté en tant que %s (ID: %s)", self.user, self.user.id)
        logger.info("Préfixe de commande actif : '%s'", self.command_prefix)
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.competing,
                name=f"MK ARENA • CODM ({self.command_prefix}aide)"
            )
        )
