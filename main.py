import os
import logging
from datetime import timedelta

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("mk-arena")

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
# À activer aussi dans Discord Developer Portal > Bot > Privileged Gateway Intents.
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    log.info(
        "MK Arena connected as %s (ID: %s) in %s server(s)",
        bot.user,
        bot.user.id if bot.user else "unknown",
        len(bot.guilds),
    )


@bot.command(name="ping", description="Vérifie si MK Arena répond")
async def ping(ctx: commands.Context):
    """Commande préfixe !ping."""
    await ctx.send(f"🏓 Pong ! Latence : {round(bot.latency * 1000)} ms")


@bot.command(name="aide", description="Affiche la liste des commandes")
async def aide(ctx: commands.Context):
    """Commande préfixe !aide."""
    embed = discord.Embed(
        title="🤖 MK Arena | Aide",
        description="Commandes MK Arena utilisant le préfixe !.",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Général", value="`!ping`\n`!aide`\n`!serveur`\n`!userinfo [membre]`\n`!avatar [membre]`", inline=False)
    embed.add_field(name="Modération", value="`!clear 10`\n`!kick @membre raison`\n`!ban @membre raison`\n`!timeout @membre minutes raison`\n`!slowmode secondes`\n`!lock`\n`!unlock`", inline=False)
    embed.set_footer(text="MK Arena • Commandes préfixe !")
    await ctx.send(embed=embed)


@bot.command(name="serveur", description="Affiche les informations du serveur")
@commands.guild_only()
async def serveur(ctx: commands.Context):
    guild = ctx.guild
    embed = discord.Embed(title=f"📊 {guild.name}", color=discord.Color.blurple())
    embed.add_field(name="Membres", value=str(guild.member_count or "Inconnu"))
    embed.add_field(name="Salons", value=str(len(guild.channels)))
    embed.add_field(name="Créé le", value=discord.utils.format_dt(guild.created_at, style="D"), inline=False)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)


@bot.command(name="userinfo", description="Affiche les informations d'un membre")
@commands.guild_only()
async def userinfo(ctx: commands.Context, membre: discord.Member = None):
    membre = membre or ctx.author
    embed = discord.Embed(title=f"👤 {membre}", color=discord.Color.blurple())
    embed.add_field(name="ID", value=str(membre.id), inline=False)
    embed.add_field(name="Compte créé", value=discord.utils.format_dt(membre.created_at, style="D"), inline=True)
    if membre.joined_at:
        embed.add_field(name="A rejoint le serveur", value=discord.utils.format_dt(membre.joined_at, style="D"), inline=True)
    embed.set_thumbnail(url=membre.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="avatar", description="Affiche l'avatar d'un membre")
async def avatar(ctx: commands.Context, membre: discord.Member = None):
    membre = membre or ctx.author
    embed = discord.Embed(title=f"Avatar de {membre}", color=discord.Color.blurple())
    embed.set_image(url=membre.display_avatar.url)
    await ctx.send(embed=embed)


@bot.command(name="clear", description="Supprime un nombre de messages")
@commands.has_permissions(manage_messages=True)
@commands.bot_has_permissions(manage_messages=True, read_message_history=True)
@commands.guild_only()
async def clear(ctx: commands.Context, nombre: int):
    if nombre < 1 or nombre > 100:
        await ctx.send("Choisis un nombre entre 1 et 100.")
        return
    deleted = await ctx.channel.purge(limit=nombre + 1)
    await ctx.send(f"🧹 {max(0, len(deleted) - 1)} message(s) supprimé(s).", delete_after=5)


