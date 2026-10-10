import os
import logging
import sqlite3
import time
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
intents.members = True  # Active aussi Server Members Intent dans le portail Discord.

bot = commands.Bot(command_prefix="!", intents=intents)
database_ready = False
slash_commands_synced = False
persistent_views_registered = False


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
        connection.execute("""CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY, welcome_channel_id INTEGER, log_channel_id INTEGER,
            welcome_enabled INTEGER NOT NULL DEFAULT 1, xp_enabled INTEGER NOT NULL DEFAULT 1,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
        connection.execute("""CREATE TABLE IF NOT EXISTS user_xp (
            guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL, xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0, last_message_at REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (guild_id, user_id))""")
        connection.execute("""CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
            channel_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")



@bot.event
async def on_ready():
    global database_ready, slash_commands_synced
    if not database_ready:
        init_database()
        database_ready = True
        log.info("Base SQLite initialisée : %s", DB_PATH)
    if not slash_commands_synced:
        try:
            synced = await bot.tree.sync()
            slash_commands_synced = True
            log.info("%s commande(s) slash synchronisée(s).", len(synced))
        except discord.HTTPException:
            log.exception("Impossible de synchroniser les commandes slash.")
    global persistent_views_registered
    if not persistent_views_registered:
        bot.add_view(TicketPanelView())
        bot.add_view(TicketCloseView())
        persistent_views_registered = True
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
        value="`!ping`\n`!aide`\n`!panel`\n`!serveur`\n`!userinfo [membre]`\n`!avatar [membre]`\n`!profil [membre]`\n`!classement`\n`!ticketpanel`",
        inline=False,
    )
    embed.add_field(
        name="Modération",
        value="`!clear 10`\n`!kick @membre raison`\n`!ban @membre raison`\n`!timeout @membre minutes raison`\n`!slowmode secondes`\n`!lock`\n`!unlock`\n`!warn @membre raison`\n`!warnings @membre`\n`!unwarn @membre ID`",
        inline=False,
    )
    embed.add_field(
        name="Configuration • Tournois CODM",
        value="`!panel`\n`!config panel`\n`!config tournoi panel`\n`!config tournoi format bo3_5v5 Infos...`\n`!config tournoi regles bo3_5v5 Regles...`\n`!config tournoi creer 10 Nom du tournoi`\n`!config tournoi liste`\n`!config tournoi info ID`\n`!config tournoi fermer ID`\n`!config tournoi ouvrir ID`\n`!config tournoi lancer ID`\n`!config tournoi inscrire ID`\n`!config tournoi desinscrire ID`",
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
        "🏆 Panel tournoi : `!config tournoi panel`. "
        "Admins : `!config tournoi format <mode> <infos>` et "
        "`!config tournoi regles <mode> <règles>`. "
        "Gestion : `!config tournoi creer <places> <nom>`, `liste`, `info <ID>`, "
        "`fermer <ID>`, `ouvrir <ID>`, `lancer <ID>`, `inscrire <ID>`, `desinscrire <ID>`."
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


async def get_tournament_config(guild_id: int, format_key: str):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT details, rules FROM tournament_config WHERE guild_id = ? AND format_key = ?",
            (guild_id, format_key),
        ).fetchone()
    return row or ("", "")


async def build_tournament_panel_embed(guild_id: int, format_key: str):
    label = TOURNAMENT_FORMATS[format_key]
    details, rules = await get_tournament_config(guild_id, format_key)
    embed = discord.Embed(
        title="🏆 MK Arena • Configuration des tournois",
        description=(
            f"**Mode sélectionné : {label}**\n\n"
            "Choisis un mode dans le menu, puis utilise les boutons pour modifier ses informations ou ses règles."
        ),
        color=discord.Color.blurple(),
    )
    embed.add_field(name="📋 Informations du format", value=(details or "Pas encore configurées.")[:1024], inline=False)
    embed.add_field(name="📜 Règles du format", value=(rules or "Pas encore configurées.")[:1024], inline=False)
    embed.set_footer(text="Modification réservée aux membres ayant la permission Gérer le serveur.")
    return embed


