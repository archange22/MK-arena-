from __future__ import annotations

from systems.economy import EconomySystem
from systems.drafts import DraftSystem
from systems.giveaways import GiveawaySystem
from systems.polls import PollSystem
from systems.suggestions import SuggestionSystem
import time

import logging
from datetime import timedelta
import discord
from discord import app_commands

from ai.engine import NovaEngine
from ai.response import format_nova_status
from config.permissions import can_manage_nova
from memory.conversation import ConversationMemory
from memory.database import Database
from memory.knowledge import KnowledgeManager
from security.antiraid import AntiRaidManager
from security.automod import AutoModManager
from features.leveling import LevelingManager
from commands.tickets import TicketManager

logger = logging.getLogger(__name__)


class TicketLaunchView(discord.ui.View):
    def __init__(self, ticket_manager: TicketManager):
        super().__init__(timeout=None)
        self.ticket_manager = ticket_manager

    @discord.ui.button(label="Ouvrir un ticket", style=discord.ButtonStyle.success, emoji="📩", custom_id="nova_ticket_open")
    async def open_ticket_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return
        await interaction.response.defer(ephemeral=True)
        try:
            channel = await self.ticket_manager.create_ticket(
                interaction.guild,
                interaction.user,
                topic="Assistance générale"
            )
            await interaction.followup.send(f"✅ Votre ticket a été créé : {channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Erreur création ticket : {e}", ephemeral=True)


