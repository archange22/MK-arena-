import logging
import discord
from discord.ext import commands
from discord import app_commands

logger = logging.getLogger("cogs.general")

class General(commands.Cog):
    """Commandes générales et utilitaires du bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_help_embed(self) -> discord.Embed:
        p = self.bot.command_prefix
        embed = discord.Embed(
            title="📖 Aide • MK ARENA",
            description=f"Bot officiel MK ARENA. Les commandes fonctionnent avec le préfixe `{p}` et en commandes Slash `/`.",
            color=0x5865F2
        )
        embed.add_field(
            name="Commandes Générales",
            value=(
                f"• `{p}ping` ou `/ping` : Latence du bot\n"
                f"• `{p}aide` ou `/aide` : Afficher ce guide d'aide\n"
            ),
            inline=False
        )
        embed.add_field(
            name="Commandes Tickets (Staff)",
            value=(
                f"• `{p}ticket-setup` ou `/ticket-setup` : Déployer le panneau de tickets (Inscriptions, Clan, Staff, Support)\n"
                f"• `{p}close` ou `/close` : Fermer le ticket actif\n"
            ),
            inline=False
        )
        embed.set_footer(text=f"Préfixe actif : {p} • MK ARENA")
        return embed

    @app_commands.command(name="ping", description="Vérifier la latence du bot.")
    async def slash_ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong ! Latence : **{latency}ms**.")

    @commands.command(name="ping")
    async def prefix_ping(self, ctx: commands.Context):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"🏓 Pong ! Latence : **{latency}ms**.")

    @app_commands.command(name="aide", description="Afficher l'aide et les commandes.")
    async def slash_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._build_help_embed(), ephemeral=True)

    @commands.command(name="aide", aliases=["help"])
    async def prefix_help(self, ctx: commands.Context):
        await ctx.send(embed=self._build_help_embed())

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
