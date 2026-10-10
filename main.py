import os
import logging

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("mk-arena")

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def setup_hook():
    """Synchronise slash commands when the bot starts."""
    try:
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            log.info("Synchronised %s slash commands to guild %s", len(synced), GUILD_ID)
        else:
            synced = await bot.tree.sync()
            log.info("Synchronised %s global slash commands", len(synced))
    except (ValueError, discord.DiscordException):
        log.exception("Could not synchronise slash commands")
        raise


@bot.event
async def on_ready():
    log.info("MK Arena connected as %s (ID: %s)", bot.user, bot.user.id if bot.user else "unknown")


@bot.tree.command(name="ping", description="Vérifie si MK Arena répond")
async def slash_ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong ! Latence : {latency} ms")


@bot.tree.command(name="aide", description="Affiche les commandes disponibles")
async def slash_aide(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 MK Arena | Aide",
        description="Commandes actuellement disponibles :",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="/ping", value="Vérifie la latence du bot.", inline=False)
    embed.add_field(name="/aide", value="Affiche cette aide.", inline=False)
    embed.set_footer(text="MK Arena • Version de base")
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.command(name="ping")
async def prefix_ping(ctx: commands.Context):
    await ctx.reply(f"🏓 Pong ! Latence : {round(bot.latency * 1000)} ms")


@bot.command(name="aide", aliases=["help"])
async def prefix_aide(ctx: commands.Context):
    await ctx.reply("Commandes : /ping, /aide, !ping, !aide")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "La variable DISCORD_TOKEN est absente. Ajoute-la dans les variables d'environnement Render."
        )
    bot.run(TOKEN, log_handler=None)
