import discord
from discord import app_commands
from discord.ext import commands
from decouple import config

from views.CreatingEventView import CreatingEventView
from views.RunningEventView import RunningEventView
from classes.Event import Event
import db.db_event as db_event
import functions

TOKEN = config("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Store event per channel
events = {}

@tree.command(name="new_event", description="Start an event")
async def new_event(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await create_event(interaction)

    try:
        await event_message(interaction)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
        return


async def create_event(interaction: discord.Interaction, player: discord.Member = None, teamA: bool = True):
    view_event = events.get(interaction.channel.id)

    if view_event is None:
        event_data = db_event.find_event(interaction.guild.id, interaction.channel.id)
        if event_data is not None:
            view_event = RunningEventView(
                interaction=interaction,
                events=events, 
                event=event_data,
            )
        else:
            view_event = CreatingEventView(interaction=interaction, events=events)
            view_event.add_player(player, team_a=teamA)
        events[interaction.channel.id] = view_event
    return view_event


async def event_message(interaction: discord.Interaction):
    view_event = events.get(interaction.channel.id)
    if view_event is not None:
        if view_event.message_id is not None:
            try:
                message = await interaction.channel.fetch_message(view_event.message_id)
            except Exception as e:
                view_event.message_id = None
        if view_event.message_id is None:
            try:
                message = await interaction.channel.send(
                    embed=view_event.build_embed(),
                    view=view_event
                )
                view_event.message_id = message.id
            except Exception as e:
                await interaction.followup.send(f"Error: {e}", ephemeral=True)
        else:
            await message.edit(embed=view_event.build_embed(), view=view_event)
        await interaction.followup.send("See event message: " \
            f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{view_event.message_id}", 
            ephemeral=True)
        events[interaction.channel.id] = view_event

@tree.command(name="add_player", description="Add player to Team A")
@app_commands.describe(user="Add player to a team")
async def add_player(interaction: discord.Interaction, user: discord.Member, team: str = "A"):
    await interaction.response.defer(ephemeral=True)
    team_a = False
    if team.uppper() == "A":
        team_a = True

    view = events.get(interaction.channel.id)
    if not view:
        view = await create_event(interaction, user, team_a)

    view.add_player(user, team_a=team_a)
    view.update_buttons()

    try:
        await event_message(interaction)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)
        return

    team_name = "Team A" if team_a else "Team B"
    await interaction.followup.send(
        f"{user.mention} added to **{team_name}**",
        ephemeral=True
    )

@ tree.command(name='clean', description='If event are showing wrong info, use this command to clean the channel and reset the event.')
async def clean(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    events.clear()
    await interaction.followup.send("Use /new_event in the same channel the events were running", ephemeral=True)

@ tree.command(name='history', description='Event list or history details for specific events.')
async def history(interaction: discord.Interaction, event_id: int = None):
    await interaction.response.defer(ephemeral=True)
    if event_id is None:
        await interaction.followup.send("Full history not available yet.", ephemeral=True)
        #embed = functions.print_history(interaction)
    else:
        event_data = db_event.read_event(interaction.guild.id, interaction.channel.id, event_id)
        if event_data is None:
            await interaction.followup.send("Event not found.", ephemeral=True)
        else:
            if event_data.victory is not None:
                view_event = RunningEventView(
                        interaction=interaction,
                        event=event_data,
                    )
                await interaction.followup.send(embed=view_event.build_embed(), view=view_event, ephemeral=True)
            else:
                await interaction.followup.send("Event still active.", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # allow commands (optional depending on setup)
    if message.content.startswith("/"):
        return

    if message.channel.id in events:
        await message.delete()

# save match muito lento
# refazer queries (blocar edicao de eventos encerrados)
# await asyncio.to_thread(data_base.some_function, ...)

# comandos de estatistica 
# move here

# contador de eventos por guild ID?
# remove all team A/B e criar eventos individuais
# to no play 
# criar novas temporadas 
# nome/id do event? comandos de resultado? Deletar evento? 
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)