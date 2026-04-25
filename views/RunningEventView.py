import asyncio
import math
import discord

import db.db_reports as db_reports

from views.BaseView import BasePermView
from views.ConfirmCloseView import ConfirmCloseView
from views.ReportResultView import ReportResultView
from views.MyMatchesView import MyMatchesView

from classes.Match import Match
from classes.Event import Event

class RunningEventView(BasePermView):
    def __init__(self, event: Event, interaction: discord.Interaction = None):
        super().__init__()
        self.event = event
        self.processing_message = "⏳ Event is being closed."
        self.guild_id = event.guild_id if interaction is None else interaction.guild.id
        self.channel_id = event.channel_id if interaction is None else interaction.channel.id
        self.season_name = "" if interaction is None else getattr(getattr(interaction.channel, "category", None), "name", "")
        

    def build_embed(self):
        if self.event.victory is not None:
            self.clear_items()
        embed = self.print_event_started()
        return embed

    async def update_message(self, event: Event = None):
        if event is not None:
            self.event = event
        if self.message is not None:
            await self.message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Close event", style=discord.ButtonStyle.red, custom_id="close_event")
    async def close_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return

        if discord.utils.get(interaction.guild.roles, name="Samambot Admin") not in interaction.user.roles:
            await interaction.followup.send("Only users with 'Samambot Admin' role can close events", ephemeral=True)
            return
        
        confirm_view = ConfirmCloseView(self)
        confirm_view.message = await interaction.followup.send(
            "Closing an event cannot be undone, do you want to close it?", view=confirm_view, ephemeral=True
        )

    @discord.ui.button(label="My open games", style=discord.ButtonStyle.gray, custom_id="my_games")
    async def my_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        view = MyMatchesView(db_reports.open_matches(interaction.guild.id, interaction.channel.id, interaction.user.mention))
        embed_built = await view.build_embed(interaction, interaction.user)
        await interaction.followup.send(embed=embed_built, ephemeral=True)

    @discord.ui.button(label="Report result", style=discord.ButtonStyle.green, custom_id="report_result")
    async def report_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return
        
        if self.event.in_event(interaction.user.mention):
            confirm_view = ReportResultView(interaction=interaction, event_data=self.event, parent_view=self)
            confirm_view.message = await interaction.followup.send(
                "Select your opponent:",
                view=confirm_view,
                ephemeral=True
            )
        else:
            msg_player_not_in = await interaction.followup.send(
                "You are not in the event.\n " \
                "Report a match for other players by using /result",
                ephemeral=True
            )
            await asyncio.sleep(30)
            await msg_player_not_in.delete()

    def print_event_started(self):
        str_title = f"__**Event:**__ {self.event.get_event_name()}  {self.season_name}"
        embed = discord.Embed(title=str_title, color=0x03f8fc)

        embed.description = f'Event ID: {str(self.event.get_id())}'
        embed.add_field(name='Team A ' + self.event.get_team_emoji(1),
                        value=f'{self.event.print_players(team=1)}\nWin: {self.event.get_wins(team=1)}', inline=False)
        embed.add_field(name='Team B ' + self.event.get_team_emoji(2),
                        value=f'{self.event.print_players(team=2)}\nWin: {self.event.get_wins(team=2)}', inline=False)
        embed.add_field(name=f'Pairings: {self.event.get_wins(team=1) + self.event.get_wins(team=2)}/{len(self.event.get_matches())}',
                        value=f'{self.event.print_matches()}', inline=False)
        return embed