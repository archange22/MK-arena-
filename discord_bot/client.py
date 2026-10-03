import discord
from discord import app_commands
from ai.engine import NovaEngine
from ai.intent import detect_intent
from memory.database import Database
from memory.conversation import ConversationMemory
from memory.knowledge import KnowledgeManager
from config.permissions import can_manage_nova

class NovaClient(discord.Client):
    def __init__(self, settings, db: Database):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.settings = settings
        self.db = db
        self.tree = app_commands.CommandTree(self)
        self.context = ConversationMemory(db, settings.context_ttl_minutes)
        self.knowledge = KnowledgeManager(db)
        self.engine = NovaEngine(self.knowledge, self.context)
        self.tournament_scanner = None

    async def setup_hook(self):
        self.tree.add_command(self._status_command())
        self.tree.add_command(self._sync_command())
        await self.tree.sync()

    def _status_command(self):
        @app_commands.command(name="nova-status", description="Voir l'état de NOVA.")
        async def status(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
                return
            await interaction.response.send_message(
                f"🟢 NOVA en ligne\n"
                f"Base SQLite : OK\n"
                f"Tournois indexés : {self.db.count_tournaments()}",
                ephemeral=True
            )
        return status

    def _sync_command(self):
        @app_commands.command(name="nova-sync", description="Synchroniser la catégorie TOURNOIS.")
        async def sync(interaction: discord.Interaction):
            if not isinstance(interaction.user, discord.Member) or not can_manage_nova(interaction.user):
                await interaction.response.send_message("Tu n'as pas la permission d'utiliser cette commande.", ephemeral=True)
                return
            if not self.tournament_scanner:
                await interaction.response.send_message("Scanner indisponible.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            count = await self.tournament_scanner.sync()
            await interaction.followup.send(f"Synchronisation terminée : {count} salon(s) de tournoi analysé(s).", ephemeral=True)
        return sync

    async def on_ready(self):
        print(f"Connecté en tant que {self.user} ({self.user.id})")
        if self.tournament_scanner:
            try:
                await self.tournament_scanner.sync()
            except Exception as exc:
                print(f"Synchronisation initiale impossible: {exc}")

    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not self.engine.is_called(message.content):
            return

        content = self.engine.remove_call(message.content)
        if not content.strip():
            await message.channel.send("Oui ? 😎")
            return

        is_staff_instruction = content.strip().startswith('"') and content.strip().endswith('"')
        if is_staff_instruction:
            if not isinstance(message.author, discord.Member) or not can_manage_nova(message.author):
                await message.channel.send("Je peux discuter avec toi, mais tu n'as pas la permission de modifier mes connaissances.")
                return
            content = content.strip()[1:-1].strip()
            if content.lower().startswith(("nova ", "nova:")):
                content = content[4:].lstrip(": ").strip()
            saved = self.knowledge.learn(content, source=f"staff:{message.author.id}", guild_id=message.guild.id)
            await message.channel.send(saved)
            return

        response = self.engine.respond(
            user_id=message.author.id,
            guild_id=message.guild.id,
            text=content,
        )
        self.context.add(message.author.id, "user", content)
        self.context.add(message.author.id, "assistant", response)
        await message.channel.send(response)
