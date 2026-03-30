import asyncio

import discord
import db.db_event as db_event
import re

from classes.Players import Players

def define_team(ctx_guild, ctx_channel, team_id: int, p1: discord.User, p2: discord.User = None,
                p3: discord.User = None, p4: discord.User = None):
    list = []
    list.append(p1)
    list.append(p2)
    list.append(p3)
    list.append(p4)
    db_event.new_team(ctx_guild, ctx_channel, list, team_id)

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

def resultado(ctx_guild, ctx_channel, player_w, player_l, losses):
    db_event.update_matches(ctx_guild, ctx_channel, player_w, player_l, losses)

