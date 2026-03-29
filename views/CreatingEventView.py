from asyncio import events

import discord
import discord.ui
import pandas as pd

from views.RunningEventView import RunningEventView
from classes.Event import Event
from classes.Players import Players
import db.db_event as db_event
import functions

class CreatingEventView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, events=None):
        super().__init__(timeout=None)
        self.team_a = set()
        self.team_b = set()
        self.message_id = None
        self.events = events
        self.processing = False  # Flag to prevent multiple simultaneous starts
        self.num_players = [4,6,8]  # Allowed player counts for starting the event

    def total_players(self):
        return len(self.team_a) + len(self.team_b)

    def add_player(self, player: discord.User, team_a: bool = True):
        if player is None:
            return
        if team_a:
            if(len(self.team_a)< 4):  # Assuming a maximum of 4 players per team
                self.team_b.discard(player.mention)
                self.team_a.add(player.mention)
        else:
            if(len(self.team_b) < 4):  # Assuming a maximum of 4 players per team
                self.team_a.discard(player.mention)
                self.team_b.add(player.mention)

    def validate_teams(self):
        if self.total_players() in self.num_players and len(self.team_a) == len(self.team_b):
            return False
        return True

    def remove_player(self, player: discord.User):
        self.team_a.discard(player.mention)
        self.team_b.discard(player.mention)

    def update_buttons(self):
        total = self.total_players()

        for item in self.children:
            if item.custom_id == "start":
                item.disabled = self.validate_teams()

            if item.custom_id == "team_a":
                item.label = f"Join Team A ({len(self.team_a)})"

            if item.custom_id == "team_b":
                item.label = f"Join Team B ({len(self.team_b)})"

    def build_embed(self):
        embed = discord.Embed(title="New Event Lobby")

        team_a = "\n".join(u for u in self.team_a) or "—"
        team_b = "\n".join(u for u in self.team_b) or "—"

        embed.add_field(name="Team A", value=team_a, inline=True)
        embed.add_field(name="Team B", value=team_b, inline=True)
        embed.set_footer(text=f"Total players: {self.total_players()}")

        return embed

    async def update_message(self, interaction: discord.Interaction, clean_btns: bool = False):
        msg_id = self.message_id
        
        if msg_id is None:
            return
        if clean_btns:
            self.clear_items()
        channel = interaction.channel
        message = await channel.fetch_message(msg_id)

        await message.edit(embed=self.build_embed(), view=self)
        
    def teams_to_dataframe(self) -> pd.DataFrame:
        data = []

        for player in self.team_a:
            data.append({"player": player, "team": 1})

        for player in self.team_b:
            data.append({"player": player, "team": 2})

        return pd.DataFrame(data)

    @discord.ui.button(label="Join Team A (0)", style=discord.ButtonStyle.green, custom_id="team_a")
    async def join_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        self.add_player(interaction.user)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Join Team B (0)", style=discord.ButtonStyle.blurple, custom_id="team_b")
    async def join_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        if interaction.guild.id == 1184558595602391121 and interaction.user.id == 723638398312513586:  # Only for testing purposes
            await interaction.response.defer()
            self.team_a = set()
            self.team_b = set()
            user: discord.User = interaction.guild.get_member(690644525177110561)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(866339429273305098)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(1184558521459671110)
            self.add_player(user, team_a=False)

        self.add_player(interaction.user, team_a=False)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Drop", style=discord.ButtonStyle.danger, custom_id="drop")
    async def drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        self.remove_player(interaction.user)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.red, custom_id="start", disabled=True)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.processing:
            await interaction.response.send_message(
                "⏳ Event is already starting...", ephemeral=True
            )
            return

        self.processing = True
        await interaction.response.defer()

        # Disable the start button to prevent double-clicks
        button.disabled = True
        await interaction.message.edit(view=self)

        players = Players()
        players.add_players(self.team_a, 1)
        players.add_players(self.team_b, 2)

        new_view = RunningEventView(
            interaction=interaction,
            events=self.events, 
            event=db_event.create_event(interaction.guild_id, interaction.channel_id, players)
        )
        await functions.channelnameopen(interaction.channel, new_view.event.event_id)

        message = await interaction.followup.send(
            embed=new_view.build_embed(),
            view=new_view
        )

        new_view.message_id = message.id
        self.events[interaction.channel.id] = new_view

        