class TournamentFormatSelect(discord.ui.Select):
    def __init__(self, panel_view):
        self.panel_view = panel_view
        options = [
            discord.SelectOption(label=label, value=key, default=(key == panel_view.selected_key))
            for key, label in TOURNAMENT_FORMATS.items()
        ]
        super().__init__(
            placeholder="Choisir un mode de tournoi...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="mk_arena_tournament_format_select",
        )

    async def callback(self, interaction: discord.Interaction):
        self.panel_view.selected_key = self.values[0]
        for option in self.options:
            option.default = option.value == self.panel_view.selected_key
        embed = await build_tournament_panel_embed(interaction.guild_id, self.panel_view.selected_key)
        await interaction.response.edit_message(embed=embed, view=self.panel_view)


class TournamentInfoModal(discord.ui.Modal):
    def __init__(self, guild_id: int, format_key: str, initial: str = ""):
        self.guild_id = guild_id
        self.format_key = format_key
        super().__init__(title=f"Modifier : {TOURNAMENT_FORMATS[format_key]}", timeout=300)
        self.details_input = discord.ui.TextInput(
            label="Informations du mode",
            placeholder="Ex. BO3, 5 joueurs par équipe, conditions de victoire...",
            default=initial[:1800] if initial else None,
            style=discord.TextStyle.paragraph,
            max_length=1800,
            required=True,
        )
        self.add_item(self.details_input)

    async def on_submit(self, interaction: discord.Interaction):
        details = str(self.details_input.value).strip()
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
                (self.guild_id, self.format_key, TOURNAMENT_FORMATS[self.format_key], details, interaction.user.id),
            )
        await interaction.response.send_message(
            f"✅ Informations enregistrées pour **{TOURNAMENT_FORMATS[self.format_key]}**. Clique sur **Actualiser** dans le panel.",
            ephemeral=True,
        )


class TournamentRulesModal(discord.ui.Modal):
    def __init__(self, guild_id: int, format_key: str, initial: str = ""):
        self.guild_id = guild_id
        self.format_key = format_key
        super().__init__(title=f"Règles : {TOURNAMENT_FORMATS[format_key]}", timeout=300)
        self.rules_input = discord.ui.TextInput(
            label="Règles du tournoi",
            placeholder="Ex. interdiction de tricher, retard, forfait, preuves...",
            default=initial[:1800] if initial else None,
            style=discord.TextStyle.paragraph,
            max_length=1800,
            required=True,
        )
        self.add_item(self.rules_input)

    async def on_submit(self, interaction: discord.Interaction):
        rules = str(self.rules_input.value).strip()
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
                (self.guild_id, self.format_key, TOURNAMENT_FORMATS[self.format_key], rules, interaction.user.id),
            )
        await interaction.response.send_message(
            f"✅ Règles enregistrées pour **{TOURNAMENT_FORMATS[self.format_key]}**. Clique sur **Actualiser** dans le panel.",
            ephemeral=True,
        )


