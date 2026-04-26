import asyncio

import discord
import db.db_event as db_event

from views.BaseView import BasePermView
from views.ConfirmStartView import ConfirmStartView
from views.RemovePlayerView import RemovePlayerView
from classes.Players import Players
from classes.State import State

class CreatingEventView(BasePermView):
    def __init__(self):
        super().__init__()
        self.players: Players = Players()
        self.processing_message = "⏳ Starting event..."

    def total_players(self):
        return self.players.len()

    async def add_player(self, interaction: discord.Interaction, player: discord.User, team_a: bool = True):
        self.players.add_team_mate(player_tag=player.mention, team=1 if team_a else 2)
        State.set_player_name(player.mention, player.display_name)
        await self.update_message(interaction)

    async def remove_player(self, interaction: discord.Interaction, player_mention: str):
        self.players.remove_player_tag(player_mention)
        await self.update_message(interaction)

    def build_embed(self):
        embed = discord.Embed(title="New Event Lobby")
        embed.add_field(name="Team A", value=self.players.get_players_names_col(1), inline=True)
        embed.add_field(name="Team B", value=self.players.get_players_names_col(2), inline=True)
        return embed

    async def update_message(self, interaction: discord.Interaction, clean_btns: bool = False):
        if clean_btns:
            self.clear_items()
        else:
            for item in self.children:
                if item.custom_id == "drop":
                    item.disabled = (self.total_players() == 0)

                if item.custom_id == "start":
                    item.disabled = not self.players.get_ready()

                if item.custom_id == "team_a":
                    item.label = f"Join Team A ({len(self.players.get_players_tags(1))})"

                if item.custom_id == "team_b":
                    item.label = f"Join Team B ({len(self.players.get_players_tags(2))})"

        if self.message is not None:
            await self.send_message(interaction, view=self, original_response=self.message)

    @discord.ui.button(label="Join Team A (0)", style=discord.ButtonStyle.green, custom_id="team_a")
    async def join_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return

        await self.add_player(interaction, player=interaction.user)

    @discord.ui.button(label="Join Team B (0)", style=discord.ButtonStyle.blurple, custom_id="team_b")
    async def join_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return
        
        # Only for testing purposes
        if interaction.guild.id == 1184558595602391121 and interaction.user.id == 723638398312513586: 
            await self.add_player(interaction, player=interaction.guild.get_member(690644525177110561), team_a=True)
            await self.add_player(interaction, player=interaction.guild.get_member(866339429273305098), team_a=True)
            await self.add_player(interaction, player=interaction.guild.get_member(1184558521459671110), team_a=False)
        # End of testing purposes

        await self.add_player(interaction, player=interaction.user, team_a=False)

    @discord.ui.button(label="Remove player", style=discord.ButtonStyle.danger, custom_id="drop", disabled=True)
    async def drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return

        if self.players.len() > 0:
            await self.send_message(interaction, content="Select a player to be removed:", view=RemovePlayerView(self.players, self))
        else:
            await self.send_message(interaction, content="No players to remove.")

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.red, custom_id="start", disabled=True)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return
        if not self.players.get_ready():
            await self.send_message(interaction, content="You need 4, 6 or 8 players with balanced teams to start the event.")
            return 
        if interaction.channel.category is None:
            await self.send_message(interaction, content="Events can only be started inside a category (season). \nCreate or move a channel to a category.")
            return 
        
        self.process_start(interaction.user.mention)
        await self.send_message(interaction, content="Starting the event cannot be undone. Are you sure?", view=ConfirmStartView(self))