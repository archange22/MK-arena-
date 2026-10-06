import pytest
from unittest.mock import MagicMock
from bot.permissions import is_authorized
from bot.client import ChachaBot
import config

def test_permissions_admin():
    member = MagicMock()
    member.guild_permissions.administrator = True
    member.guild_permissions.manage_guild = False
    member.guild_permissions.manage_roles = False
    member.guild.owner_id = 999
    member.id = 123
    assert is_authorized(member) is True

def test_permissions_manage_guild():
    member = MagicMock()
    member.guild_permissions.administrator = False
    member.guild_permissions.manage_guild = True
    member.guild_permissions.manage_roles = False
    member.guild.owner_id = 999
    member.id = 123
    assert is_authorized(member) is True

def test_permissions_owner():
    member = MagicMock()
    member.guild_permissions.administrator = False
    member.guild_permissions.manage_guild = False
    member.guild_permissions.manage_roles = False
    member.guild.owner_id = 123
    member.id = 123
    assert is_authorized(member) is True

def test_permissions_regular_user():
    member = MagicMock()
    member.guild_permissions.administrator = False
    member.guild_permissions.manage_guild = False
    member.guild_permissions.manage_roles = False
    member.guild.owner_id = 999
    member.id = 123
    assert is_authorized(member) is False

def test_bot_initialization_and_prefix():
    bot = ChachaBot()
    assert bot is not None
    assert bot.command_prefix == "!"
    assert bot.tree is not None

def test_bot_register_commands():
    bot = ChachaBot()
    bot._register_commands()
    registered_cmds = [cmd.name for cmd in bot.commands]
    assert "ping" in registered_cmds
    assert "aide" in registered_cmds
