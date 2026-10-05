import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from datetime import timedelta

import discord
from discord import app_commands
from memory.database import Database
from features.leveling import LevelingManager
from security.antiraid import AntiRaidManager
from security.automod import AutoModManager
from commands.tickets import TicketManager
from commands.staff import StaffCommands
from memory.knowledge import KnowledgeManager


@pytest.fixture
def test_db():
    db = Database(":memory:")
    db.initialize()
    return db


def create_mock_member(user_id=1001, name="AdminUser", is_admin=True, is_owner=True):
    member = MagicMock(spec=discord.Member)
    member.id = user_id
    member.name = name
    member.display_name = name
    member.mention = f"<@{user_id}>"
    member.bot = False
    member.guild_permissions = MagicMock()
    member.guild_permissions.administrator = is_admin
    member.guild_permissions.manage_guild = is_admin
    member.display_avatar = MagicMock()
    member.display_avatar.url = "https://example.com/avatar.png"
    member.timeout = AsyncMock()
    return member


def create_mock_guild(guild_id=12345):
    guild = MagicMock(spec=discord.Guild)
    guild.id = guild_id
    guild.name = "MK Arena Test Server"
    guild.owner = create_mock_member(9999, "ServerOwner", is_admin=True, is_owner=True)
    guild.ban = AsyncMock()
    guild.kick = AsyncMock()
    guild.get_member = MagicMock(return_value=None)
    guild.default_role = MagicMock(spec=discord.Role)
    guild.roles = []
    guild.categories = []
    return guild


def create_mock_channel(channel_id=5555, name="general"):
    channel = MagicMock(spec=discord.TextChannel)
    channel.id = channel_id
    channel.name = name
    channel.send = AsyncMock()
    channel.purge = AsyncMock(return_value=[MagicMock(), MagicMock()])
    channel.set_permissions = AsyncMock()
    channel.delete = AsyncMock()
    channel.overwrites_for = MagicMock(return_value=MagicMock())
    return channel


def create_mock_interaction(user, guild, channel):
    interaction = MagicMock(spec=discord.Interaction)
    interaction.user = user
    interaction.guild = guild
    interaction.guild_id = guild.id
    interaction.channel = channel
    interaction.response = MagicMock()
    interaction.response.send_message = AsyncMock()
    interaction.response.defer = AsyncMock()
    interaction.followup = MagicMock()
    interaction.followup.send = AsyncMock()
    return interaction


def make_client(test_db):
    from discord_bot.client import NovaClient
    settings = MagicMock()
    settings.context_ttl_minutes = 30
    settings.max_context_messages = 20
    client = NovaClient(settings=settings, db=test_db)
    client._register_commands()
    return client


@pytest.mark.asyncio
async def test_slash_panel_cmd(test_db):
    client = make_client(test_db)
    cmd = client.tree.get_command("panel")
    assert cmd is not None

    admin = create_mock_member(is_admin=True)
    guild = create_mock_guild()
    channel = create_mock_channel()
    interaction = create_mock_interaction(admin, guild, channel)

    await cmd.callback(interaction)
    assert interaction.response.send_message.called
    kwargs = interaction.response.send_message.call_args[1]
    assert kwargs.get("ephemeral") is True
    assert "embed" in kwargs


@pytest.mark.asyncio
async def test_slash_warn_warnings_and_clearwarns(test_db):
    client = make_client(test_db)

    admin = create_mock_member(1001, "Admin", is_admin=True)
    target = create_mock_member(2002, "TargetUser", is_admin=False)
    guild = create_mock_guild()
    channel = create_mock_channel()
    interaction = create_mock_interaction(admin, guild, channel)

    warn_cmd = client.tree.get_command("warn")
    warnings_cmd = client.tree.get_command("warnings")
    clearwarns_cmd = client.tree.get_command("clearwarns")

    # Warn 1
    await warn_cmd.callback(interaction, membre=target, raison="Trolling")
    assert interaction.response.send_message.called
    warns = test_db.get_warns(guild.id, target.id)
    assert len(warns) == 1
    assert warns[0]["reason"] == "Trolling"

    # Warnings view
    inter_view = create_mock_interaction(admin, guild, channel)
    await warnings_cmd.callback(inter_view, membre=target)
    assert inter_view.response.send_message.called

    # Clear warns
    inter_clear = create_mock_interaction(admin, guild, channel)
    await clearwarns_cmd.callback(inter_clear, membre=target)
    assert len(test_db.get_warns(guild.id, target.id)) == 0


