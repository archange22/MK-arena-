import logging
import discord
from discord.ext import commands
from discord import app_commands
from bot.permissions import is_authorized
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
        self._register_commands()
        await self.tree.sync()
        logger.info("Commandes slash et préfixe synchronisées avec succès.")

    async def on_ready(self):
        logger.info(f"Connecté en tant que {self.user} (ID: {self.user.id})")
        logger.info(f"Préfixe de commande actif : '{self.command_prefix}'")
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.competing,
                name=f"MK ARENA • CODM ({self.command_prefix}aide)"
            )
        )

    def _build_help_embed(self) -> discord.Embed:
        p = self.command_prefix
        embed = discord.Embed(
            title="📖 Aide • Chacha Live (MK ARENA)",
            description=f"Bot officiel MK ARENA. Toutes les commandes fonctionnent avec le préfixe `{p}` et en commandes Slash `/`.",
            color=0x5865F2
        )
        embed.add_field(
            name="Commandes disponibles",
            value=(
                f"• `{p}ping` ou `/ping` : Afficher la latence du bot en millisecondes\n"
                f"• `{p}aide` ou `/aide` : Afficher ce guide d'aide\n"
            ),
            inline=False
        )
        embed.set_footer(text=f"Préfixe actif : {p} • MK ARENA")
        return embed

    def _register_commands(self):
        @self.tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
            logger.error("Erreur commande slash %s: %s", getattr(interaction.command, "name", "inconnue"), error)
            msg = f"❌ Erreur lors de l'exécution : {error}"
            try:
                if interaction.response.is_done():
                    await interaction.followup.send(msg, ephemeral=True)
                else:
                    await interaction.response.send_message(msg, ephemeral=True)
            except Exception:
                pass

        # Commandes Slash
        @self.tree.command(name="ping", description="Vérifier la latence du bot.")
        async def slash_ping(interaction: discord.Interaction):
            latency = round(self.latency * 1000)
            await interaction.response.send_message(f"🏓 Pong ! Latence : **{latency}ms**.")

        @self.tree.command(name="aide", description="Afficher l'aide et les commandes disponibles.")
        async def slash_help(interaction: discord.Interaction):
            embed = self._build_help_embed()
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # Commandes Préfixes (!)
        @self.command(name="ping")
        async def prefix_ping(ctx: commands.Context):
            latency = round(self.latency * 1000)
            await ctx.send(f"🏓 Pong ! Latence : **{latency}ms**.")

        @self.command(name="aide", aliases=["help"])
        async def prefix_help(ctx: commands.Context):
            embed = self._build_help_embed()
            await ctx.send(embed=embed)
