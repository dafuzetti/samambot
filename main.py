import discord
from discord import app_commands
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
    new_event = "Event found and loaded."
    if view_event is None:
        try:
            event_data = db_event.find_event(interaction.guild.id, interaction.channel.id)
            if event_data is not None:
                view_event = RunningEventView(interaction=interaction, event=event_data,)
            else:
                new_event = "Event created."
                view_event = CreatingEventView()
                functions.channelnameopen(interaction.channel, "NEW")
        except Exception as e:
            print(f"Error creating event: {e}")
        State.set_eventView(interaction.channel.id, view_event)
    return new_event

async def event_message(interaction: discord.Interaction):
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

def return_message(base_msg: str="", followup_msg=None):
    if followup_msg:
        return f"{base_msg}\n{followup_msg}"
    return base_msg

@ tree.command(name='clean', description='If event are showing wrong info, use this command to clean the channel and reset the event.')
async def clean(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    State.clear_events()
    await interaction.followup.send("Use /new_event in the same channel the events were running", ephemeral=True)

@tree.command(name="new_event", description="Start an event")
async def new_event(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    msg = await create_event(interaction)
    await interaction.followup.send(return_message(msg, await event_message(interaction)), ephemeral=True)

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

# refazer queries (blocar edicao de eventos encerrados)
# add player cagado, evento rodando precisa validar 
# add comandos win/lose/result 

# comandos de estatistica 
# move here

# contador de eventos por guild ID?
# remove all team A/B e criar eventos individuais
# to no play 
# criar novas temporadas 
# nome/id do event? comandos de resultado? Deletar evento? 