# Security layer placeholder for future validation logic.

import discord


def can_execute_action(member: discord.Member | None, required_permission: str | None = None) -> bool:
    if member is None:
        return False
    if member.guild.owner_id == member.id:
        return True
    if required_permission is None:
        return member.guild_permissions.administrator or member.guild_permissions.manage_guild

    permissions = {
        "administrator": member.guild_permissions.administrator,
        "manage_guild": member.guild_permissions.manage_guild,
        "manage_channels": member.guild_permissions.manage_channels,
    }
    return bool(permissions.get(required_permission, False))


def validate_staff_action(member: discord.Member | None) -> bool:
    return can_execute_action(member, "administrator") or can_execute_action(member, "manage_guild")