@pytest.mark.asyncio
async def test_slash_rank_and_leaderboard(test_db):
    client = make_client(test_db)

    user = create_mock_member(3003, "Gamer", is_admin=False)
    guild = create_mock_guild()
    channel = create_mock_channel()
    interaction = create_mock_interaction(user, guild, channel)

    # Add XP
    test_db.add_xp(guild.id, user.id, amount=100)

    rank_cmd = client.tree.get_command("rank")
    await rank_cmd.callback(interaction, membre=user)
    assert interaction.response.send_message.called

    leaderboard_cmd = client.tree.get_command("leaderboard")
    inter_lb = create_mock_interaction(user, guild, channel)
    await leaderboard_cmd.callback(inter_lb)
    assert inter_lb.response.send_message.called


@pytest.mark.asyncio
async def test_slash_moderation_ban_kick_timeout_clear(test_db):
    client = make_client(test_db)

    admin = create_mock_member(1001, "Admin", is_admin=True)
    target = create_mock_member(4004, "BadActor", is_admin=False)
    guild = create_mock_guild()
    channel = create_mock_channel()

    # Ban
    inter_ban = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("ban").callback(inter_ban, membre=target, raison="Griefing")
    assert guild.ban.called

    # Kick
    inter_kick = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("kick").callback(inter_kick, membre=target, raison="Regles")
    assert guild.kick.called

    # Timeout
    inter_timeout = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("timeout").callback(inter_timeout, membre=target, minutes=15, raison="Spam")
    assert target.timeout.called

    # Clear
    inter_clear = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("clear").callback(inter_clear, nombre=5)
    assert channel.purge.called


@pytest.mark.asyncio
async def test_slash_antiraid_and_lockdown(test_db):
    client = make_client(test_db)

    admin = create_mock_member(1001, "Admin", is_admin=True)
    guild = create_mock_guild()
    channel = create_mock_channel()

    # Antiraid ON
    choice_on = app_commands.Choice(name="Activer", value="on")
    inter_ar = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("anti-raid").callback(inter_ar, etat=choice_on)
    assert client.antiraid.is_enabled(guild.id) is True

    # Lockdown LOCK
    choice_lock = app_commands.Choice(name="Activer Confinement", value="lock")
    inter_ld = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("lockdown").callback(inter_ld, action=choice_lock)
    assert inter_ld.followup.send.called


@pytest.mark.asyncio
async def test_tickets_setup_and_close(test_db):
    client = make_client(test_db)

    admin = create_mock_member(1001, "Admin", is_admin=True)
    guild = create_mock_guild()
    channel = create_mock_channel(name="ticket-user-123")

    # Setup tickets
    inter_setup = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("setup-tickets").callback(inter_setup)
    assert channel.send.called

    # Close ticket
    inter_close = create_mock_interaction(admin, guild, channel)
    await client.tree.get_command("ticket-close").callback(inter_close)
    assert channel.delete.called


@pytest.mark.asyncio
async def test_natural_language_triggers_and_execution(test_db):
    client = make_client(test_db)

    admin = create_mock_member(1001, "Admin", is_admin=True)
    guild = create_mock_guild()
    channel = create_mock_channel()

    # Add trigger via natural chat
    msg = MagicMock(spec=discord.Message)
    msg.author = admin
    msg.guild = guild
    msg.channel = channel
    msg.reference = None
    msg.content = "Nova si quelqu'un fait !staff donne lui Voici le questionnaire staff https://forms.gle/abc"
    msg.reply = AsyncMock()

    await client.on_message(msg)
    assert msg.reply.called
    assert "Règle enregistrée avec succès" in msg.reply.call_args[0][0]

    # Test trigger invocation by regular member
    user = create_mock_member(2002, "NormalUser", is_admin=False)
    user_msg = MagicMock(spec=discord.Message)
    user_msg.author = user
    user_msg.guild = guild
    user_msg.channel = channel
    user_msg.reference = None
    user_msg.content = "!staff"

    await client.on_message(user_msg)
    assert channel.send.called
    assert "Voici le questionnaire staff" in channel.send.call_args[0][0]

    # List triggers
    list_msg = MagicMock(spec=discord.Message)
    list_msg.author = admin
    list_msg.guild = guild
    list_msg.channel = channel
    list_msg.reference = None
    list_msg.content = "Nova liste les règles"
    list_msg.reply = AsyncMock()

    await client.on_message(list_msg)
    assert list_msg.reply.called
    assert "!staff" in list_msg.reply.call_args[0][0]

    # Delete trigger
    del_msg = MagicMock(spec=discord.Message)
    del_msg.author = admin
    del_msg.guild = guild
    del_msg.channel = channel
    del_msg.reference = None
    del_msg.content = "Nova supprime la règle !staff"
    del_msg.reply = AsyncMock()

    await client.on_message(del_msg)
    assert del_msg.reply.called
    assert "supprimée" in del_msg.reply.call_args[0][0]
