import asyncio

import discord
import functions
import db.db_event as db_event

from views.RunningEventView import RunningEventView
from views.RemovePlayerView import RemovePlayerView
from classes.Players import Players
from classes.State import State

class CreatingEventView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.players: Players = Players()
        self.message = None
        self.processing_player = None  # Flag to prevent multiple simultaneous starts

    def total_players(self):
        return self.players.len()

    def add_player(self, player: discord.User, team_a: bool = True):
        self.players.add_player(player_tag=player.mention, team=1 if team_a else 2, name=player.display_name)

    # Needs to be called from the remove player view
    async def remove_player(self, player_mention):
        self.players.remove_player_tag(player_mention)
        await self.update_message()

    def build_embed(self):
        embed = discord.Embed(title="New Event Lobby")

        list_a = self.players.get_players_names(1)
        list_b = self.players.get_players_names(2)

        team_a = "\n".join(list_a) if list_a else "-"
        team_b = "\n".join(list_b) if list_b else "-"

        embed.add_field(name="Team A", value=team_a, inline=True)
        embed.add_field(name="Team B", value=team_b, inline=True)

        return embed

    async def update_message(self, clean_btns: bool = False):
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
            await self.message.edit(embed=self.build_embed(), view=self)
    
    def is_processing(self):
        if self.processing_player:
            return True, f"⏳ Event already started by: {self.processing_player}"
        return False, None

    @discord.ui.button(label="Join Team A (0)", style=discord.ButtonStyle.green, custom_id="team_a")
    async def join_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer() 

        self.add_player(interaction.user)

        await self.update_message()

    @discord.ui.button(label="Join Team B (0)", style=discord.ButtonStyle.blurple, custom_id="team_b")
    async def join_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer() 
        
        # Only for testing purposes
        if interaction.guild.id == 1184558595602391121 and interaction.user.id == 723638398312513586: 
            self.add_player(interaction.guild.get_member(690644525177110561), team_a=True)
            self.add_player(interaction.guild.get_member(866339429273305098), team_a=True)
            self.add_player(interaction.guild.get_member(1184558521459671110), team_a=False)
        # End of testing purposes

        self.add_player(interaction.user, team_a=False)

        await self.update_message()

    @discord.ui.button(label="Remove player", style=discord.ButtonStyle.danger, custom_id="drop", disabled=True)
    async def drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        if self.players.len() > 0:
            confirm_view = RemovePlayerView(self.players)
            confirm_view.message = await interaction.followup.send(
                "Select player to be removed:", view=confirm_view, ephemeral=True
            )
        else:
            msg_no_players = await interaction.followup.send(
                "No players to be removed.", ephemeral=True
            )
            await asyncio.sleep(30)
            await msg_no_players.delete()


        # need to update from the internal event? await self.update_message()

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.red, custom_id="start", disabled=True)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        start = False
        processing, msg = self.is_processing()
        if processing:
            print_msg = msg
        elif not self.players.get_ready():
            print_msg = "You need 4, 6 or 8 players with balanced teams to start the event."
        else:
            self.processing_player = interaction.user.mention
            print_msg = "⏳ Event starting..."
            start = True

        #instead of deferring, send an immediate response
        await interaction.response.send_message(print_msg, ephemeral=True)

        if start:
            await self.update_message(clean_btns=True) 
            category_id = None
            if interaction.channel.category is not None:
                category_id = interaction.channel.category_id
            event=db_event.create_event(
                    interaction.guild_id,
                    interaction.channel_id,
                    interaction.user.mention,
                    category_id,
                    self.players
                )
            new_view = RunningEventView(
                interaction=interaction,
                event=event
            )
            new_view.message = await interaction.channel.send(embed=new_view.build_embed(),view=new_view)
            State.set_eventView(interaction.channel.id, new_view)
            db_event.update_event_message_id(new_view.event.event_id, new_view.message.id)
            try:
                await interaction.edit_original_response(content=f"Event started!", view=None)
            except:
                pass
            functions.channelnameopen(interaction.channel, new_view.event.get_event_name())