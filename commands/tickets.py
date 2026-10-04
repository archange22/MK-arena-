from __future__ import annotations

import discord


class TicketManager:
    def __init__(self, category_name: str = "TICKETS-SUPPORT"):
        self.category_name = category_name

    async def get_or_create_category(self, guild: discord.Guild) -> discord.CategoryChannel:
        for cat in guild.categories:
            if cat.name.upper() == self.category_name.upper():
                return cat
        return await guild.create_category(self.category_name)

    async def create_ticket(self, guild: discord.Guild, member: discord.Member, topic: str = "Assistance générale") -> discord.TextChannel:
        category = await self.get_or_create_category(guild)
        clean_name = f"ticket-{member.name.lower()[:15]}-{member.discriminator if hasattr(member, 'discriminator') and member.discriminator != '0' else member.id % 1000}"

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True, embed_links=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
        }

        # Accès pour le propriétaire et les administrateurs
        if guild.owner:
            overwrites[guild.owner] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=clean_name,
            category=category,
            overwrites=overwrites,
            topic=f"Ticket ouvert par {member.mention} | Motif : {topic}"
        )

        embed = discord.Embed(
            title="🎫 Protocole d'Assistance - Aperture MK Arena",
            description=(
                f"Bienvenue {member.mention}. Votre requête a été transmise aux superviseurs.\n\n"
                f"**Motif :** {topic}\n"
                f"**Consigne GLaDOS :** *Veuillez exposer votre problème calmement sans gaspiller de bande passante.*"
            ),
            color=0x3498DB
        )
        embed.set_footer(text="Utilisez /ticket-close pour clore ce canal.")
        await channel.send(embed=embed)
        return channel

    async def close_ticket(self, channel: discord.TextChannel, closed_by: discord.Member) -> bool:
        if not channel.name.startswith("ticket-"):
            return False
        await channel.send(f"🔒 Ticket fermé par {closed_by.mention}. Suppression du salon d'ici quelques secondes...")
        await channel.delete(reason=f"Fermé par {closed_by}")
        return True
