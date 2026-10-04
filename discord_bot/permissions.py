import discord


def can_manage_nova(member: discord.Member, settings=None) -> bool:
    if member.guild_permissions.administrator or member.guild_permissions.manage_guild:
        return True

    # Vérifier rôle admin/staff configuré
    if settings:
        admin_roles = [getattr(settings, "admin_role_id", None), getattr(settings, "staff_role_id", None)]
        user_role_ids = [r.id for r in member.roles]
        if any(rid in user_role_ids for rid in admin_roles if rid):
            return True

    return False
