import os
import logging
import sqlite3
from datetime import timedelta

import discord
from discord.ext import commands

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("mk-arena")

TOKEN = os.getenv("DISCORD_TOKEN")
DB_PATH = os.getenv("SQLITE_PATH", "mk_arena.db")

intents = discord.Intents.default()
# À activer aussi dans Discord Developer Portal > Bot > Privileged Gateway Intents.
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
database_ready = False


def init_database():
    """Crée la table des avertissements si elle n'existe pas."""
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                max_players INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                creator_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tournament_registrations (
                tournament_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (tournament_id, user_id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id) ON DELETE CASCADE
            )"""
        )
        connection.execute(
            """CREATE TABLE IF NOT EXISTS tournament_config (
                guild_id INTEGER NOT NULL,
                format_key TEXT NOT NULL,
                format_label TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                rules TEXT NOT NULL DEFAULT '',
                updated_by INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, format_key)
            )"""
        )



@bot.event
async def on_ready():
    global database_ready
    if not database_ready:
        init_database()
        database_ready = True
        log.info("Base SQLite initialisée : %s", DB_PATH)
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
@commands.cooldown(1, 5, commands.BucketType.user)
async def aide(ctx: commands.Context):
    """Commande préfixe !aide, limitée à une utilisation toutes les 5 secondes."""
    embed = discord.Embed(
        title="🤖 MK Arena | Aide",
        description="Commandes MK Arena utilisant le préfixe !.",
        color=discord.Color.blurple(),
    )
    embed.add_field(
        name="Général",
        value="`!ping`\n`!aide`\n`!serveur`\n`!userinfo [membre]`\n`!avatar [membre]`",
        inline=False,
    )
    embed.add_field(
        name="Modération",
        value="`!clear 10`\n`!kick @membre raison`\n`!ban @membre raison`\n`!timeout @membre minutes raison`\n`!slowmode secondes`\n`!lock`\n`!unlock`\n`!warn @membre raison`\n`!warnings @membre`\n`!unwarn @membre ID`",
        inline=False,
    )
    embed.add_field(
        name="Configuration • Tournois CODM",
        value="`!config tournoi creer 10 Nom du tournoi`\n`!config tournoi liste`\n`!config tournoi info ID`\n`!config tournoi fermer ID`\n`!config tournoi ouvrir ID`\n`!config tournoi lancer ID`\n`!config tournoi inscrire ID`\n`!config tournoi desinscrire ID`",
        inline=False,
    )
    embed.set_footer(text="MK Arena • Commandes préfixe !")
    await ctx.send(embed=embed)


@bot.command(name="warn", description="Avertit un membre")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warn(ctx: commands.Context, membre: discord.Member, *, raison: str = None):
    if not raison or not raison.strip():
        await ctx.send("❌ Indique la raison. Exemple : `!warn @membre spam`")
        return
    if membre.bot:
        await ctx.send("❌ Les bots ne peuvent pas recevoir d'avertissement.")
        return
    if membre.id == ctx.author.id:
        await ctx.send("❌ Tu ne peux pas t'avertir toi-même.")
        return
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO warnings (guild_id, user_id, moderator_id, reason) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, membre.id, ctx.author.id, raison.strip()),
        )
        warning_id = cursor.lastrowid
    await ctx.send(f"⚠️ {membre.mention} a reçu un avertissement. ID : `{warning_id}`. Raison : {raison}")


@bot.command(name="warnings", description="Affiche les avertissements d'un membre")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warnings(ctx: commands.Context, membre: discord.Member):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT id, moderator_id, reason, created_at FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY id DESC LIMIT 10",
            (ctx.guild.id, membre.id),
        ).fetchall()
    if not rows:
        await ctx.send(f"✅ Aucun avertissement enregistré pour {membre.mention}.")
        return
    embed = discord.Embed(
        title=f"⚠️ Avertissements de {membre}",
        description=f"10 avertissements maximum affichés. Total affiché : {len(rows)}",
        color=discord.Color.orange(),
    )
    for warning_id, moderator_id, reason, created_at in rows:
        embed.add_field(
            name=f"ID {warning_id} • {created_at}",
            value=f"Raison : {reason}\nModérateur : <@{moderator_id}>",
            inline=False,
        )
    await ctx.send(embed=embed)


@bot.command(name="unwarn", description="Retire un avertissement par son ID")
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def unwarn(ctx: commands.Context, membre: discord.Member, warning_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "DELETE FROM warnings WHERE id = ? AND guild_id = ? AND user_id = ?",
            (warning_id, ctx.guild.id, membre.id),
        )
    if cursor.rowcount == 0:
        await ctx.send("❌ Aucun avertissement correspondant à cet ID pour ce membre.")
        return
    await ctx.send(f"✅ Avertissement `{warning_id}` retiré pour {membre.mention}.")


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


@bot.group(name="config", invoke_without_command=True, description="Configuration de MK Arena")
async def config(ctx: commands.Context):
    await ctx.send(
        "⚙️ Configuration MK Arena : `!config tournoi`. "
        "Utilise `!aide` pour afficher les commandes disponibles."
    )


@config.group(name="tournoi", invoke_without_command=True, description="Gestion des tournois CODM")
async def tournoi(ctx: commands.Context):
    await ctx.send(
        "🏆 Commandes tournoi : `!config tournoi creer <places> <nom>`, "
        "`!config tournoi liste`, `!config tournoi info <ID>`, "
        "`!config tournoi fermer <ID>`, `!config tournoi ouvrir <ID>`, "
        "`!config tournoi lancer <ID>`, `!config tournoi inscrire <ID>`, "
        "`!config tournoi desinscrire <ID>`."
    )

TOURNAMENT_FORMATS = {
    "bo3_5v5": "CODM BO3 • 5v5",
    "battle_royale": "Battle Royale",
    "3v3": "CODM • 3v3",
    "1v1": "CODM • 1v1",
    "2v2": "CODM • 2v2",
    "full_sniper": "Full Sniper",
    "full_smg": "Full SMG",
}


@tournoi.command(name="panel", description="Affiche le panel des formats et règles")
@commands.guild_only()
async def tournoi_panel(ctx: commands.Context):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT format_key, details, rules FROM tournament_config WHERE guild_id = ?",
            (ctx.guild.id,),
        ).fetchall()
    saved = {key: (details, rules) for key, details, rules in rows}
    embed = discord.Embed(
        title="🏆 MK Arena • Panel des tournois CODM",
        description=(
            "Formats disponibles et informations configurées par les administrateurs.\n"
            "Utilise les commandes indiquées ci-dessous pour modifier le panel."
        ),
        color=discord.Color.blurple(),
    )
    for key, label in TOURNAMENT_FORMATS.items():
        details, rules = saved.get(key, ("", ""))
        value = f"**Infos :** {details or 'À configurer par un administrateur.'}\n"
        value += f"**Règles :** {rules or 'À configurer par un administrateur.'}"
        embed.add_field(name=label, value=value[:1024], inline=False)
    embed.add_field(
        name="🛠️ Commandes administrateur",
        value=(
            "`!config tournoi format bo3_5v5 Infos du match...`\n"
            "`!config tournoi regles bo3_5v5 Règles du match...`\n"
            "Remplace `bo3_5v5` par : `battle_royale`, `3v3`, `1v1`, "
            "`2v2`, `full_sniper` ou `full_smg`.\n"
            "Permissions requises : Gérer le serveur."
        ),
        inline=False,
    )
    embed.set_footer(text="Les paramètres sont séparés par serveur Discord.")
    await ctx.send(embed=embed)


@tournoi.command(name="format", description="Configure les informations d'un format")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_format(ctx: commands.Context, format_key: str, *, details: str):
    format_key = format_key.lower()
    if format_key not in TOURNAMENT_FORMATS:
        await ctx.send("❌ Format inconnu. Choisis : " + ", ".join(f"`{key}`" for key in TOURNAMENT_FORMATS))
        return
    details = details.strip()
    if not details:
        await ctx.send("❌ Ajoute les informations du format.")
        return
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """INSERT INTO tournament_config
               (guild_id, format_key, format_label, details, rules, updated_by)
               VALUES (?, ?, ?, ?, '', ?)
               ON CONFLICT(guild_id, format_key) DO UPDATE SET
               format_label = excluded.format_label,
               details = excluded.details,
               updated_by = excluded.updated_by,
               updated_at = CURRENT_TIMESTAMP""",
            (ctx.guild.id, format_key, TOURNAMENT_FORMATS[format_key], details[:1800], ctx.author.id),
        )
    await ctx.send(f"✅ Informations enregistrées pour **{TOURNAMENT_FORMATS[format_key]}**. Utilise `!config tournoi panel` pour voir le résultat.")


@tournoi.command(name="regles", description="Configure les règles d'un format")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_regles(ctx: commands.Context, format_key: str, *, rules: str):
    format_key = format_key.lower()
    if format_key not in TOURNAMENT_FORMATS:
        await ctx.send("❌ Format inconnu. Choisis : " + ", ".join(f"`{key}`" for key in TOURNAMENT_FORMATS))
        return
    rules = rules.strip()
    if not rules:
        await ctx.send("❌ Ajoute les règles à enregistrer.")
        return
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """INSERT INTO tournament_config
               (guild_id, format_key, format_label, details, rules, updated_by)
               VALUES (?, ?, ?, '', ?, ?)
               ON CONFLICT(guild_id, format_key) DO UPDATE SET
               format_label = excluded.format_label,
               rules = excluded.rules,
               updated_by = excluded.updated_by,
               updated_at = CURRENT_TIMESTAMP""",
            (ctx.guild.id, format_key, TOURNAMENT_FORMATS[format_key], rules[:1800], ctx.author.id),
        )
    await ctx.send(f"✅ Règles enregistrées pour **{TOURNAMENT_FORMATS[format_key]}**. Utilise `!config tournoi panel` pour voir le résultat.")


@tournoi.command(name="creer", description="Crée un tournoi CODM")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_creer(ctx: commands.Context, places: int, *, nom: str):
    nom = nom.strip()
    if not nom:
        await ctx.send("❌ Donne un nom au tournoi.")
        return
    if places < 2 or places > 256:
        await ctx.send("❌ Le nombre de places doit être compris entre 2 et 256.")
        return
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "INSERT INTO tournaments (guild_id, name, max_players, creator_id) VALUES (?, ?, ?, ?)",
            (ctx.guild.id, nom[:100], places, ctx.author.id),
        )
        tournament_id = cursor.lastrowid
    embed = discord.Embed(
        title=f"🏆 Tournoi CODM créé : {nom[:100]}",
        description=f"ID : `{tournament_id}`\nPlaces : **{places}**\nStatut : 🟢 Inscriptions ouvertes",
        color=discord.Color.green(),
    )
    embed.set_footer(text=f"Créé par {ctx.author}")
    await ctx.send(embed=embed)


@tournoi.command(name="liste", description="Liste les tournois CODM du serveur")
@commands.guild_only()
async def tournoi_liste(ctx: commands.Context):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """SELECT t.id, t.name, t.max_players, t.status, COUNT(r.user_id)
               FROM tournaments t LEFT JOIN tournament_registrations r ON r.tournament_id = t.id
               WHERE t.guild_id = ? GROUP BY t.id ORDER BY t.id DESC LIMIT 15""",
            (ctx.guild.id,),
        ).fetchall()
    if not rows:
        await ctx.send("🏆 Aucun tournoi enregistré sur ce serveur. Un administrateur peut en créer avec `!tournoi creer 10 Nom`.")
        return
    embed = discord.Embed(title="🏆 Tournois CODM", color=discord.Color.blurple())
    status_names = {"open": "🟢 Inscriptions ouvertes", "closed": "🟠 Inscriptions fermées", "running": "🔴 En cours", "finished": "🏁 Terminé"}
    for tid, name, maximum, status, count in rows:
        embed.add_field(
            name=f"#{tid} • {name}",
            value=f"{status_names.get(status, status)}\n👥 {count}/{maximum} participants",
            inline=False,
        )
    await ctx.send(embed=embed)


@tournoi.command(name="info", description="Affiche les détails d'un tournoi")
@commands.guild_only()
async def tournoi_info(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """SELECT t.name, t.max_players, t.status, t.creator_id, t.created_at, COUNT(r.user_id)
               FROM tournaments t LEFT JOIN tournament_registrations r ON r.tournament_id = t.id
               WHERE t.guild_id = ? AND t.id = ? GROUP BY t.id""",
            (ctx.guild.id, tournament_id),
        ).fetchone()
        players = connection.execute(
            """SELECT user_id FROM tournament_registrations WHERE tournament_id = ?
               ORDER BY registered_at LIMIT 30""",
            (tournament_id,),
        ).fetchall() if row else []
    if not row:
        await ctx.send("❌ Tournoi introuvable sur ce serveur.")
        return
    name, maximum, status, creator_id, created_at, count = row
    status_names = {"open": "🟢 Inscriptions ouvertes", "closed": "🟠 Inscriptions fermées", "running": "🔴 En cours", "finished": "🏁 Terminé"}
    mentions = "\n".join(f"• <@{player_id}>" for (player_id,) in players) or "Aucun participant pour le moment."
    embed = discord.Embed(title=f"🏆 {name}", color=discord.Color.blurple())
    embed.add_field(name="ID", value=str(tournament_id), inline=True)
    embed.add_field(name="Participants", value=f"{count}/{maximum}", inline=True)
    embed.add_field(name="Statut", value=status_names.get(status, status), inline=True)
    embed.add_field(name="Organisateur", value=f"<@{creator_id}>", inline=True)
    embed.add_field(name="Créé le", value=created_at, inline=True)
    embed.add_field(name="Inscrits", value=mentions[:1024], inline=False)
    await ctx.send(embed=embed)


@tournoi.command(name="fermer", description="Ferme les inscriptions d'un tournoi")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_fermer(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE tournaments SET status = 'closed' WHERE id = ? AND guild_id = ? AND status = 'open'",
            (tournament_id, ctx.guild.id),
        )
    await ctx.send("🔒 Inscriptions fermées." if cursor.rowcount else "❌ Tournoi introuvable ou inscriptions déjà fermées.")


@tournoi.command(name="ouvrir", description="Ouvre les inscriptions d'un tournoi")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_ouvrir(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.execute(
            "UPDATE tournaments SET status = 'open' WHERE id = ? AND guild_id = ? AND status = 'closed'",
            (tournament_id, ctx.guild.id),
        )
    await ctx.send("🔓 Inscriptions ouvertes." if cursor.rowcount else "❌ Tournoi introuvable ou impossible à rouvrir (il doit être fermé).")


@tournoi.command(name="lancer", description="Lance un tournoi et ferme les inscriptions")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def tournoi_lancer(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            """SELECT t.name, t.max_players, COUNT(r.user_id)
               FROM tournaments t LEFT JOIN tournament_registrations r ON r.tournament_id = t.id
               WHERE t.guild_id = ? AND t.id = ? AND t.status IN ('open', 'closed')
               GROUP BY t.id""",
            (ctx.guild.id, tournament_id),
        ).fetchone()
        if not row:
            await ctx.send("❌ Tournoi introuvable ou déjà lancé.")
            return
        name, maximum, count = row
        if count < 2:
            await ctx.send("❌ Il faut au moins 2 participants inscrits pour lancer le tournoi.")
            return
        connection.execute(
            "UPDATE tournaments SET status = 'running' WHERE id = ? AND guild_id = ?",
            (tournament_id, ctx.guild.id),
        )
    await ctx.send(f"🚨 **{name}** démarre ! {count}/{maximum} participants inscrits. Les inscriptions sont maintenant fermées.")


@tournoi.command(name="inscrire", description="S'inscrit à un tournoi CODM")
@commands.guild_only()
async def tournoi_inscrire(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT name, max_players, status FROM tournaments WHERE id = ? AND guild_id = ?",
            (tournament_id, ctx.guild.id),
        ).fetchone()
        if not row:
            await ctx.send("❌ Tournoi introuvable sur ce serveur.")
            return
        name, maximum, status = row
        if status != "open":
            await ctx.send("❌ Les inscriptions à ce tournoi ne sont pas ouvertes.")
            return
        count = connection.execute(
            "SELECT COUNT(*) FROM tournament_registrations WHERE tournament_id = ?",
            (tournament_id,),
        ).fetchone()[0]
        if count >= maximum:
            await ctx.send("❌ Ce tournoi affiche complet.")
            return
        try:
            connection.execute(
                "INSERT INTO tournament_registrations (tournament_id, user_id) VALUES (?, ?)",
                (tournament_id, ctx.author.id),
            )
        except sqlite3.IntegrityError:
            await ctx.send("ℹ️ Tu es déjà inscrit à ce tournoi.")
            return
    await ctx.send(f"✅ {ctx.author.mention}, ton inscription à **{name}** est confirmée ! ({count + 1}/{maximum})")


@tournoi.command(name="desinscrire", description="Se désinscrit d'un tournoi CODM")
@commands.guild_only()
async def tournoi_desinscrire(ctx: commands.Context, tournament_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT name, status FROM tournaments WHERE id = ? AND guild_id = ?",
            (tournament_id, ctx.guild.id),
        ).fetchone()
        if not row:
            await ctx.send("❌ Tournoi introuvable sur ce serveur.")
            return
        name, status = row
        if status != "open":
            await ctx.send("❌ Tu peux te désinscrire uniquement tant que les inscriptions sont ouvertes.")
            return
        cursor = connection.execute(
            "DELETE FROM tournament_registrations WHERE tournament_id = ? AND user_id = ?",
            (tournament_id, ctx.author.id),
        )
    if cursor.rowcount:
        await ctx.send(f"✅ Tu es désinscrit de **{name}**.")
    else:
        await ctx.send("ℹ️ Tu n'étais pas inscrit à ce tournoi.")


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Réessaie dans {error.retry_after:.1f} seconde(s).", delete_after=5)
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
