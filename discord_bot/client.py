from __future__ import annotations

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
from commands.tickets import TicketManager

logger = logging.getLogger(__name__)


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
        self.engine = NovaEngine(self.knowledge, self.context)
        self.antiraid = AntiRaidManager(max_joins=5, window_seconds=10)
        self.tickets = TicketManager()
        self.tournament_scanner = None

    async def setup_hook(self):
        self._register_commands()
        await self.tree.sync()

    def _is_owner_or_admin(self, member: discord.Member) -> bool:
        return member.guild.owner_id == member.id or member.guild_permissions.administrator

    def _register_commands(self):
        # 1. Statut & Sync
        @self.tree.command(name="nova-status", description="Voir l'état de NOVA et de ses systèmes.")
        async def status(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
                return
            await interaction.response.send_message(
                format_nova_status("0.4-GLaDOS-Admin", self.db, self.tournament_scanner, self.db.count_knowledge()),
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

        # 2. Tickets
        @self.tree.command(name="ticket-open", description="Ouvrir un ticket d'assistance privé.")
        @app_commands.describe(sujet="Motif de votre demande")
        async def ticket_open(interaction: discord.Interaction, sujet: str = "Assistance"):
            if not isinstance(interaction.user, discord.Member) or not interaction.guild:
                return
            await interaction.response.defer(ephemeral=True)
            try:
                channel = await self.tickets.create_ticket(interaction.guild, interaction.user, topic=sujet)
                await interaction.followup.send(f"Ticket ouvert avec succès dans {channel.mention}.", ephemeral=True)
            except Exception as e:
                await interaction.followup.send(f"Erreur lors de l'ouverture du ticket : {e}", ephemeral=True)

        @self.tree.command(name="ticket-close", description="Fermer le ticket actuel.")
        async def ticket_close(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not isinstance(interaction.channel, discord.TextChannel):
                return
            if not interaction.channel.name.startswith("ticket-"):
                await interaction.response.send_message("Cette commande ne peut être exécutée que dans un salon de ticket.", ephemeral=True)
                return
            await interaction.response.send_message("Fermeture et incinération du ticket en cours...")
            await self.tickets.close_ticket(interaction.channel, interaction.user)

        # 3. Anti-Raid & Lockdown
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
                await interaction.response.send_message(f"📊 **Anti-Raid :** {current} | **Confinement :** {lock}", ephemeral=True)

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

        # 4. Modération & Actions Administrateur (Kick, Ban, Mute, Clear, Roles)
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
            await interaction.response.send_message(f"👞 **{membre.mention} a été expulsé.**\n*Raison :* {raison}")

        @self.tree.command(name="timeout", description="Mettre un membre en sourdine temporaire.")
        async def timeout_cmd(interaction: discord.Interaction, membre: discord.Member, minutes: int = 10, raison: str = "Période de réflexion"):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            duration = timedelta(minutes=minutes)
            await membre.timeout(duration, reason=raison)
            await interaction.response.send_message(f"⏳ **{membre.mention} est réduit au silence pendant {minutes} minutes.**\n*Raison :* {raison}")

        @self.tree.command(name="clear", description="Supprimer un nombre défini de messages.")
        async def clear_cmd(interaction: discord.Interaction, nombre: int = 10):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user) or not isinstance(interaction.channel, discord.TextChannel):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=nombre)
            await interaction.followup.send(f"🧹 **{len(deleted)} messages incinérés.**", ephemeral=True)

        @self.tree.command(name="role-add", description="Attribuer un rôle à un membre.")
        async def role_add_cmd(interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await membre.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle {role.mention} accordé à {membre.mention}.")

        @self.tree.command(name="role-remove", description="Retirer un rôle à un membre.")
        async def role_remove_cmd(interaction: discord.Interaction, membre: discord.Member, role: discord.Role):
            if not isinstance(interaction.user, discord.Member) or not self._is_owner_or_admin(interaction.user):
                await interaction.response.send_message("Réservé au créateur et administrateurs.", ephemeral=True)
                return
            await membre.remove_roles(role)
            await interaction.response.send_message(f"❌ Rôle {role.mention} retiré à {membre.mention}.")

    async def on_member_join(self, member: discord.Member):
        if not member.guild:
            return
        is_raid = self.antiraid.record_join(member.guild.id)
        if is_raid:
            logger.warning(f"Raid détecté sur {member.guild.name} ({member.guild.id}) !")
            await self.antiraid.apply_guild_lockdown(member.guild, lock=True)
            # Notifie le salon système ou le premier salon dispo
            target = member.guild.system_channel
            if target and target.permissions_for(member.guild.me).send_messages:
                await target.send("🚨 **[ALERTE APERTURE : RAID MASSIF DÉTECTÉ]**\nLe protocole de confinement automatique a été déclenché. Les salons ont été verrouillés.")

    async def on_ready(self):
        logger.info("NOVA est en ligne. Connexion réussie.")
        print(f"Connecté en tant que {self.user} ({self.user.id})")
        if self.tournament_scanner:
            try:
                await self.tournament_scanner.sync()
            except Exception as exc:
                logger.exception("Synchronisation initiale impossible : %s", exc)

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not self.engine.is_called(message.content):
            return

        content = self.engine.remove_call(message.content)
        if not content.strip():
            await message.reply("Oui, sujet de test ? J'écoute.")
            return

        # Direct Owner/Admin natural language quick commands
        is_admin = isinstance(message.author, discord.Member) and self._is_owner_or_admin(message.author)
        lower_content = content.lower()

        if is_admin and isinstance(message.channel, discord.TextChannel):
            # Commande de purge rapide: "nova clear 10" ou "nova purge 20"
            if lower_content.startswith(("clear ", "purge ", "nettoie ")):
                try:
                    num = int(lower_content.split()[1])
                    deleted = await message.channel.purge(limit=num + 1)
                    confirm = await message.channel.send(f"🧹 **{len(deleted)-1} messages détruits sur ordre du créateur.**")
                    return
                except Exception:
                    pass

            # Commande de lock rapide
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

        reference_context = None
        if message.reference and message.reference.resolved and isinstance(message.reference.resolved, discord.Message):
            reference_context = message.reference.resolved.content

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
