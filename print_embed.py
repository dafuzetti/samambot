import math
import discord
import data_base

def print_players(players, event_obj):
    dt = players
    embed = discord.Embed(
        title="__**Event ID:**__ " + str(event_obj[0])  + "\n__**Event channel:**__ " + event_obj[1] + "\n__**Players:**__", color=0x03f8fc)
    list = dt.values.tolist()
    playersA = ''
    playersB = ''
    for match in list:
        if str(match[1]) == "1":
            playersA = playersA + str(match[0]) + ' '
        if str(match[1]) == "2":
            playersB = playersB + str(match[0]) + ' '
    embed.add_field(name='Team A', value=playersA, inline=False)
    embed.add_field(name='Team B', value=playersB, inline=False)
    return embed


def print_history(ctx_guild, ctx_channel):
    hist = data_base.read_events(ctx_guild, ctx_channel)
    embed = discord.Embed(title="__**Events**__", color=0x03f8fc)
    count = 0
    dates = ''
    active = ''
    for draft in hist:
        count = count + 1
        if draft[5] is not None:
            dates = dates + ' ID: ' + str(draft[0]) + ' - ' + str(
                draft[2])[6:] + '/' + str(draft[2])[4:~1] + '/' + str(
                draft[2])[0:~3] + ' (' + str(draft[7]) + ') ' + '\n'
        else:
            active = active + ' ID: ' + str(draft[0]) + ' - ' + str(
                draft[2])[6:] + '/' + str(draft[2])[4:~1] + '/' + str(
                draft[2])[0:~3] + ' (' + str(draft[7]) + ') ' + draft[6] + '\n'
    embed.add_field(name='History', value=dates, inline=False)
    embed.add_field(name='Active', value=active, inline=False)
    return embed



def print_event(ctx_guild, ctx_channel, event=None, matches=None, event_content=None, players=None):
    embed = discord.Embed(title="__**No event**__", color=0x03f8fc)
    event_id = event
    if (event_id is None):
        event_id = data_base.find_event(ctx_guild, ctx_channel)
    if event_id is not None:
        matches = data_base.read_matches(ctx_guild, ctx_channel, event_id)
        event_data = data_base.read_event(ctx_guild, ctx_channel, event_id)
        if len(matches) > 0:
            embed = print_event_started(matches, event_data)
        else:
            players = data_base.read_players(ctx_guild, ctx_channel, event_id)
            embed = print_players(players, event_data)
    else:
        embed = print_history(ctx_guild, ctx_channel)
    return embed


def print_event_started(dt, event_obj):
    list = dt.values.tolist()
    str_title = "__**Event ID:**__ " + str(event_obj[0])  + "\n__**Event channel:**__ " + event_obj[1]
    embed = discord.Embed(title=str_title, color=0x03f8fc)
    count = len(list)
    matches = ''
    playersA = ''
    playersB = ''
    pos = 0
    winA = 0
    winB = 0
    nrp = math.sqrt(count)
    toadd = 1

    for match in list:
        pos = pos + 1
        if str(match[1]) == '2':
            winA = winA + 1
        if str(match[3]) == '2':
            winB = winB + 1
        if pos == toadd:
            playersA = playersA + match[0]
            playersB = playersB + match[2]
            toadd = toadd + nrp + 1
        if match[1] == match[3] and match[3] == 0:
            matches = matches + str(match[0]) + \
                ' - ' + str(match[2]) + '\n'
        else:
            matches = matches + str(match[0]) + ' ' + str(match[1]) + \
                '-' + str(match[3]) + ' ' + str(match[2]) + '\n'

    emjA = ''
    emjB = ''
    if str(event_obj[4]) == '2':
        emjA = ':skull:'
        emjB = ':trophy:'
    elif str(event_obj[4]) == '1':
        emjA = ':trophy:'
        emjB = ':skull:'
    elif str(event_obj[4]) == '0':
        emjA = '🍕'
        emjB = '🍕'

    embed.add_field(name='Team A ' + str(emjA),
                    value=f'Players: {playersA}\nWin: {winA}', inline=False)
    embed.add_field(name='Team B ' + str(emjB),
                    value=f'Players: {playersB}\nWin: {winB}', inline=False)
    embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                    value=matches, inline=False)
    return embed