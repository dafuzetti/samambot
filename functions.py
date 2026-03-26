import discord
import itertools
import data_base
import re

def define_team(ctx_guild, ctx_channel, team_id: int, p1: discord.User, p2: discord.User = None,
                p3: discord.User = None, p4: discord.User = None):
    list = []
    list.append(p1)
    list.append(p2)
    list.append(p3)
    list.append(p4)
    data_base.new_team(ctx_guild, ctx_channel, list, team_id)


async def channelnameopen(channel, event_id):
    name = channel.name
    newname = name
    if newname.endswith('__'):
        parts = newname.rsplit("__", 1)
        newname = ('_event-' + str(event_id) + '_').join(parts)
    if newname != name:
        try:
            await channel.edit(name=newname)
        except discord:
            return


async def channelnameclose(channel, event_id = None):
    name = channel.name
    newname = name
    pattern = re.compile(r'_event-(\d+)_')
    if bool(pattern.search(newname)):
        newname = newname.rsplit("_", 2)[0] + '__'
    if newname != name:
        try:
            await channel.edit(name=newname)
        except discord:
            return


def resultado(ctx_guild, ctx_channel, player_w, player_l, losses):
    data_base.update_matches(ctx_guild, ctx_channel, player_w, player_l, losses)


def start(ctx_guild, ctx_channel, event_id, players):
    counts = players['team'].value_counts()
    if len(players) % 2 == 0 and counts.nunique() == 1 and len(counts) == 2:
        TeamA = players[players['team'] == 1]
        TeamB = players.drop(TeamA.index)
        Mlist = itertools.product(
            TeamA['player'].tolist(), TeamB['player'].tolist())
        data_base.save_matches(ctx_guild, ctx_channel, Mlist, event_id)
    return event_id
