from __future__ import annotations
import discord

CATEGORIES = [
    ("Accueil", "accueil", "🏠", "Vue d'ensemble et état général du serveur."),
    ("Arrivées & départs", "welcome_leave", "👋", "Messages de bienvenue, d'au revoir et salons associés."),
    ("Rôles automatiques", "autorole", "🏷️", "Attribution automatique de rôles aux nouveaux membres."),
    ("Rôles sécurisés", "secure_roles", "🛡️", "Protection et verrouillage des rôles sensibles."),
    ("Niveaux", "levels", "📈", "Système d'expérience, niveaux et récompenses de rôle."),
    ("Économie", "economy", "💰", "Monnaie virtuelle, daily, weekly, travail et boutique."),
    ("Modération", "moderation", "🔨", "Filtres AutoMod, anti-liens, anti-spam et sanctions automatiques."),
    ("Captcha", "captcha", "🔒", "Vérification anti-bot obligatoire à l'arrivée."),
    ("Anniversaires", "birthdays", "🎂", "Souhaits automatiques des anniversaires des membres."),
    ("Notifications sociales", "social_notifications", "📢", "Alertes YouTube, Twitch, TikTok et réseaux sociaux."),
    ("Rôles-Réactions", "reaction_roles", "🔘", "Choix de rôles via boutons ou réactions."),
    ("Suggestions", "suggestions", "💡", "Boîte à idées et votes communautaires."),
    ("Signalements", "reports", "🚨", "Signalement confidentiel des abus au staff."),
    ("Tickets", "tickets", "🎟️", "Système de support privé avec salons temporaires."),
    ("Salons de statistiques", "stat_channels", "📊", "Compteurs de membres, vocaux et bots en temps réel."),
    ("Réactions de mots", "word_reactions", "👀", "Réactions automatiques d'émojis sur mots clés."),
    ("Commandes personnalisées", "custom_commands", "🪄", "Déclencheurs de texte et réponses sur mesure."),
    ("Snippets", "snippets", "💬", "Réponses préenregistrées rapides pour le staff."),
    ("Messages récurrents", "recurring_messages", "⏰", "Messages programmés et annonces périodiques."),
    ("Logs", "logs", "🗃️", "Journalisation complète des actions et modérations."),
    ("Starboards", "starboards", "⭐", "Tableau d'honneur des messages les plus réagi."),
    ("Route de l'Infini", "infinity_road", "🔢", "Mini-jeu de progression et défis communautaires.")
]

class ConfigCategorySelect(discord.ui.Select):
    def __init__(self, db, guild_id: int):
        options = [
            discord.SelectOption(
                label=label,
                value=val,
                emoji=emoji,
                description=desc[:100]
            )
            for label, val, emoji, desc in CATEGORIES
        ]
        super().__init__(
            placeholder="Choisissez une catégorie de commandes...",
            min_values=1,
            max_values=1,
            options=options
        )
        self.db = db
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        cat_info = next((c for c in CATEGORIES if c[1] == chosen), None)
        label = cat_info[0] if cat_info else chosen
        emoji = cat_info[2] if cat_info else "⚙️"
        desc = cat_info[3] if cat_info else "Configuration du module"

        embed = discord.Embed(
            title=f"{emoji} Configuration • {label}",
            description=f"**Description :** {desc}

*Statut du module :* 🟢 **Actif**

Vous pouvez ajuster les paramètres ci-dessous ou utiliser le dashboard web.",
            color=0x5865F2
        )
        embed.set_footer(text="Configuration style DraftBot • Aperture MK Arena")
        await interaction.response.edit_message(embed=embed, view=self.view)

class ConfigView(discord.ui.View):
    def __init__(self, db, guild_id: int):
        super().__init__(timeout=300)
        self.add_item(ConfigCategorySelect(db, guild_id))
