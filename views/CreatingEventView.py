from asyncio import events
import asyncio

import discord
import discord.ui
import pandas as pd

from views.RunningEventView import RunningEventView
from classes.Event import Event
from classes.Players import Players
import db.db_event as db_event
import functions
from classes.State import State

class CreatingEventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.team_a = set()
        self.team_b = set()
        self.message = None
        self.processing_player = None  # Flag to prevent multiple simultaneous starts
        self.num_players = [4,6,8]  # Allowed player counts for starting the event

    def total_players(self):
        return len(self.team_a) + len(self.team_b)

    def add_player(self, player: discord.User, team_a: bool = True):
        if self.total_players() >= 8 or player is None:
            return
        if team_a:
            if(len(self.team_a)< 4):  # Assuming a maximum of 4 players per team
                self.team_b.discard(player.mention)
                self.team_a.add(player.mention)
        else:
            if(len(self.team_b) < 4):  # Assuming a maximum of 4 players per team
                self.team_a.discard(player.mention)
                self.team_b.add(player.mention)

    def build_embed(self):
        embed = discord.Embed(title="New Event Lobby")

        team_a = "\n".join(u for u in self.team_a) or "—"
        team_b = "\n".join(u for u in self.team_b) or "—"

        embed.add_field(name="Team A", value=team_a, inline=True)
        embed.add_field(name="Team B", value=team_b, inline=True)
        embed.set_footer(text=f"Total players: {self.total_players()}")

        return embed

    async def update_message(self, interaction: discord.Interaction, clean_btns: bool = False):
        if clean_btns:
            self.clear_items()
        else:
            for item in self.children:
                if item.custom_id == "start":
                    item.disabled = not (self.total_players() in self.num_players and len(self.team_a) == len(self.team_b))

                if item.custom_id == "team_a":
                    item.label = f"Join Team A ({len(self.team_a)})"

                if item.custom_id == "team_b":
                    item.label = f"Join Team B ({len(self.team_b)})"

        await interaction.message.edit(embed=self.build_embed(), view=self)
    
    async def is_processing(self):
        if self.processing_player:
            return True, f"⏳ Event already started by: {self.processing_player}"
        return False, None

    @discord.ui.button(label="Join Team A (0)", style=discord.ButtonStyle.green, custom_id="team_a")
    async def join_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer() 

        self.add_player(interaction.user)

        await self.update_message(interaction)

    @discord.ui.button(label="Join Team B (0)", style=discord.ButtonStyle.blurple, custom_id="team_b")
    async def join_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer() 
        
        # Only for testing purposes
        if interaction.guild.id == 1184558595602391121 and interaction.user.id == 723638398312513586: 
            self.team_a = set()
            self.team_b = set()
            user: discord.User = interaction.guild.get_member(690644525177110561)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(866339429273305098)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(1184558521459671110)
            self.add_player(user, team_a=False)
        # End of testing purposes

        self.add_player(interaction.user, team_a=False)

        await self.update_message(interaction)

    @discord.ui.button(label="Drop", style=discord.ButtonStyle.danger, custom_id="drop")
    async def drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer() 

        self.team_a.discard(interaction.user.mention)
        self.team_b.discard(interaction.user.mention)

        await self.update_message(interaction)

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.red, custom_id="start", disabled=True)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        start = False
        processing, msg = await self.is_processing()
        if processing:
            print_msg = msg
        elif self.total_players() not in self.num_players or len(self.team_a) != len(self.team_b):
            print_msg = "You need 4, 6 or 8 players with balanced teams to start the event."
        else:
            self.processing_player = interaction.user.mention
            print_msg = "⏳ Event starting..."
            start = True
            
        #instead of deferring, send an immediate response
        await interaction.response.send_message(print_msg, ephemeral=True)

        if start:
            await self.update_message(interaction, clean_btns=True) 
            players = Players()
            players.add_teams(self.team_a, self.team_b)
            new_view = RunningEventView(
                interaction=interaction,
                event=db_event.create_event(
                    interaction.guild_id,
                    interaction.channel_id,
                    players
                )
            )
            State.set_eventView(interaction.channel.id, new_view)
            new_view.message = await interaction.channel.send(embed=new_view.build_embed(),view=new_view)
            try:
                await interaction.edit_original_response(content=f"Event started!", view=None)
            except:
                pass
            functions.channelnameopen(interaction.channel, new_view.event.event_id)