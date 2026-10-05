import discord

def can_manage_nova(member: discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False
    perms = member.guild_permissions
    return (
        perms.administrator
        or perms.manage_guild
        or perms.manage_roles
        or (member.guild is not None and member.guild.owner_id == member.id)
    )

def has_staff_access(member: discord.Member | None) -> bool:
    if not member or not isinstance(member, discord.Member):
        return False
    return can_manage_nova(member)
