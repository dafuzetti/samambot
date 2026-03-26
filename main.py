import discord
from discord import app_commands
from discord.ext import commands
from decouple import config

import EventView
import data_base
import functions

TOKEN = config("TOKEN")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Store event per channel
events = {}

@tree.command(name="event", description="Start an event")
async def event(interaction: discord.Interaction):
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
        event_id = data_base.find_event(interaction.guild.id, interaction.channel.id)
        if event_id:
            matches = data_base.read_matches(interaction.guild.id, interaction.channel.id, event_id)
            if len(matches) > 0:
                event_content = data_base.read_event(interaction.guild.id, interaction.channel.id, event_id)
                players = data_base.read_players(interaction.guild.id, interaction.channel.id, event_id)
                view_event = EventView.RunningEventView(interaction=interaction, events=events, event_id=event_id, matches=matches, event_content=event_content, players=players)
                await functions.channelnameopen(interaction.channel, event_id)
        if not view_event:
            view_event = EventView.CreatingEventView(interaction=interaction, events=events)
            view_event.add_player(player, team_a=teamA)
        events[interaction.channel.id] = view_event
    return view_event

async def event_message(interaction: discord.Interaction):
    view_event = events.get(interaction.channel.id)
    if view_event.message_id is not None:
        try:
            message = await interaction.channel.fetch_message(view_event.message_id)
            if message:
                await message.edit(embed=view_event.build_embed(), view=view_event)
                await interaction.followup.send("See event message!", ephemeral=True)
            else:
                view_event.message_id = None
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
    if view_event.message_id is None:
        try:
            message = await interaction.channel.send(
                embed=view_event.build_embed(),
                view=view_event
            )
            view_event.message_id = message.id
            await interaction.followup.send("See event message!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"Error: {e}", ephemeral=True)
    events[interaction.channel.id] = view_event


async def add_player(interaction: discord.Interaction, user: discord.Member, team_a: bool = True):
    await interaction.response.defer(ephemeral=True)

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


@tree.command(name="adda", description="Add player to Team A")
@app_commands.describe(user="User to add")
async def adda(interaction: discord.Interaction, user: discord.Member):
    await add_player(interaction, user, team_a=True)
        

@tree.command(name="addb", description="Add player to Team B")
@app_commands.describe(user="User to add")
async def addb(interaction: discord.Interaction, user: discord.Member):
    await add_player(interaction, user, team_a=False)


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # allow commands (optional depending on setup)
    if message.content.startswith("/"):
        return

    if message.channel.id in events:
        await message.delete()

# admin only para fechar evento
# refazer queries 
# salvar match rsultados
# contador de eventos por guild ID?
# close event ta piscando os botoes apos o click / remover duplo click nos comandos
# comandos de estatistica 
@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)