class NovaClient(discord.Client):
    def __init__(self, settings, db: Database):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.db = db
        self.tree = app_commands.CommandTree(self)
        self.context = ConversationMemory(db, settings.context_ttl_minutes, getattr(settings, "max_context_messages", 20))
        self.knowledge = KnowledgeManager(db)
        self.engine = NovaEngine(self.knowledge, self.context, self.db)
        self.antiraid = AntiRaidManager(max_joins=5, window_seconds=10)
        self.automod = AutoModManager()
        self.leveling = LevelingManager(db)
        self.tickets = TicketManager()
        self.tournament_scanner = None
        self.economy = EconomySystem(db)
        self.drafts = DraftSystem(db)
        self.giveaways = GiveawaySystem(db)
        self.polls = PollSystem(db)
        self.suggestions = SuggestionSystem(db)
        self.start_time = time.time()

    async def setup_hook(self):
        self._register_commands()
        self.add_view(TicketLaunchView(self.tickets))
        await self.tree.sync()

    def _is_owner_or_admin(self, member: discord.Member) -> bool:
        return member.guild.owner_id == member.id or member.guild_permissions.administrator

    def _register_commands(self):
        # --- COMMANDES GENERALES ---
        @self.tree.command(name="ping", description="Vérifier la latence du bot.")
        async def ping_cmd(interaction: discord.Interaction):
            latency = round(self.latency * 1000)
            await interaction.response.send_message(f"🏓 Pong ! Latence API : **{latency}ms**.")

        @self.tree.command(name="uptime", description="Afficher le temps de fonctionnement du bot.")
        async def uptime_cmd(interaction: discord.Interaction):
            uptime_sec = int(time.time() - getattr(self, "start_time", time.time()))
            hours, rem = divmod(uptime_sec, 3600)
            mins, secs = divmod(rem, 60)
            await interaction.response.send_message(f"⏱️ NOVA est en ligne depuis : **{hours}h {mins}m {secs}s**.")

        @self.tree.command(name="botinfo", description="Informations et statistiques sur NOVA.")
        async def botinfo_cmd(interaction: discord.Interaction):
            embed = discord.Embed(
                title="🤖 NOVA v3 • MK ARENA x DraftBot Edition",
                description="Bot officiel Aperture MK Arena : Drafts CODM, Tournois, Modération & Économie.",
                color=0x10b981
            )
            embed.add_field(name="Serveurs", value=str(len(self.guilds)), inline=True)
            embed.add_field(name="Latence", value=f"{round(self.latency * 1000)}ms", inline=True)
            embed.add_field(name="Architecture", value="Modulaire v3 • Python 3.11+", inline=True)
            await interaction.response.send_message(embed=embed)

        # --- ECONOMIE DRAFTBOT ---
        @self.tree.command(name="balance", description="Consulter votre solde de crédits Aperture.")
        async def balance_cmd(interaction: discord.Interaction, membre: discord.Member = None):
            target = membre or interaction.user
            acc = self.economy.get_account(interaction.guild_id, target.id)
            embed = discord.Embed(
                title=f"💳 Portefeuille de {target.display_name}",
                color=0xf59e0b
            )
            embed.add_field(name="Portefeuille", value=f"{acc['wallet']} 🪙", inline=True)
            embed.add_field(name="Banque", value=f"{acc['bank']} 🪙", inline=True)
            embed.add_field(name="Total", value=f"{acc['wallet'] + acc['bank']} 🪙", inline=True)
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="daily", description="Récupérer votre récompense quotidienne (250 crédits).")
        async def daily_cmd(interaction: discord.Interaction):
            ok, msg, _ = self.economy.claim_daily(interaction.guild_id, interaction.user.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="weekly", description="Récupérer votre prime hebdomadaire (1500 crédits).")
        async def weekly_cmd(interaction: discord.Interaction):
            ok, msg, _ = self.economy.claim_weekly(interaction.guild_id, interaction.user.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="work", description="Travailler pour gagner des crédits.")
        async def work_cmd(interaction: discord.Interaction):
            ok, msg, _ = self.economy.work(interaction.guild_id, interaction.user.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="pay", description="Transférer des crédits à un autre membre.")
        @app_commands.describe(membre="Bénéficiaire", montant="Montant à envoyer")
        async def pay_cmd(interaction: discord.Interaction, membre: discord.Member, montant: int):
            if membre.id == interaction.user.id:
                await interaction.response.send_message("Vous ne pouvez pas vous transférer de l'argent à vous-même.", ephemeral=True)
                return
            ok, msg = self.economy.transfer(interaction.guild_id, interaction.user.id, membre.id, montant)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="richest", description="Classement des membres les plus riches.")
        async def richest_cmd(interaction: discord.Interaction):
            lb = self.economy.get_leaderboard(interaction.guild_id)
            if not lb:
                await interaction.response.send_message("Aucun compte économique enregistré.", ephemeral=True)
                return
            embed = discord.Embed(title="💰 Top 10 • Les plus fortunés de MK ARENA", color=0xf59e0b)
            for idx, r in enumerate(lb, start=1):
                m = interaction.guild.get_member(r['user_id'])
                name = m.display_name if m else f"Membre ({r['user_id']})"
                embed.add_field(name=f"#{idx} {name}", value=f"**{r['total']} 🪙** (Cash: {r['wallet']} | Banque: {r['bank']})", inline=False)
            await interaction.response.send_message(embed=embed)

        # --- DRAFTS & COMPETITION ESPORT ---
        @self.tree.command(name="draft-create", description="Créer une session de Draft compétitive.")
        @app_commands.describe(capitaine1="Premier capitaine", capitaine2="Deuxième capitaine", format="Format du match")
        @app_commands.choices(format=[
            app_commands.Choice(name="BO1", value="BO1"),
            app_commands.Choice(name="BO3", value="BO3"),
            app_commands.Choice(name="BO5", value="BO5"),
        ])
        async def draft_create_cmd(interaction: discord.Interaction, capitaine1: discord.Member, capitaine2: discord.Member, format: app_commands.Choice[str]):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Réservé au staff et organisateurs.", ephemeral=True)
                return
            draft_id = self.drafts.create_draft(interaction.guild_id, capitaine1.id, capitaine2.id, bo_type=format.value)
            desc = (
                f"**Format :** {format.value}\n"
                f"**Capitaine 1 :** {capitaine1.mention}\n"
                f"**Capitaine 2 :** {capitaine2.mention}\n\n"
                f"👉 Les joueurs peuvent taper `/draft-join {draft_id}` pour entrer dans la pool !"
            )
            embed = discord.Embed(title=f"🎮 Session de Draft #{draft_id} Initiée !", description=desc, color=0x10b981)
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="draft-join", description="Rejoindre la pool de sélection d'un draft.")
        @app_commands.describe(draft_id="Identifiant du draft")
        async def draft_join_cmd(interaction: discord.Interaction, draft_id: int):
            ok, msg = self.drafts.join_pool(draft_id, interaction.user.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="draft-pick", description="Capitaine : choisir un joueur dans la pool.")
        @app_commands.describe(draft_id="Identifiant du draft", joueur="Joueur sélectionné")
        async def draft_pick_cmd(interaction: discord.Interaction, draft_id: int, joueur: discord.Member):
            ok, msg = self.drafts.pick_player(draft_id, interaction.user.id, joueur.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="draft-ban", description="Capitaine : bannir une map ou arme pour le match.")
        @app_commands.describe(draft_id="Identifiant du draft", element="Nom de la map ou arme à bannir")
        async def draft_ban_cmd(interaction: discord.Interaction, draft_id: int, element: str):
            ok, msg = self.drafts.ban_element(draft_id, interaction.user.id, element)
            await interaction.response.send_message(msg, ephemeral=not ok)

        @self.tree.command(name="draft-status", description="Voir le statut et les équipes d'un draft.")
        @app_commands.describe(draft_id="Identifiant du draft")
        async def draft_status_cmd(interaction: discord.Interaction, draft_id: int):
            d = self.drafts.get_draft(draft_id)
            if not d:
                await interaction.response.send_message("Draft introuvable.", ephemeral=True)
                return
            embed = discord.Embed(title=f"📋 Statut Draft #{draft_id} ({d['state'].upper()})", color=0x3b82f6)
            embed.add_field(name="Format", value=d['bo_type'], inline=True)
            embed.add_field(name="Capitaine 1", value=f"<@{d['captain1_id']}>", inline=True)
            embed.add_field(name="Capitaine 2", value=f"<@{d['captain2_id']}>", inline=True)
            t1_names = ", ".join(f"<@{u}>" for u in d['team1']) or "Aucun joueur"
            t2_names = ", ".join(f"<@{u}>" for u in d['team2']) or "Aucun joueur"
            embed.add_field(name="Équipe 1", value=t1_names, inline=False)
            embed.add_field(name="Équipe 2", value=t2_names, inline=False)
            pool_names = ", ".join(f"<@{u}>" for u in d['pool']) or "Pool vide"
            embed.add_field(name="Pool restante", value=pool_names, inline=False)
            bans_str = ", ".join(f"{b['element']}" for b in d['bans']) or "Aucun ban"
            embed.add_field(name="Bans actifs", value=bans_str, inline=False)
            await interaction.response.send_message(embed=embed)

        # --- GIVEAWAYS ---
        @self.tree.command(name="giveaway-start", description="Lancer un tirage au sort Giveaway.")
        @app_commands.describe(lot="Lot à gagner", gagnants="Nombre de gagnants", minutes="Durée en minutes")
        async def giveaway_start_cmd(interaction: discord.Interaction, lot: str, gagnants: int = 1, minutes: int = 60):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
                return
            gid = self.giveaways.start_giveaway(interaction.guild_id, interaction.channel_id, lot, gagnants, minutes * 60)
            desc = (
                f"**Lot :** {lot}\n"
                f"**Nombre de gagnant(s) :** {gagnants}\n"
                f"**Durée :** {minutes} minute(s)\n\n"
                f"Participez avec `/giveaway-enter {gid}` !"
            )
            embed = discord.Embed(title="🎉 NOUVEAU GIVEAWAY !", description=desc, color=0xef4444)
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message(f"✅ Giveaway #{gid} lancé.", ephemeral=True)

        @self.tree.command(name="giveaway-enter", description="Participer à un giveaway en cours.")
        @app_commands.describe(giveaway_id="ID du giveaway")
        async def giveaway_enter_cmd(interaction: discord.Interaction, giveaway_id: int):
            ok, msg = self.giveaways.enter_giveaway(giveaway_id, interaction.user.id)
            await interaction.response.send_message(msg, ephemeral=not ok)

        # --- SONDAGES ---
        @self.tree.command(name="poll", description="Créer un sondage interactif pour la communauté.")
        @app_commands.describe(question="Question posée", option1="Choix 1", option2="Choix 2", option3="Choix 3 (optionnel)")
        async def poll_cmd(interaction: discord.Interaction, question: str, option1: str, option2: str, option3: str = None):
            options = [option1, option2]
            if option3:
                options.append(option3)
            pid = self.polls.create_poll(interaction.guild_id, question, options)
            opts_lines = "\n".join(f"• Option {idx+1} : **{opt}** (`/poll-vote {pid} {idx+1}`)" for idx, opt in enumerate(options))
            embed = discord.Embed(
                title=f"📊 Sondage #{pid} : {question}",
                description=f"Exprimez votre vote :\n{opts_lines}",
                color=0x3b82f6
            )
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Sondage publié.", ephemeral=True)

        @self.tree.command(name="poll-vote", description="Voter dans un sondage.")
        @app_commands.describe(poll_id="ID du sondage", choix="Numéro de votre choix (1, 2, 3...)")
        async def poll_vote_cmd(interaction: discord.Interaction, poll_id: int, choix: int):
            ok, msg = self.polls.vote(poll_id, interaction.user.id, choix - 1)
            await interaction.response.send_message(msg, ephemeral=not ok)

        # --- SUGGESTIONS ---
        @self.tree.command(name="suggest", description="Soumettre une suggestion pour MK ARENA.")
        @app_commands.describe(proposition="Votre idée ou proposition")
        async def suggest_cmd(interaction: discord.Interaction, proposition: str):
            sid = self.suggestions.add_suggestion(interaction.guild_id, interaction.user.id, proposition)
            embed = discord.Embed(title=f"💡 Suggestion #{sid}", description=proposition, color=0x10b981)
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            embed.set_footer(text="Votez avec /suggest-vote [id] [pour/contre]")
            await interaction.channel.send(embed=embed)
            await interaction.response.send_message("✅ Votre suggestion a été transmise.", ephemeral=True)

        # 1. Panel Web Admin
        @self.tree.command(name="panel", description="Accéder au panel d'administration Web de NOVA (Style DraftBot).")
        async def panel_cmd(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Tu n'as pas la permission d'accéder au panel d'administration.", ephemeral=True)
                return
            render_url = "https://mk-arena-.onrender.com"
            embed = discord.Embed(
                title="⚙️ Panel d'Administration NOVA x MK ARENA",
                description=(
                    "Le panel web complet (style DraftBot) vous permet de configurer :\n"
                    "• **Messages de bienvenue & Auto-Rôle**\n"
                    "• **Auto-Modération (Anti-Raid, Anti-Spam, Anti-Liens, Blacklist)**\n"
                    "• **Système de Tickets & Catégories**\n"
                    "• **Niveaux & Récompenses XP**\n"
                    "• **Tournois & Scrims MK ARENA**\n"
                    "• **Matrice IA GLaDOS & Personality Cores**\n\n"
                    f"👉 **[Ouvrir le Panel Admin Web]({render_url})**"
                ),
                color=0x10b981
            )
            embed.set_footer(text="Aperture Science & MK Arena • Administration")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        # 2. Statut & Sync
        @self.tree.command(name="nova-status", description="Voir l'état de NOVA et de ses systèmes.")
        async def status(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
                return
            await interaction.response.send_message(
                format_nova_status("0.5-DraftBot-Panel", self.db, self.tournament_scanner, self.db.count_knowledge()),
                ephemeral=True,
            )

        @self.tree.command(name="nova-sync", description="Synchroniser la catégorie TOURNOIS.")
        async def sync(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Accès refusé.", ephemeral=True)
                return
            if not self.tournament_scanner:
                await interaction.response.send_message("Scanner indisponible.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            count = await self.tournament_scanner.sync()
            await interaction.followup.send(f"Synchronisation terminée : {count} salon(s) analysé(s).", ephemeral=True)

        # 3. Tickets
        @self.tree.command(name="setup-tickets", description="Envoyer le panel d'ouverture de tickets interactif.")
        async def setup_tickets_cmd(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Permission refusée.", ephemeral=True)
                return
            embed = discord.Embed(
                title="📩 Centre d'Assistance • MK ARENA",
                description="Cliquez sur le bouton ci-dessous pour ouvrir un ticket privé avec le staff.\n\n*Pour réclamation tournoi, question scrims ou support général.*",
                color=0x10b981
            )
            embed.set_footer(text="Système de tickets Aperture / MK Arena")
            await interaction.channel.send(embed=embed, view=TicketLaunchView(self.tickets))
            await interaction.response.send_message("✅ Panel de tickets envoyé avec succès.", ephemeral=True)

        @self.tree.command(name="ticket-close", description="Fermer le ticket actuel.")
        async def ticket_close(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not isinstance(interaction.channel, discord.TextChannel):
                return
            if not interaction.channel.name.startswith("ticket-"):
                await interaction.response.send_message("Cette commande ne peut être exécutée que dans un ticket.", ephemeral=True)
                return
            await interaction.response.send_message("Fermeture et incinération du ticket en cours...")
            await self.tickets.close_ticket(interaction.channel, interaction.user)

        # 4. Warns & Modération DraftBot
        @self.tree.command(name="warn", description="Avertir un membre avec sanction automatique.")
        @app_commands.describe(membre="Membre à sanctionner", raison="Motif du warn")
        async def warn_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str = "Non-respect des règles"):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            
            warn_id = self.db.add_warn(interaction.guild_id, membre.id, interaction.user.id, raison)
            all_warns = self.db.get_warns(interaction.guild_id, membre.id)
            total = len(all_warns)

            sanction = ""
            if total >= 5:
                await interaction.guild.ban(membre, reason=f"5 Avertissements atteints ({raison})")
                sanction = "\n🚨 **Seuil critique (5 warns) atteint : BAN AUTOMATIQUE appliqué.**"
            elif total >= 3:
                await membre.timeout(timedelta(hours=1), reason=f"3 Avertissements atteints ({raison})")
                sanction = "\n⚠️ **Seuil de 3 warns atteint : MUTE temporaire de 1 heure appliqué.**"

            embed = discord.Embed(
                title="⚠️ Avertissement infligé",
                description=f"{membre.mention} a reçu un avertissement (Warn #{warn_id}).\n**Raison :** {raison}\n**Total actuel :** {total} avertissement(s).{sanction}",
                color=0xf59e0b
            )
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="warnings", description="Voir les avertissements d'un membre.")
        @app_commands.describe(membre="Membre à inspecter")
        async def warnings_cmd(interaction: discord.Interaction, membre: discord.Member):
            warns = self.db.get_warns(interaction.guild_id, membre.id)
            if not warns:
                await interaction.response.send_message(f"✅ {membre.mention} n'a aucun avertissement dans son dossier.", ephemeral=True)
                return
            embed = discord.Embed(
                title=f"📋 Dossier disciplinaire de {membre.display_name}",
                description=f"Nombre total d'avertissements : **{len(warns)}**",
                color=0xef4444
            )
            for w in warns[:10]:
                embed.add_field(name=f"Warn #{w['id']} • {w['created_at'][:10]}", value=f"**Raison :** {w['reason']}", inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        @self.tree.command(name="clearwarns", description="Effacer tous les avertissements d'un membre.")
        @app_commands.describe(membre="Membre à réhabiliter")
        async def clearwarns_cmd(interaction: discord.Interaction, membre: discord.Member):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            self.db.clear_warns(interaction.guild_id, membre.id)
            await interaction.response.send_message(f"🧹 Le casier disciplinaire de {membre.mention} a été entièrement effacé.")

        # 5. Niveaux & XP (Rank / Leaderboard)
        @self.tree.command(name="rank", description="Afficher votre carte de rang et niveau XP.")
        @app_commands.describe(membre="Membre dont vous voulez voir le rang (optionnel)")
        async def rank_cmd(interaction: discord.Interaction, membre: discord.Member = None):
            target = membre or interaction.user
            if not isinstance(target, discord.Member):
                return
            info = self.leveling.get_rank_info(interaction.guild_id, target.id)
            embed = discord.Embed(
                title=f"🎮 Carte de Niveau • {target.display_name}",
                color=0x10b981
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.add_field(name="🏆 Rang", value=f"#{info['rank']}", inline=True)
            embed.add_field(name="⭐ Niveau", value=f"{info['level']}", inline=True)
            embed.add_field(name="💬 Messages", value=f"{info['messages']}", inline=True)
            embed.add_field(name="📈 Progression XP", value=f"{info['progress']} / {info['needed']} XP (Total: {info['xp']})", inline=False)
            await interaction.response.send_message(embed=embed)

        @self.tree.command(name="leaderboard", description="Classement des 10 membres les plus actifs.")
        async def leaderboard_cmd(interaction: discord.Interaction):
            board = self.db.get_leaderboard(interaction.guild_id, limit=10)
            if not board:
                await interaction.response.send_message("Aucune donnée d'XP pour le moment.", ephemeral=True)
                return
            embed = discord.Embed(
                title="🏆 Top 10 • Classement d'Activité MK ARENA",
                description="Les membres les plus engagés du serveur :",
                color=0xf59e0b
            )
            for idx, row in enumerate(board, start=1):
                user = interaction.guild.get_member(row["user_id"])
                name = user.display_name if user else f"Membre ({row['user_id']})"
                medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else f"#{idx}"
                embed.add_field(
                    name=f"{medal} {name}",
                    value=f"Niveau **{row['level']}** • **{row['xp']}** XP ({row['messages_count']} messages)",
                    inline=False
                )
            await interaction.response.send_message(embed=embed)

        # 6. Anti-Raid & Lockdown
        @self.tree.command(name="anti-raid", description="Activer ou désactiver la protection anti-raid.")
        @app_commands.describe(etat="activer ou désactiver")
        @app_commands.choices(etat=[
            app_commands.Choice(name="Activer", value="on"),
            app_commands.Choice(name="Désactiver", value="off"),
            app_commands.Choice(name="Statut", value="status"),
        ])
        async def antiraid_cmd(interaction: discord.Interaction, etat: app_commands.Choice[str]):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Accès réservé au créateur et administrateurs.", ephemeral=True)
                return
            if etat.value == "on":
                self.antiraid.set_enabled(interaction.guild_id, True)
                await interaction.response.send_message("🛡️ **Système Anti-Raid APERTURE activé.**", ephemeral=True)
            elif etat.value == "off":
                self.antiraid.set_enabled(interaction.guild_id, False)
                await interaction.response.send_message("⚠️ **Système Anti-Raid APERTURE désactivé.**", ephemeral=True)
            else:
                current = "Actif" if self.antiraid.is_enabled(interaction.guild_id) else "Inactif"
                lock = "En cours" if self.antiraid.is_in_lockdown(interaction.guild_id) else "Normal"
                await interaction.response.send_message(f"🛡️ **Anti-Raid :** {current} | **Confinement :** {lock}", ephemeral=True)

        @self.tree.command(name="lockdown", description="Verrouiller ou déverrouiller tous les salons en urgence.")
        @app_commands.describe(action="activer ou désactiver le confinement")
        @app_commands.choices(action=[
            app_commands.Choice(name="Activer Confinement (Lock)", value="lock"),
            app_commands.Choice(name="Désactiver Confinement (Unlock)", value="unlock"),
        ])
        async def lockdown_cmd(interaction: discord.Interaction, action: app_commands.Choice[str]):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user) or not interaction.guild:
                await interaction.response.send_message("Permission refusée.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            lock = action.value == "lock"
            count = await self.antiraid.apply_guild_lockdown(interaction.guild, lock=lock)
            msg = f"🔒 **Confinement activé :** {count} salons verrouillés." if lock else f"🔓 **Confinement levé :** {count} salons réouverts."
            await interaction.followup.send(msg, ephemeral=True)

        # 7. Modération classique
        @self.tree.command(name="ban", description="Bannir un membre du serveur.")
        async def ban_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str = "Expulsion ordonnée par la direction"):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await interaction.guild.ban(membre, reason=f"{raison} (par {interaction.user})")
            await interaction.response.send_message(f"☣️ **{membre.mention} a été banni du serveur.**\n*Raison :* {raison}")

        @self.tree.command(name="kick", description="Expulser un membre du serveur.")
        async def kick_cmd(interaction: discord.Interaction, membre: discord.Member, raison: str = "Non-respect des règles"):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await interaction.guild.kick(membre, reason=f"{raison} (par {interaction.user})")
            await interaction.response.send_message(f"👢 **{membre.mention} a été expulsé.**\n*Raison :* {raison}")

        @self.tree.command(name="timeout", description="Mettre un membre en sourdine temporaire.")
        async def timeout_cmd(interaction: discord.Interaction, membre: discord.Member, minutes: int = 10, raison: str = "Période de réflexion"):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            duration = timedelta(minutes=minutes)
            await membre.timeout(duration, reason=raison)
            await interaction.response.send_message(f"🔇 **{membre.mention} est réduit au silence pendant {minutes} minutes.**\n*Raison :* {raison}")

        @self.tree.command(name="clear", description="Supprimer un nombre défini de messages.")
        async def clear_cmd(interaction: discord.Interaction, nombre: int = 10):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user) or not isinstance(interaction.channel, discord.TextChannel):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=nombre)
            await interaction.followup.send(f"🗑️ **{len(deleted)} messages incinérés.**", ephemeral=True)

    async def on_member_join(self, member: discord.Member):
        if not member.guild:
            return

        # 1. Protection Anti-Raid
        is_raid = self.antiraid.record_join(member.guild.id)
        if is_raid:
            logger.warning(f"Raid détecté sur {member.guild.name} ({member.guild.id}) !")
            await self.antiraid.apply_guild_lockdown(member.guild, lock=True)
            target = member.guild.system_channel
            if target and target.permissions_for(member.guild.me).send_messages:
                await target.send("🚨 **[ALERTE APERTURE : RAID MASSIF DÉTECTÉ]**\nLe protocole de confinement automatique a été déclenché. Les salons ont été verrouillés.")
            return

        # 2. Configuration Bienvenue & Auto-Rôle (Panel DraftBot)
        settings = self.db.get_guild_settings(member.guild.id)

        # Attribution Auto-rôle
        autorole_id = settings.get("autorole_id")
        if autorole_id:
            try:
                role = member.guild.get_role(int(autorole_id))
                if role:
                    await member.add_roles(role)
            except Exception as e:
                logger.warning(f"Impossible d'assigner l'auto-rôle : {e}")

        # Message de Bienvenue
        if settings.get("welcome_enabled"):
            w_channel_id = settings.get("welcome_channel_id")
            target_channel = member.guild.get_channel(int(w_channel_id)) if w_channel_id else member.guild.system_channel
            if target_channel and target_channel.permissions_for(member.guild.me).send_messages:
                template = settings.get("welcome_message", "Bienvenue {user} sur {server} !")
                text = template.replace("{user}", member.mention).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
                embed = discord.Embed(
                    title=f"👋 Bienvenue sur {member.guild.name} !",
                    description=text,
                    color=0x10b981
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text=f"Membre #{member.guild.member_count} • Aperture Science Facility")
                await target_channel.send(embed=embed)

    async def on_member_remove(self, member: discord.Member):
        if not member.guild:
            return
        settings = self.db.get_guild_settings(member.guild.id)
        if settings.get("leave_enabled"):
            l_channel_id = settings.get("leave_channel_id")
            target_channel = member.guild.get_channel(int(l_channel_id)) if l_channel_id else member.guild.system_channel
            if target_channel and target_channel.permissions_for(member.guild.me).send_messages:
                template = settings.get("leave_message", "Au revoir {user}...")
                text = template.replace("{user}", member.name).replace("{server}", member.guild.name).replace("{count}", str(member.guild.member_count))
                await target_channel.send(text)

    async def on_ready(self):
        logger.info("NOVA V2 est en ligne avec Panel DraftBot actif.")
        print(f"Connecté en tant que {self.user} ({self.user.id})")
        if self.tournament_scanner:
            try:
                await self.tournament_scanner.sync()
            except Exception as exc:
                logger.exception("Synchronisation initiale impossible : %s", exc)

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        settings = self.db.get_guild_settings(message.guild.id)

        # 1. Vérification AutoModérateur
        is_violation, reason = self.automod.check_message(message.author.id, message.content, settings)
        if is_violation:
            try:
                await message.delete()
                warning_msg = await message.channel.send(f"⚠️ {message.author.mention}, votre message a été supprimé par l'AutoMod : *{reason}*")
                # Auto-suppression de l'avertissement après 6 secondes
                import asyncio
                await asyncio.sleep(6)
                await warning_msg.delete()
            except Exception:
                pass
            return

        # 2. Gain d'XP & Niveaux (Leveling)
        if settings.get("xp_enabled", 1):
            rate = float(settings.get("xp_rate", 1.0))
            xp, level, level_up = self.leveling.process_message(message.guild.id, message.author.id, rate=rate)
            if level_up:
                embed = discord.Embed(
                    title="🎉 Montée de Niveau !",
                    description=f"Félicitations {message.author.mention}, vous passez au **Niveau {level}** !",
                    color=0x10b981
                )
                await message.channel.send(embed=embed)

        # 2.5 Déclencheurs automatiques / Custom Triggers (ex: !staff, !recrutement, etc.)
        matched_trigger = self.db.find_matching_trigger(message.guild.id, message.content)
        if matched_trigger:
            await message.channel.send(matched_trigger["response_text"])
            return

        # 3. Conversation & Commandes IA / GLaDOS
        if not self.engine.is_called(message.content):
            return

        content = self.engine.remove_call(message.content)
        if not content.strip():
            await message.reply("Oui, sujet de test ? J'écoute.")
            return

        # --- Connexion NOVA API (Site Web) ---
        try:
            from nova_api import ask_nova_api
            nova_reply = await ask_nova_api(str(message.channel.id), content, message.author.display_name)
            if nova_reply:
                await message.reply(nova_reply)
                return
        except Exception as e:
            logger.warning(f"Erreur appel NOVA API: {e}")

        # Commandes naturelles administrateur
        is_admin = isinstance(message.author, discord.Member) and self._is_owner_or_admin(message.author)
        lower_content = content.lower()

        if is_admin and isinstance(message.channel, discord.TextChannel):
            if lower_content.startswith(("clear ", "purge ", "nettoie ")):
                try:
                    num = int(lower_content.split()[1])
                    deleted = await message.channel.purge(limit=num + 1)
                    await message.channel.send(f"🗑️ **{len(deleted)-1} messages détruits sur ordre du créateur.**")
                    return
                except Exception:
                    pass

            if lower_content in ["lock", "verrouille", "ferme le salon"]:
                overwrites = message.channel.overwrites_for(message.guild.default_role)
                overwrites.send_messages = False
                await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
                await message.reply("🔒 **Salon verrouillé. Silence exigé.**")
                return

            if lower_content in ["unlock", "deverrouille", "déverrouille", "ouvre le salon"]:
                overwrites = message.channel.overwrites_for(message.guild.default_role)
                overwrites.send_messages = None
                await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
                await message.reply("🔓 **Salon déverrouillé. Vous pouvez reprendre vos activités.**")
                return

        # Contexte et réponse IA
        reference_context = None
        if message.reference and message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
            reference_context = message.reference.resolved.content

        # 3.1 Gestion des règles personnalisées en langage naturel
        rule_action, rule_trig, rule_resp = self.engine.parse_rule_instruction(content)
        if rule_action == "add" and rule_trig and rule_resp:
            if not isinstance(message.author, discord.Member) or not can_manage_nova(message.author):
                await message.reply("⛔ Vous n'avez pas la permission d'ajouter des règles personnalisées pour NOVA.")
                return
            self.db.add_custom_trigger(message.guild.id, rule_trig, rule_resp, created_by=message.author.id)
            await message.reply(
                f"✅ **Règle enregistrée avec succès !**\n"
                f"Désormais, dès que quelqu'un tape `{rule_trig}`, j'enverrai automatiquement :\n"
                f"> {rule_resp}"
            )
            return

        if rule_action == "delete" and rule_trig:
            if not isinstance(message.author, discord.Member) or not can_manage_nova(message.author):
                await message.reply("⛔ Vous n'avez pas la permission de supprimer des règles personnalisées.")
                return
            deleted = self.db.delete_custom_trigger(message.guild.id, rule_trig)
            if deleted:
                await message.reply(f"🗑️ La règle pour `{rule_trig}` a bien été supprimée.")
            else:
                await message.reply(f"❓ Aucune règle active trouvée pour `{rule_trig}`.")
            return

        if rule_action == "list":
            triggers = self.db.get_custom_triggers(message.guild.id)
            if not triggers:
                await message.reply("📋 Aucune règle personnalisée n'est actuellement configurée sur ce serveur.")
                return
            lines = ["📋 **Commandes & Règles automatiques actives sur ce serveur :**"]
            for t in triggers:
                lines.append(f"• `{t['trigger_text']}` ➔ {t['response_text'][:80]}")
            await message.reply("\n".join(lines))
            return

        quoted_staff = content.strip().startswith('"') and content.strip().endswith('"')
        if quoted_staff:
            if not isinstance(message.author, discord.Member) or not can_manage_nova(message.author):
                await message.reply("Je peux discuter avec toi, mais tu n'as pas la permission de modifier mes connaissances.")
                return
            content = content.strip()[1:-1].strip()
            if content.lower().startswith(("nova ", "nova:")):
                content = content[4:].lstrip(": ").strip()
            saved = self.knowledge.learn(content, source=f"staff:{message.author.id}", guild_id=message.guild.id)
            self.context.add(message.author.id, "user", content)
            self.context.add(message.author.id, "assistant", saved)
            await message.reply(saved)
            return

        response = self.engine.respond(
            user_id=message.author.id,
            guild_id=message.guild.id,
            text=content,
            reference_context=reference_context,
        )
        self.context.add(message.author.id, "user", content)
        self.context.add(message.author.id, "assistant", response)
        await message.reply(response)
