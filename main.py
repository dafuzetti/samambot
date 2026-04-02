import discord
from discord.ext import commands
from decouple import config

from views.CreatingEventView import CreatingEventView
from views.RunningEventView import RunningEventView
import db.db_event as db_event
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
    if view is not None:
        view_event = view
    else:
        view_event = State.get_eventView(interaction.channel.id)
    
    if view_event is None:
        return None

    if view_event.message is not None:
        try:
            await view_event.message.edit(embed=view_event.build_embed(), view=view_event)
        except:
            view_event.message = None

    if view_event.message is None:
        view_event.message = await interaction.channel.send(embed=view_event.build_embed(), view=view_event)
    
    return f"See event message: https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{view_event.message.id}"

async def save_result(interaction: discord.Interaction, winner: discord.User, loser: discord.User, gameloss: int = 0):
    view_event = State.get_eventView(interaction.channel.id)
    msg, event_data = db_event.update_matches_from_channel(interaction.guild.id, interaction.channel.id, winner.mention, loser.mention, gameloss) 

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

@ tree.command(name='clean', description='If event are showing wrong info, use this command to clean the channel and reset the event.')
async def clean(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    State.clear_events()
    await interaction.followup.send("Use /event in the same channel the events were running", ephemeral=True)

@tree.command(name="event", description="Start an event")
async def event(interaction: discord.Interaction):
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

@ tree.command(name='history', description='Event list or history details for specific events.')
async def history(interaction: discord.Interaction, event_id: int = None):
    await interaction.response.defer(ephemeral=True)
    msg = ""
    view_hist = None
    if event_id is None:
        msg = "Full history not available yet. Use /history <event>"
        #view_hist = functions.print_history(interaction)
    else:
        event_data = db_event.read_event(interaction.guild.id, interaction.channel.id, event_id)
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
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)

# comandos de estatistica 
# move here

# move read_events para dentro das comm
# blocar edicao de eventos encerrados
# contador de eventos por guild ID?
# remove all team A/B e criar eventos individuais
# to no play 
# criar novas temporadas 
# nome/id do event? comandos de resultado? Deletar evento? 
# remover classes.propriety access
# remover teams a and b from creatingevent and add a list of players 
# mover print para dentro das classes
# match using player objc, return team from players at query
# populaet name at players 