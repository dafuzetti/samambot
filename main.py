import discord
from discord.ext import commands
from decouple import config

from views.CreatingEventView import CreatingEventView
from views.RunningEventView import RunningEventView
from views.MyMatchesView import MyMatchesView
import db.db_event as db_event
import db.db_reports as db_reports
import functions
from classes.State import State

TOKEN = config("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

async def create_event(interaction: discord.Interaction):
    view_event = State.get_eventView(interaction.channel.id)
    msg = "Event found and loaded."
    if view_event is None:
        try:
            event_data = db_event.find_event(interaction.guild.id, interaction.channel.id)
            if event_data is not None:
                view_event = RunningEventView(interaction=interaction, event=event_data)
            else:
                msg = "Event created."
                view_event = CreatingEventView()
                functions.channelnameopen(interaction.channel, "NEW")
        except Exception as e:
            print(f"Error creating event: {e}")
        State.set_eventView(interaction.channel.id, view_event)
    return msg, view_event

async def event_message(interaction: discord.Interaction, view=None):
    channel = None
    view_event = view
    if interaction is not None:
        channel = interaction.channel
    if channel is None:
        try:
            channel = bot.get_channel(view_event.event.channel_id)
        except(Exception) as e:
            print(e)
    if channel is None:
        return None
        
    if view_event is None and channel is not None: 
        view_event = State.get_eventView(channel.id)
    if view_event is None:
        return None

    if channel and hasattr(channel, 'category') and channel.category:
        view_event.season_name = channel.category.name

    if view_event.message is None:
        try:
            if view_event.event.message_id is not None:
                channel = bot.get_channel(view_event.event.channel_id)
                view_event.message = await channel.fetch_message(view_event.event.message_id)
        except:
            view_event.message = None

    if view_event.message is not None:
        try:
            await view_event.message.edit(embed=view_event.build_embed(), view=view_event)
        except:
            view_event.message = None

    if view_event.message is None:
        view_event.message = await channel.send(embed=view_event.build_embed(), view=view_event)
        if view_event and hasattr(view_event, "event") and view_event.event:
            if hasattr(view_event.event, "event_id"):
                db_event.update_event_message_id(view_event.event.event_id, view_event.message.id)
        
    State.set_eventView(channel.id, view_event)

    return f"See event message: https://discord.com/channels/{channel.guild.id}/{channel.id}/{view_event.message.id}"


async def save_result(interaction: discord.Interaction, winner: discord.User, loser: discord.User, gameloss: int = 0):
    view_event = State.get_eventView(interaction.channel.id)
    msg, event_data = db_event.update_matches_from_channel(interaction.guild.id, interaction.channel.id, interaction.user.mention, winner.mention, loser.mention, gameloss) 

    if event_data is not None:
        if isinstance(view_event, RunningEventView):
            view_event.event.set_matches(event_data.matches)
        else:
            view_event = RunningEventView(interaction=interaction, event=event_data)
            State.set_eventView(interaction.channel.id, view_event)
    msg = return_message(msg, await event_message(interaction, view_event))
    return msg

def return_message(base_msg: str="", followup_msg=None):
    if followup_msg:
        return f"{base_msg}\n{followup_msg}"
    return base_msg

@tree.command(name="event", description="Start an event")
async def event(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    msg, view = await create_event(interaction)
    await interaction.followup.send(return_message(msg, await event_message(interaction, view)), ephemeral=True)

@tree.context_menu(name="New Event")
async def event_context(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.defer(ephemeral=True)
    msg, view = await create_event(interaction)
    await interaction.followup.send(return_message(msg, await event_message(interaction, view)), ephemeral=True)

@tree.command(name="add_player", description="Add player to an event.")
async def add_player(interaction: discord.Interaction, user: discord.Member, team: str = "A"):
    msg = ""
    await interaction.response.defer(ephemeral=True)
    team_a = team.upper() == "A"
    view_event = State.get_eventView(interaction.channel.id)
    if view_event is not None:
        if isinstance(view_event, CreatingEventView):
            view_event.add_player(user, team_a=team_a)
            await view_event.update_message()
            msg = return_message(f"{user.mention} added to event.", await event_message(interaction, view_event))
        else:
            msg = "Event already started. Can't add players."
    else:
        msg = "No event found. Use /event to create a new event."
    await interaction.followup.send(msg, ephemeral=True)

@tree.command(name='win', description='Report the result of a match.')
async def win(interaction: discord.Interaction, loser: discord.User, gameloss: int = 0):
    await interaction.response.defer(ephemeral=True) 
    await interaction.followup.send(await save_result(interaction, interaction.user, loser, gameloss), ephemeral=True)

@tree.command(name='lose', description='Report the result of a match.')
async def lose(interaction: discord.Interaction, winner: discord.User, gameloss: int = 0):
    await interaction.response.defer(ephemeral=True) 
    await interaction.followup.send(await save_result(interaction, winner, interaction.user, gameloss), ephemeral=True)

@tree.command(name='result', description='Report the result of a match.')
async def result(interaction: discord.Interaction, winner: discord.User, loser: discord.User, gameloss: int = 0):
    await interaction.response.defer(ephemeral=True) 
    await interaction.followup.send(await save_result(interaction, winner, loser, gameloss), ephemeral=True)

@ tree.command(name='games', description='Return missing matches from all events.')
async def clean(interaction: discord.Interaction, user: discord.Member = None):
    await interaction.response.defer(ephemeral=True)
    view = MyMatchesView(db_reports.open_matches(interaction.guild.id, interaction.channel.id, 
                                                 user.mention if user else interaction.user.mention))
    embed_built = await view.build_embed(interaction, user if user else interaction.user)
    await interaction.followup.send(embed=embed_built, ephemeral=True)

@ tree.command(name='history', description='Event list or history details for specific events.')
async def history(interaction: discord.Interaction, event_id: int = None):
    await interaction.response.defer(ephemeral=True)
    msg = ""
    view_hist = None
    if event_id is None:
        msg = "Full history not available yet. Use /history <event>"
        #view_hist = functions.print_history(interaction)
    else:
        event_data = db_event.read_event(interaction.guild.id, interaction.channel.id, event_id, user=interaction.user.mention, log=True)
        if event_data is None:
            msg = "Event not found."
        else:
            if event_data.victory is not None:
                view_hist = RunningEventView(interaction=interaction,event=event_data)
            else:
                msg = "Event still active."

    if view_hist is not None:
        await interaction.followup.send(embed=view_hist.build_embed(), view=view_hist, ephemeral=True)
    else:
        await interaction.followup.send(msg, ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # allow commands (optional depending on setup)
    if message.content.startswith("/"):
        return

    if State.is_event_running(message.channel.id):
        await message.delete()

@bot.event
async def on_ready():
    await tree.sync()

    active_events = db_event.get_all_active_events()

    for event in active_events:
        view = RunningEventView(event=event)
        await event_message(interaction=None, view=view)
        bot.add_view(view)

    print(f"Logged in as {bot.user}")

bot.run(TOKEN)

# add player as object for creating event and matches
# remover teams a and b from creatingevent and add a list of players 
# match using player objc, return team from players at query
# populaet name at players 
# handle player name 
# remove all team A/B e criar eventos individuais
# user nome no remove player

# creating event: start event adicionar placeholders
# comandos de estatistica 
# public message when event gets closed? when last player reports result to ask for confirmation
# arquivo de fechamento de event 
# move here / liberar para eventos encerrados? bloquear por usuario?
# Block evento sem category?

# blocar edicao de eventos encerrados db
# to no play 
# Guardar nome das seasons?
# close season? 
# season report #1, #2, #3 
# Season type team/individual
# move read_events para dentro das comm
# Deletar evento?  
# remover classes.propriety access
# mover print para dentro das classes