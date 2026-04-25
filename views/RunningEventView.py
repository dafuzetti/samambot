import asyncio
import discord

import db.db_reports as db_reports

from views.BaseView import BasePermView
from views.ConfirmCloseView import ConfirmCloseView
from views.ReportResultView import ReportResultView
from views.MyMatchesView import MyMatchesView

from classes.Event import Event

class RunningEventView(BasePermView):
    def __init__(self, event: Event, interaction: discord.Interaction = None):
        super().__init__()
        self.event = event
        self.processing_message = "⏳ Event is being closed."
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

    @discord.ui.button(label="Close event", style=discord.ButtonStyle.red, custom_id="close_event")
    async def close_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return

        if discord.utils.get(interaction.guild.roles, name="Samambot Admin") not in interaction.user.roles:
            await self.send_message(interaction, content="Only users with 'Samambot Admin' role can close events")
        else:
            self.process_start(interaction.user.mention)
            await self.send_message(interaction, content="This will permanently close the event. Are you sure?", view=ConfirmCloseView(self))

    @discord.ui.button(label="My open games", style=discord.ButtonStyle.gray, custom_id="my_games")
    async def my_games(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.defer_response(interaction)
        await self.send_message(interaction, "Fetching your open games...")
        my_open_matches = db_reports.open_matches(interaction.guild.id, interaction.channel.id, interaction.user.mention)
        await self.send_message(interaction, view=MyMatchesView(my_open_matches))

    @discord.ui.button(label="Report result", style=discord.ButtonStyle.green, custom_id="report_result")
    async def report_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        if await self.is_processing(interaction):
            return
        
        if self.event.in_event(interaction.user.mention):
            await self.send_message(interaction, view=ReportResultView(interaction=interaction, event_data=self.event, parent_view=self))
        else:
            await self.send_message(interaction, "You are not in the event.\nReport a match for other players by using /result")