@bot.command(name="kick", description="Expulse un membre du serveur")
@commands.has_permissions(kick_members=True)
@commands.bot_has_permissions(kick_members=True)
@commands.guild_only()
async def kick(ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
    if membre == ctx.author:
        await ctx.send("Tu ne peux pas t'expulser toi-même.")
        return
    await membre.kick(reason=f"{raison} | Modérateur : {ctx.author}")
    await ctx.send(f"👢 {membre.mention} a été expulsé. Raison : {raison}")


@bot.command(name="ban", description="Bannit un membre du serveur")
@commands.has_permissions(ban_members=True)
@commands.bot_has_permissions(ban_members=True)
@commands.guild_only()
async def ban(ctx: commands.Context, membre: discord.Member, *, raison: str = "Aucune raison précisée"):
    if membre == ctx.author:
        await ctx.send("Tu ne peux pas te bannir toi-même.")
        return
    await membre.ban(reason=f"{raison} | Modérateur : {ctx.author}")
    await ctx.send(f"🔨 {membre} a été banni. Raison : {raison}")


@bot.command(name="timeout", description="Met un membre en timeout pour X minutes")
@commands.has_permissions(moderate_members=True)
@commands.bot_has_permissions(moderate_members=True)
@commands.guild_only()
async def timeout(ctx: commands.Context, membre: discord.Member, minutes: int, *, raison: str = "Aucune raison précisée"):
    if minutes < 1 or minutes > 40320:
        await ctx.send("La durée doit être comprise entre 1 minute et 28 jours.")
        return
    if membre == ctx.author:
        await ctx.send("Tu ne peux pas te mettre en timeout avec cette commande.")
        return
    await membre.timeout(timedelta(minutes=minutes), reason=f"{raison} | Modérateur : {ctx.author}")
    await ctx.send(f"⏳ {membre.mention} est en timeout pendant {minutes} minute(s). Raison : {raison}")


@bot.command(name="slowmode", description="Configure le mode lent du salon")
@commands.has_permissions(manage_channels=True)
@commands.bot_has_permissions(manage_channels=True)
@commands.guild_only()
async def slowmode(ctx: commands.Context, secondes: int):
    if secondes < 0 or secondes > 21600:
        await ctx.send("Choisis une durée entre 0 et 21600 secondes.")
        return
    await ctx.channel.edit(slowmode_delay=secondes)
    await ctx.send(f"🐢 Mode lent réglé sur {secondes} seconde(s).")


async def set_channel_lock(ctx: commands.Context, locked: bool):
    channel = ctx.channel
    overwrite = channel.overwrites_for(ctx.guild.default_role)
    overwrite.send_messages = not locked
    await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
    await ctx.send("🔒 Salon verrouillé." if locked else "🔓 Salon déverrouillé.")


@bot.command(name="lock", description="Verrouille le salon actuel")
@commands.has_permissions(manage_channels=True)
@commands.bot_has_permissions(manage_channels=True)
@commands.guild_only()
async def lock(ctx: commands.Context):
    await set_channel_lock(ctx, True)


@bot.command(name="unlock", description="Déverrouille le salon actuel")
@commands.has_permissions(manage_channels=True)
@commands.bot_has_permissions(manage_channels=True)
@commands.guild_only()
async def unlock(ctx: commands.Context):
    await set_channel_lock(ctx, False)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        message = "❌ Tu n'as pas les permissions nécessaires pour cette commande."
    elif isinstance(error, commands.BotMissingPermissions):
        message = "❌ Il me manque des permissions pour faire ça."
    elif isinstance(error, commands.MissingRequiredArgument):
        message = f"❌ Argument manquant : `{error.param.name}`."
    elif isinstance(error, commands.BadArgument):
        message = "❌ Argument invalide. Vérifie le membre et les valeurs indiquées."
    elif isinstance(error, commands.NoPrivateMessage):
        message = "❌ Cette commande doit être utilisée dans un serveur."
    else:
        log.exception("Erreur de commande", exc_info=error)
        message = "❌ Une erreur est survenue pendant l'exécution de la commande."
    try:
        await ctx.send(message)
    except discord.DiscordException:
        log.exception("Impossible d'envoyer le message d'erreur")


if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "La variable DISCORD_TOKEN est absente. Ajoute-la dans les variables d'environnement Render."
        )
    bot.run(TOKEN, log_handler=None)
