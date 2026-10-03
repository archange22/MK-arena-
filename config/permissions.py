import discord


def can_manage_nova(member: discord.Member) -> bool:
    return (
        member.guild.owner_id == member.id
        or member.guild_permissions.administrator
        or member.guild_permissions.manage_guild
    )


def has_staff_access(member: discord.Member | None) -> bool:
    if not member:
        return False
    return member.guild.owner_id == member.id or member.guild_permissions.administrator or member.guild_permissions.manage_guild
