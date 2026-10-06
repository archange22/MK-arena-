import re
import logging
import discord
from discord.ext import commands
from discord import app_commands
from bot.permissions import is_authorized

logger = logging.getLogger("cogs.tickets")

INSCRIPTION_TEMPLATE = """# 🎮 INSCRIPTION DE L’ÉQUIPE

**Nom de la team :**
**Capitaine :**

## 👥 Joueurs titulaires

**1️⃣ Joueur 1**
> Discord :
> IGN :
> UID :

**2️⃣ Joueur 2**
> Discord :
> IGN :
> UID :

**3️⃣ Joueur 3**
> Discord :
> IGN :
> UID :

**4️⃣ Joueur 4**
> Discord :
> IGN :
> UID :

**5️⃣ Joueur 5**
> Discord :
> IGN :
> UID :

## 🔄 Remplaçants

**6️⃣ Remplaçant 1**
> Discord :
> IGN :
> UID :

**7️⃣ Remplaçant 2**
> Discord :
> IGN :
> UID :"""

TICKET_TYPES = {
    "inscription": {
        "label": "Inscription Tournoi",
        "emoji": "🏆",
        "description": "Inscrire une équipe ou un joueur à un tournoi CODM",
        "channel_prefix": "tournoi",
        "title": "🏆 Inscription Tournoi MK ARENA",
        "is_tournament": True
    },
    "staff": {
        "label": "Recrutement Staff",
        "emoji": "🛡️",
        "description": "Postuler pour rejoindre l'équipe d'administration ou modération",
        "channel_prefix": "recrut-staff",
        "title": "🛡️ Recrutement Staff MK ARENA",
        "instructions": (
            "Bienvenue dans votre salon de candidature Staff !\n\n"
            "Merci d'indiquer :\n"
            "• **Votre âge et disponibilité**\n"
            "• **Le poste visé** (Modérateur, Arbitre tournois, Animateur, etc.)\n"
            "• **Vos expériences passées** sur Discord ou dans l'esport\n"
            "• **Vos motivations** pour rejoindre le staff MK ARENA"
        )
    },
    "clan": {
        "label": "Recrutement Clan MK",
        "emoji": "⚔️",
        "description": "Rejoindre le clan compétitif MK sur Call of Duty: Mobile",
        "channel_prefix": "recrut-clan",
        "title": "⚔️ Recrutement Clan MK ARENA",
        "instructions": (
            "Bienvenue dans votre salon de recrutement de clan !\n\n"
            "Merci de renseigner :\n"
            "• **Votre pseudo & ID joueur CODM**\n"
            "• **Votre rang actuel & historique** (Légendaire, points, etc.)\n"
            "• **Votre rôle préféré** (Slayer, Anchor, OBJ, Sniper)\n"
            "• **Vos disponibilités** pour les scrims et entraînements"
        )
    },
    "support": {
        "label": "Support & Questions",
        "emoji": "❓",
        "description": "Poser une question ou demander de l'aide au staff",
        "channel_prefix": "support",
        "title": "❓ Support & Assistance MK ARENA",
        "instructions": (
            "Bienvenue dans votre salon de support !\n\n"
            "Veuillez détailler précisément votre demande ou problème.\n"
            "Un membre de l'équipe vous répondra dans les plus brefs délais."
        )
    }
}

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="mk:ticket:close")
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fermeture du ticket en cours...", ephemeral=False)
        try:
            if isinstance(interaction.channel, discord.TextChannel):
                await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except discord.Forbidden:
            await interaction.followup.send("❌ Erreur : Le bot n'a pas la permission de supprimer ce salon (Permission 'Gérer les salons' requise).", ephemeral=True)
        except Exception as e:
            logger.error("Erreur suppression salon: %s", e)
            await interaction.followup.send(f"❌ Impossible de supprimer le salon : {e}", ephemeral=True)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=data["label"],
                value=key,
                emoji=data["emoji"],
                description=data["description"]
            )
            for key, data in TICKET_TYPES.items()
        ]
        super().__init__(
            placeholder="Sélectionnez le type de ticket à ouvrir...",
            min_values=1,
            max_values=1,
            custom_id="mk:ticket:select",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        ticket_key = self.values[0]
        cfg = TICKET_TYPES.get(ticket_key)
        if not cfg:
            await interaction.response.send_message("❌ Type de ticket invalide.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Cette action doit être effectuée sur un serveur.", ephemeral=True)
            return

        # Sanitize nom du salon (minuscules, chiffres, tirets uniquement)
        raw_name = getattr(interaction.user, "name", "user").lower()
        clean_name = re.sub(r"[^a-z0-9]", "", raw_name)[:12] or str(interaction.user.id)[:8]
        prefix = cfg["channel_prefix"]
        expected_channel_name = f"{prefix}-{clean_name}"

        # Éviter doublon si déjà ouvert
        existing = discord.utils.get(guild.text_channels, name=expected_channel_name)
        if existing:
            await interaction.response.send_message(
                f"⚠️ Vous avez déjà un ticket ouvert de ce type : {existing.mention}",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        bot_member = guild.me or guild.get_member(interaction.client.user.id)
        if not bot_member or not bot_member.guild_permissions.manage_channels:
            await interaction.followup.send(
                "❌ **Erreur de permission Discord** : Le bot doit avoir la permission **Gérer les salons** (`Manage Channels`) pour créer des tickets. Donnez-lui cette permission dans les paramètres du serveur.",
                ephemeral=True
            )
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, attach_files=True, embed_links=True),
            bot_member: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True, manage_channels=True, manage_messages=True)
        }

        # Staff et administrateurs
        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild or role.permissions.manage_channels:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)

        try:
            category = discord.utils.get(guild.categories, name="TICKETS")
            if not category and bot_member.guild_permissions.manage_channels:
                try:
                    category = await guild.create_category("TICKETS")
                except Exception:
                    category = None

            channel = await guild.create_text_channel(
                name=expected_channel_name,
                category=category,
                overwrites=overwrites,
                reason=f"Ticket {cfg['label']} ouvert par {interaction.user}"
            )

            if cfg.get("is_tournament"):
                # Message spécifique tournoi avec template à remplir
                embed = discord.Embed(
                    title="🏆 Inscription Tournoi MK ARENA",
                    description=(
                        f"Bienvenue {interaction.user.mention} !\n\n"
                        "Pour valider l'inscription de votre équipe, **copiez le modèle ci-dessous**, remplissez chaque champ puis envoyez-le dans ce salon."
                    ),
                    color=0xF1C40F
                )
                embed.set_footer(text="Un responsable esport vérifiera la conformité de votre line-up.")
                
                # Envoi du message avec le template prêt à être copié
                await channel.send(
                    content=f"{interaction.user.mention} Voici votre fiche d'inscription :",
                    embed=embed,
                    view=TicketControlView()
                )
                # Envoi du texte brut formaté pour copie facile sur téléphone
                await channel.send(f"```markdown\n{INSCRIPTION_TEMPLATE}\n```")
            else:
                embed = discord.Embed(
                    title=cfg["title"],
                    description=cfg.get("instructions", "Veuillez détailler votre demande."),
                    color=0x5865F2
                )
                embed.set_author(name=str(interaction.user), icon_url=getattr(interaction.user.display_avatar, "url", None))
                embed.set_footer(text="Cliquez sur le bouton ci-dessous pour fermer ce ticket.")

                await channel.send(
                    content=f"{interaction.user.mention} Bienvenue dans votre salon !",
                    embed=embed,
                    view=TicketControlView()
                )

            await interaction.followup.send(
                f"✅ Votre ticket **{cfg['label']}** a été créé : {channel.mention}",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ **Erreur Discord : Permission refusée**. Vérifiez que le rôle du bot est placé suffisamment haut et qu'il possède la permission **Gérer les salons**.",
                ephemeral=True
            )
        except Exception as e:
            logger.error("Erreur création ticket : %s", e)
            await interaction.followup.send(f"❌ Erreur lors de la création du ticket : `{e}`", ephemeral=True)

class TicketPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

class Tickets(commands.Cog):
    """Système de tickets modulaire pour MK ARENA."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _build_panel_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎫 Centre d'Assistance & Inscriptions • MK ARENA",
            description=(
                "Bienvenue sur l'espace d'accueil MK ARENA.\n"
                "Sélectionnez ci-dessous la raison pour laquelle vous souhaitez ouvrir un salon privé avec notre équipe :\n\n"
                "🏆 **Inscription Tournoi** : Formulaire officiel d'inscription pour votre équipe CODM.\n"
                "🛡️ **Recrutement Staff** : Rejoindre notre équipe d'organisation ou de modération.\n"
                "⚔️ **Recrutement Clan** : Candidater pour intégrer l'équipe compétitive MK.\n"
                "❓ **Support & Questions** : Une question, réclamation ou besoin d'assistance."
            ),
            color=0x2B2D31
        )
        embed.set_footer(text="MK ARENA • Système de tickets sécurisé")
        return embed

    @app_commands.command(name="ticket-setup", description="Déployer le panneau de création de tickets.")
    async def slash_ticket_setup(self, interaction: discord.Interaction):
        if not is_authorized(interaction.user):
            await interaction.response.send_message("❌ Vous devez être administrateur ou staff pour utiliser cette commande.", ephemeral=True)
            return

        embed = self._build_panel_embed()
        view = TicketPanelView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ Panneau de tickets déployé avec succès !", ephemeral=True)

    @commands.command(name="ticket-setup")
    async def prefix_ticket_setup(self, ctx: commands.Context):
        if not is_authorized(ctx.author):
            await ctx.send("❌ Vous devez être administrateur ou staff pour utiliser cette commande.")
            return

        embed = self._build_panel_embed()
        view = TicketPanelView()
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="close", description="Fermer le ticket actuel.")
    async def slash_close(self, interaction: discord.Interaction):
        name = interaction.channel.name.lower()
        is_ticket = any(name.startswith(cfg["channel_prefix"]) for cfg in TICKET_TYPES.values()) or "ticket" in name
        if not is_ticket and not is_authorized(interaction.user):
            await interaction.response.send_message("❌ Cette commande ne peut être utilisée que dans un salon de ticket.", ephemeral=True)
            return

        await interaction.response.send_message("🔒 Fermeture du ticket en cours...", ephemeral=False)
        try:
            if isinstance(interaction.channel, discord.TextChannel):
                await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")
        except Exception as e:
            logger.error("Erreur suppression salon: %s", e)

    @commands.command(name="close")
    async def prefix_close(self, ctx: commands.Context):
        name = ctx.channel.name.lower()
        is_ticket = any(name.startswith(cfg["channel_prefix"]) for cfg in TICKET_TYPES.values()) or "ticket" in name
        if not is_ticket and not is_authorized(ctx.author):
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon de ticket.")
            return

        await ctx.send("🔒 Fermeture du ticket en cours...")
        try:
            if isinstance(ctx.channel, discord.TextChannel):
                await ctx.channel.delete(reason=f"Ticket fermé par {ctx.author}")
        except Exception as e:
            logger.error("Erreur suppression salon: %s", e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
