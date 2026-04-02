import asyncio

import discord

def channelnameopen(channel, event_id):
    if '-_' in channel.name:
        base = get_base_channel_name(channel)
        newname = f"{base}-_{event_id}_"
    update_channelname(channel, newname)

def channelnameclose(channel):
    if '-_' in channel.name:
        base = get_base_channel_name(channel)
        newname = f"{base}-__"
    update_channelname(channel, newname)

def get_base_channel_name(channel):
    if '-_' in channel.name:
        return channel.name.rsplit('-_', 1)[0]
    return channel.name

def update_channelname(channel, name):
    if channel.name != name:
        asyncio.create_task(channel.edit(name=name))

import re

async def get_player_name(interaction, player: str) -> str:
    match = re.search(r"<@!?(\d+)>", player)
    if not match:
        return player  # fallback (already a name)

    user_id = int(match.group(1))

    member = interaction.guild.get_member(user_id)
    if not member:
        try:
            member = await interaction.guild.fetch_member(user_id)
        except:
            return player

    return member.display_name