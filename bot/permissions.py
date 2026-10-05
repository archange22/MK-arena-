def is_authorized(member) -> bool:
    """
    Vérifie si un membre a le droit de gérer le bot :
    - Administrateur (accès total)
    - Gérer le serveur
    - Gérer les rôles
    - Propriétaire du serveur (créateur)
    """
    if member is None:
        return False
    perms = getattr(member, "guild_permissions", None)
    admin = getattr(perms, "administrator", False) if perms else False
    manage_guild = getattr(perms, "manage_guild", False) if perms else False
    manage_roles = getattr(perms, "manage_roles", False) if perms else False
    guild = getattr(member, "guild", None)
    is_owner = (guild is not None and getattr(guild, "owner_id", None) == getattr(member, "id", None))
    return bool(admin or manage_guild or manage_roles or is_owner)