class TournamentConfigPanel(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=600)
        self.guild_id = guild_id
        self.selected_key = "bo3_5v5"
        self.add_item(TournamentFormatSelect(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message("❌ Ce panel appartient à un autre serveur.", ephemeral=True)
            return False
        return True

    async def require_admin(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "❌ Il faut la permission **Gérer le serveur** pour modifier ce panel.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="Modifier les infos", style=discord.ButtonStyle.primary, emoji="📝", row=1)
    async def edit_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.require_admin(interaction):
            return
        details, _ = await get_tournament_config(self.guild_id, self.selected_key)
        await interaction.response.send_modal(TournamentInfoModal(self.guild_id, self.selected_key, details))

    @discord.ui.button(label="Modifier les règles", style=discord.ButtonStyle.primary, emoji="📜", row=1)
    async def edit_rules(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.require_admin(interaction):
            return
        _, rules = await get_tournament_config(self.guild_id, self.selected_key)
        await interaction.response.send_modal(TournamentRulesModal(self.guild_id, self.selected_key, rules))

    @discord.ui.button(label="Actualiser", style=discord.ButtonStyle.secondary, emoji="🔄", row=2)
    async def refresh_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await build_tournament_panel_embed(self.guild_id, self.selected_key)
        await interaction.response.edit_message(embed=embed, view=self)



def build_main_panel_embed(guild: discord.Guild):
    embed = discord.Embed(
        title="⚔️ MK ARENA • Centre de contrôle",
        description=(
            f"Bienvenue dans le panneau d'administration de **{guild.name}**.\n"
            "Choisis une catégorie avec les boutons ci-dessous. Les réglages sensibles restent réservés aux administrateurs."
        ),
        color=discord.Color.from_rgb(111, 66, 193),
    )
    embed.add_field(name="⚙️ Configuration", value="Réglages disponibles et commandes du serveur", inline=True)
    embed.add_field(name="🏆 Tournois CODM", value="Formats, règles et inscriptions", inline=True)
    embed.add_field(name="🛡️ Modération", value="Outils de sécurité et sanctions", inline=True)
    embed.add_field(name="👥 Communauté", value="Fonctions communautaires à développer", inline=True)
    embed.add_field(name="📊 Statistiques", value="Vue d'ensemble du serveur", inline=True)
    embed.add_field(name="🎫 Support", value="Tickets privés pour les membres", inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    embed.set_footer(text="MK Arena • V1 • Utilise les boutons pour naviguer")
    return embed


async def build_main_section_embed(guild: discord.Guild, section: str):
    titles = {
        "config": "⚙️ Configuration du serveur",
        "tournaments": "🏆 Centre des tournois CODM",
        "moderation": "🛡️ Centre de modération",
        "community": "👥 Communauté",
        "stats": "📊 Statistiques du serveur",
        "support": "🎫 Support et tickets",
    }
    embed = discord.Embed(title=titles[section], color=discord.Color.from_rgb(111, 66, 193))
    if section == "config":
        welcome_id, log_id, welcome_enabled, xp_enabled = get_guild_settings(guild.id)
        embed.description = (
            "Salon accueil : " + (f"<#{welcome_id}>" if welcome_id else "Non configuré") + "\n"
            "Salon logs : " + (f"<#{log_id}>" if log_id else "Non configuré") + "\n"
            "Bienvenue : " + ("Activé" if welcome_enabled else "Désactivé") + "\n"
            "XP : " + ("Activé" if xp_enabled else "Désactivé") + "\n\n"
            "Les boutons de cette page définissent le salon actuel et activent ou désactivent les fonctions."
        )
        embed.add_field(name="Commandes utiles", value="!ticketpanel : publier le panneau de tickets\n!config tournoi panel : configurer les tournois", inline=False)
    elif section == "moderation":
        embed.description = (
            "Les commandes de modération déjà disponibles :\n"
            "!clear 10 • supprimer des messages\n"
            "!warn @membre raison • avertir\n"
            "!warnings @membre • consulter les avertissements\n"
            "!unwarn @membre ID • retirer un avertissement\n"
            "!kick @membre raison • expulser\n"
            "!ban @membre raison • bannir\n"
            "!timeout @membre minutes raison • timeout\n"
            "!slowmode secondes, !lock, !unlock"
        )
        embed.set_footer(text="Les permissions Discord requises sont vérifiées par le bot.")
    elif section == "community":
        with sqlite3.connect(DB_PATH) as connection:
            total_xp = connection.execute("SELECT COALESCE(SUM(xp), 0) FROM user_xp WHERE guild_id = ?", (guild.id,)).fetchone()[0]
            tracked_users = connection.execute("SELECT COUNT(*) FROM user_xp WHERE guild_id = ?", (guild.id,)).fetchone()[0]
        embed.description = "XP communautaire actif : les membres gagnent 5 XP par minute d'activité éligible."
        embed.add_field(name="Membres suivis", value=str(tracked_users), inline=True)
        embed.add_field(name="XP distribuée", value=str(total_xp), inline=True)
        embed.add_field(name="Commandes", value="!profil [membre]\n!classement", inline=False)
    elif section == "support":
        embed.description = "Ouvre un ticket privé avec le bouton ci-dessous. Un seul ticket ouvert par membre est autorisé."
    elif section == "stats":
        with sqlite3.connect(DB_PATH) as connection:
            tournament_count = connection.execute(
                "SELECT COUNT(*) FROM tournaments WHERE guild_id = ?", (guild.id,)
            ).fetchone()[0]
            warning_count = connection.execute(
                "SELECT COUNT(*) FROM warnings WHERE guild_id = ?", (guild.id,)
            ).fetchone()[0]
        embed.description = "Aperçu calculé à partir des données locales de MK Arena."
        embed.add_field(name="👥 Membres", value=str(guild.member_count or "Inconnu"), inline=True)
        embed.add_field(name="💬 Salons", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="🏆 Tournois enregistrés", value=str(tournament_count), inline=True)
        embed.add_field(name="⚠️ Avertissements enregistrés", value=str(warning_count), inline=True)
    else:
        embed.description = "Choisis une section du panel principal."
    embed.set_footer(text="MK Arena • V1")
    return embed


class MKArenaSectionPanel(discord.ui.View):
    def __init__(self, guild_id: int, section: str):
        super().__init__(timeout=900)
        self.guild_id = guild_id
        self.section = section

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message("❌ Ce panel appartient à un autre serveur.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Retour à l'accueil", style=discord.ButtonStyle.secondary, emoji="🏠", row=0)
    async def back_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Utilise ce panel dans un serveur.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content="⚔️ **MK Arena • Centre de contrôle**",
            embed=build_main_panel_embed(interaction.guild),
            view=MKArenaHomePanel(self.guild_id),
        )

    @discord.ui.button(label="Créer un ticket", style=discord.ButtonStyle.success, emoji="🎫", row=1)
    async def create_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Pour publier le panneau de tickets dans un salon, un administrateur peut utiliser !ticketpanel.", ephemeral=True)

    @discord.ui.button(label="Actualiser", style=discord.ButtonStyle.primary, emoji="🔄", row=0)
    async def refresh_section(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Utilise ce panel dans un serveur.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=await build_main_section_embed(interaction.guild, self.section),
            view=self,
        )


class MKArenaHomePanel(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=900)
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message("❌ Ce panel appartient à un autre serveur.", ephemeral=True)
            return False
        return True

    async def open_section(self, interaction: discord.Interaction, section: str):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Utilise ce panel dans un serveur.", ephemeral=True)
            return
        if section == "tournaments":
            view = TournamentConfigPanel(self.guild_id)
            embed = await build_tournament_panel_embed(self.guild_id, view.selected_key)
            await interaction.response.edit_message(
                content="🏆 **MK Arena • Centre des tournois**",
                embed=embed,
                view=view,
            )
            return
        await interaction.response.edit_message(
            content=None,
            embed=await build_main_section_embed(interaction.guild, section),
            view=ServerSettingsPanel(self.guild_id) if section == "config" else (SupportPanelView(self.guild_id) if section == "support" else MKArenaSectionPanel(self.guild_id, section)),
        )

    @discord.ui.button(label="Configuration", style=discord.ButtonStyle.secondary, emoji="⚙️", row=0)
    async def open_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "config")

    @discord.ui.button(label="Tournois CODM", style=discord.ButtonStyle.primary, emoji="🏆", row=0)
    async def open_tournaments(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "tournaments")

    @discord.ui.button(label="Modération", style=discord.ButtonStyle.secondary, emoji="🛡️", row=1)
    async def open_moderation(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "moderation")

    @discord.ui.button(label="Communauté", style=discord.ButtonStyle.secondary, emoji="👥", row=1)
    async def open_community(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "community")

    @discord.ui.button(label="Statistiques", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def open_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "stats")

    @discord.ui.button(label="Support / Tickets", style=discord.ButtonStyle.primary, emoji="🎫", row=2)
    async def open_support(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.open_section(interaction, "support")

    @discord.ui.button(label="Actualiser", style=discord.ButtonStyle.success, emoji="🔄", row=2)
    async def refresh_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("❌ Utilise ce panel dans un serveur.", ephemeral=True)
            return
        await interaction.response.edit_message(
            content="⚔️ **MK Arena • Centre de contrôle**",
            embed=build_main_panel_embed(interaction.guild),
            view=self,
        )



def get_guild_settings(guild_id: int):
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT welcome_channel_id, log_channel_id, welcome_enabled, xp_enabled FROM guild_settings WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
    return row or (None, None, 1, 1)


def update_guild_setting(guild_id: int, key: str, value):
    allowed = {"welcome_channel_id", "log_channel_id", "welcome_enabled", "xp_enabled"}
    if key not in allowed:
        raise ValueError("Réglage non autorisé")
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        connection.execute(
            "UPDATE guild_settings SET " + key + " = ?, updated_at = CURRENT_TIMESTAMP WHERE guild_id = ?",
            (value, guild_id),
        )


async def send_configured_log(guild: discord.Guild, message: str):
    _, log_channel_id, _, _ = get_guild_settings(guild.id)
    channel = guild.get_channel(log_channel_id) if log_channel_id else None
    if isinstance(channel, discord.TextChannel):
        try:
            await channel.send(message[:1900])
        except discord.DiscordException:
            log.exception("Impossible d'envoyer un log dans le serveur %s", guild.id)


class ServerSettingsPanel(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=900)
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message("Ce panel appartient à un autre serveur.", ephemeral=True)
            return False
        if not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("La permission Gérer le serveur est nécessaire.", ephemeral=True)
            return False
        return True

    async def refresh_panel(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("Utilise ce panel dans un serveur.", ephemeral=True)
            return
        welcome_id, log_id, welcome_enabled, xp_enabled = get_guild_settings(self.guild_id)
        embed = discord.Embed(title="Configuration MK Arena", color=discord.Color.blurple())
        embed.description = (
            "Salon accueil : " + (f"<#{welcome_id}>" if welcome_id else "Non configuré") + "\n"
            "Salon logs : " + (f"<#{log_id}>" if log_id else "Non configuré") + "\n"
            "Bienvenue automatique : " + ("Activé" if welcome_enabled else "Désactivé") + "\n"
            "XP communautaire : " + ("Activé" if xp_enabled else "Désactivé") + "\n\n"
            "Les boutons Accueil et Logs utilisent le salon dans lequel ce panel a été envoyé."
        )
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Accueil ici", style=discord.ButtonStyle.primary, emoji="👋", row=0)
    async def set_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Choisis un salon textuel.", ephemeral=True)
            return
        update_guild_setting(self.guild_id, "welcome_channel_id", interaction.channel.id)
        await self.refresh_panel(interaction)

    @discord.ui.button(label="Logs ici", style=discord.ButtonStyle.primary, emoji="📋", row=0)
    async def set_logs(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message("Choisis un salon textuel.", ephemeral=True)
            return
        update_guild_setting(self.guild_id, "log_channel_id", interaction.channel.id)
        await self.refresh_panel(interaction)

    @discord.ui.button(label="Accueil ON/OFF", style=discord.ButtonStyle.secondary, emoji="🔔", row=1)
    async def toggle_welcome(self, interaction: discord.Interaction, button: discord.ui.Button):
        _, _, enabled, _ = get_guild_settings(self.guild_id)
        update_guild_setting(self.guild_id, "welcome_enabled", 0 if enabled else 1)
        await self.refresh_panel(interaction)

    @discord.ui.button(label="XP ON/OFF", style=discord.ButtonStyle.secondary, emoji="⭐", row=1)
    async def toggle_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        _, _, _, enabled = get_guild_settings(self.guild_id)
        update_guild_setting(self.guild_id, "xp_enabled", 0 if enabled else 1)
        await self.refresh_panel(interaction)

    @discord.ui.button(label="Retour", style=discord.ButtonStyle.success, emoji="🏠", row=2)
    async def go_back(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Utilise ce panel dans un serveur.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_main_panel_embed(interaction.guild), view=MKArenaHomePanel(self.guild_id))


class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Créer un ticket privé", style=discord.ButtonStyle.success, emoji="🎫", custom_id="mk_arena_ticket_create")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message("Utilise ce bouton dans un serveur.", ephemeral=True)
            return
        with sqlite3.connect(DB_PATH) as connection:
            row = connection.execute(
                "SELECT channel_id FROM tickets WHERE guild_id = ? AND user_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
                (guild.id, interaction.user.id),
            ).fetchone()
        if row:
            existing = guild.get_channel(row[0])
            if existing:
                await interaction.response.send_message(f"Tu as déjà un ticket ouvert : {existing.mention}", ephemeral=True)
                return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, attach_files=True, embed_links=True),
        }
        if guild.me:
            overwrites[guild.me] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True, manage_channels=True)
        try:
            channel = await guild.create_text_channel(
                name=("ticket-" + interaction.user.name).lower().replace(" ", "-")[:90],
                overwrites=overwrites,
                topic=f"MKARENA_TICKET_OWNER={interaction.user.id}",
                reason=f"Ticket MK Arena ouvert par {interaction.user}",
            )
            with sqlite3.connect(DB_PATH) as connection:
                connection.execute(
                    "INSERT INTO tickets (guild_id, user_id, channel_id, status) VALUES (?, ?, ?, 'open')",
                    (guild.id, interaction.user.id, channel.id),
                )
            await channel.send(
                f"🎫 Bonjour {interaction.user.mention}. Décris ton besoin ici. L'équipe autorisée pourra intervenir.",
                view=TicketCloseView(),
            )
            await interaction.response.send_message(f"Ticket créé : {channel.mention}", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Il me manque la permission Gérer les salons.", ephemeral=True)
        except discord.DiscordException:
            log.exception("Création de ticket impossible")
            await interaction.response.send_message("Impossible de créer le ticket pour le moment.", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="mk_arena_ticket_close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel) or not channel.topic or "MKARENA_TICKET_OWNER=" not in channel.topic:
            await interaction.response.send_message("Ce salon n'est pas un ticket MK Arena.", ephemeral=True)
            return
        owner_id = channel.topic.split("MKARENA_TICKET_OWNER=", 1)[1].split()[0]
        is_owner = str(interaction.user.id) == owner_id
        is_staff = isinstance(interaction.user, discord.Member) and (
            interaction.user.guild_permissions.manage_channels or interaction.user.guild_permissions.administrator
        )
        if not is_owner and not is_staff:
            await interaction.response.send_message("Seul l'auteur du ticket ou un membre du staff autorisé peut le fermer.", ephemeral=True)
            return
        with sqlite3.connect(DB_PATH) as connection:
            connection.execute(
                "UPDATE tickets SET status = 'closed' WHERE guild_id = ? AND channel_id = ? AND status = 'open'",
                (channel.guild.id, channel.id),
            )
        owner = channel.guild.get_member(int(owner_id))
        if owner:
            try:
                await channel.set_permissions(owner, send_messages=False)
            except discord.DiscordException:
                pass
        try:
            await channel.edit(name=("ferme-" + channel.name)[:100])
        except discord.DiscordException:
            pass
        await interaction.response.send_message(f"Ticket fermé par {interaction.user.mention}. Le salon est conservé pour l'équipe.")



class SupportPanelView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=900)
        self.guild_id = guild_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild_id != self.guild_id:
            await interaction.response.send_message("Ce panel appartient à un autre serveur.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Ouvrir le panneau de ticket", style=discord.ButtonStyle.success, emoji="🎫", row=0)
    async def open_ticket_panel(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="Support MK Arena",
            description="Clique sur le bouton ci-dessous pour créer ton salon privé. Un seul ticket ouvert par membre.",
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed, view=TicketPanelView(), ephemeral=True)

    @discord.ui.button(label="Retour à l'accueil", style=discord.ButtonStyle.secondary, emoji="🏠", row=0)
    async def back_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Utilise ce panel dans un serveur.", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_main_panel_embed(interaction.guild), view=MKArenaHomePanel(self.guild_id))


@bot.command(name="ticketpanel", description="Publie le panneau de création de tickets")
@commands.guild_only()
@commands.has_permissions(manage_guild=True)
async def ticketpanel(ctx: commands.Context):
    embed = discord.Embed(
        title="🎫 Support MK Arena",
        description="Besoin d'aide ? Clique ci-dessous pour créer un salon privé avec l'équipe. Un seul ticket ouvert par membre.",
        color=discord.Color.blurple(),
    )
    await ctx.send(embed=embed, view=TicketPanelView())


@bot.command(name="profil", description="Affiche le profil XP d'un membre")
@commands.guild_only()
async def profil(ctx: commands.Context, membre: discord.Member = None):
    membre = membre or ctx.author
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT xp, level FROM user_xp WHERE guild_id = ? AND user_id = ?",
            (ctx.guild.id, membre.id),
        ).fetchone()
    xp, level = row if row else (0, 0)
    embed = discord.Embed(title=f"Profil communautaire • {membre.display_name}", color=discord.Color.blurple())
    embed.set_thumbnail(url=membre.display_avatar.url)
    embed.add_field(name="Niveau", value=str(level), inline=True)
    embed.add_field(name="XP", value=str(xp), inline=True)
    embed.add_field(name="Prochain niveau", value=f"{max(0, (level + 1) * 100 - xp)} XP", inline=True)
    await ctx.send(embed=embed)


@bot.command(name="classement", description="Affiche le classement XP du serveur")
@commands.guild_only()
async def classement(ctx: commands.Context):
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT user_id, xp, level FROM user_xp WHERE guild_id = ? ORDER BY xp DESC LIMIT 10",
            (ctx.guild.id,),
        ).fetchall()
    embed = discord.Embed(title="Classement MK Arena", color=discord.Color.gold())
    embed.description = "\n".join(
        f"{index}. <@{user_id}> • Niveau {level} • {xp} XP"
        for index, (user_id, xp, level) in enumerate(rows, start=1)
    ) if rows else "Aucune XP enregistrée pour le moment."
    await ctx.send(embed=embed)


@bot.event
async def on_member_join(member: discord.Member):
    welcome_id, _, welcome_enabled, _ = get_guild_settings(member.guild.id)
    if welcome_enabled and welcome_id:
        channel = member.guild.get_channel(welcome_id)
        if isinstance(channel, discord.TextChannel):
            try:
                await channel.send(f"👋 Bienvenue {member.mention} sur **{member.guild.name}** ! Tu es le membre n°{member.guild.member_count or '?'} 🎮")
            except discord.DiscordException:
                log.exception("Message de bienvenue impossible")
    await send_configured_log(member.guild, f"📥 Arrivée : {member.mention} ({member.id})")


@bot.event
async def on_member_remove(member: discord.Member):
    await send_configured_log(member.guild, f"📤 Départ : {member} ({member.id})")


@bot.event
async def on_message_delete(message: discord.Message):
    if message.guild and not message.author.bot:
        content = (message.content or "[message sans texte]")[:700]
        await send_configured_log(message.guild, f"🗑️ Message supprimé dans {message.channel.mention} par {message.author.mention} : {content}")


@bot.event
async def on_message(message: discord.Message):
    if message.guild and not message.author.bot:
        _, _, _, xp_enabled = get_guild_settings(message.guild.id)
        if xp_enabled:
            now = time.time()
            with sqlite3.connect(DB_PATH) as connection:
                row = connection.execute(
                    "SELECT xp, level, last_message_at FROM user_xp WHERE guild_id = ? AND user_id = ?",
                    (message.guild.id, message.author.id),
                ).fetchone()
                if not row:
                    connection.execute(
                        "INSERT INTO user_xp (guild_id, user_id, xp, level, last_message_at) VALUES (?, ?, 5, 0, ?)",
                        (message.guild.id, message.author.id, now),
                    )
                elif now - row[2] >= 60:
                    xp = row[0] + 5
                    level = xp // 100
                    connection.execute(
                        "UPDATE user_xp SET xp = ?, level = ?, last_message_at = ? WHERE guild_id = ? AND user_id = ?",
                        (xp, level, now, message.guild.id, message.author.id),
                    )
    await bot.process_commands(message)


@bot.command(name="panel", description="Ouvre le centre de contrôle MK Arena")
@commands.guild_only()
async def panel(ctx: commands.Context):
    await ctx.send(
        content="⚔️ **MK Arena • Centre de contrôle**",
        embed=build_main_panel_embed(ctx.guild),
        view=MKArenaHomePanel(ctx.guild.id),
    )


@tournoi.command(name="panel", description="Ouvre le panel interactif des tournois CODM")
@commands.guild_only()
async def tournoi_panel(ctx: commands.Context):
    view = TournamentConfigPanel(ctx.guild.id)
    embed = await build_tournament_panel_embed(ctx.guild.id, view.selected_key)
    await ctx.send(embed=embed, view=view)


@config.command(name="panel", description="Ouvre le panel de configuration MK Arena")
@commands.guild_only()
async def config_panel(ctx: commands.Context):
    await ctx.send(
        content="⚔️ **MK Arena • Centre de contrôle**",
        embed=build_main_panel_embed(ctx.guild),
        view=MKArenaHomePanel(ctx.guild.id),
    )


@bot.tree.command(name="config", description="Ouvre le panel interactif de configuration MK Arena")
async def slash_config(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message(
            "❌ Utilise cette commande dans un serveur Discord.",
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        content="⚔️ **MK Arena • Centre de contrôle**",
        embed=build_main_panel_embed(interaction.guild),
        view=MKArenaHomePanel(interaction.guild.id),
        ephemeral=True,
    )


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
