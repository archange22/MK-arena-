import logging
import discord
from discord import app_commands
from bot.permissions import is_authorized

logger = logging.getLogger("bot")

class ChachaBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self._register_commands()
        await self.tree.sync()
        logger.info("Commandes synchronisées avec succès.")

    async def on_ready(self):
        logger.info(f"Connecté en tant que {self.user} (ID: {self.user.id})")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.competing,
                name="MK ARENA • CODM"
            )
        )

    def _register_commands(self):
        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            logger.error("Erreur commande %s: %s", getattr(interaction.command, "name", "inconnue"), error)
            msg = f"❌ Erreur lors de l'exécution : {error}"
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await interaction.response.send_message(msg, ephemeral=True)
            except Exception:
                pass

        @self.tree.command(name="ping", description="Vérifier la latence du bot.")
        async def ping_cmd(interaction: discord.Interaction):
            latency = round(self.latency * 1000)
            await interaction.response.send_message(f"🏓 Pong ! Latence : **{latency}ms**.")

        @self.tree.command(name="aide", description="Afficher l'aide et les commandes disponibles.")
        async def help_cmd(interaction: discord.Interaction):
            embed = discord.Embed(
                title="📖 Aide • Chacha Live (MK ARENA)",
                description="Bienvenue sur le bot officiel MK ARENA. Le bot a été remis à neuf pour une performance optimale.",
                color=0x5865F2
            )
            embed.add_field(name="Commandes générales", value="`/ping` : Latence du bot\n`/aide` : Afficher ce message", inline=False)
            embed.set_footer(text="MK ARENA • Bot nouvelle génération")
            await interaction.response.send_message(embed=embed, ephemeral=True)
