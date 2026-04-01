import math
import discord

import db.db_event as db_event
import functions

from views.ConfirmCloseView import ConfirmCloseView
from views.ReportResultView import ReportResultView

from classes.Match import Match
from classes.Event import Event
from classes.State import State

class RunningEventView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, event: Event):
        super().__init__(timeout=None)
        self.message = None
        self.processing_player = None  # Flag to prevent multiple simultaneous actions
        self.event = event
        self.guild_id = interaction.guild.id
        self.channel_id = interaction.channel.id

    def build_embed(self):
        if self.event.victory is not None:
            self.clear_items()
        embed = self.print_event_started()
        return embed

    async def is_processing(self):
        if self.processing_player:
            return True, f"⏳ Event is being closed by: {self.processing_player}"
        return False, None

    async def update_message(self):
        if self.message is not None:
            await self.message.edit(embed=self.build_embed(), view=self)
    
    @discord.ui.button(label="Close event", style=discord.ButtonStyle.red, custom_id="close_event")
    async def close_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return

        role = discord.utils.get(interaction.guild.roles, name="Samambot Admin")
        if role in interaction.user.roles:
            self.processing_player = interaction.user.mention
            confirm_view = ConfirmCloseView(interaction)
            await interaction.response.send_message(
                "Are you sure you want to close the event?", view=confirm_view, ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Only users with 'Samambot Admin' role can close events", ephemeral=True
            )

        # Wait until the user clicks Yes/No
        await confirm_view.wait()

        if not confirm_view.confirmed:
            # User canceled
            self.processing_player = None
            await confirm_view.confirmation_interaction.edit_original_response(content="Event closed canceled.", view=None)
            return

        await self.update_message()
        State.remove_event(interaction.channel.id)
        self.event = db_event.close_event(self.guild_id, self.channel_id, self.event.event_id)
        await self.update_message()
        functions.channelnameclose(interaction.channel)
        await confirm_view.confirmation_interaction.edit_original_response(content="Event closed!", view=None)

    @discord.ui.button(label="Report result", style=discord.ButtonStyle.green, custom_id="report_result")
    async def report_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        for m in self.event.get_matches():
            if isinstance(m, Match):
                match: Match = m
                match.set_names(await functions.get_player_name(interaction, match.player_a), await functions.get_player_name(interaction, match.player_b))

        confirm_view = ReportResultView(interaction=interaction, event_data=self.event)
        await interaction.response.send_message(
            "Select your opponent:",
            view=confirm_view,
            ephemeral=True
        )

    def print_event_started(self):
        list = self.event.get_matches()
        str_title = "__**Event ID:**__ " + str(self.event.get_id())
        embed = discord.Embed(title=str_title, color=0x03f8fc)
        count = len(list)
        matches_desc = ''
        playersA = ''
        playersB = ''
        pos = 0
        winA = 0
        winB = 0
        nrp = math.sqrt(count)
        toadd = 1

        for m in list:
            if isinstance(m, Match):
                match: Match = m
                pos = pos + 1
                if str(match.wins_a) == '2':
                    winA = winA + 1
                if str(match.wins_b) == '2':
                    winB = winB + 1
                if pos == toadd:
                    playersA = playersA + str(match.player_a)
                    playersB = playersB + str(match.player_b)
                    toadd = toadd + nrp + 1
                if match.wins_a == 0 and match.wins_b == 0:
                    matches_desc = matches_desc + str(match.player_a) + \
                        ' - ' + str(match.player_b) + '\n'
                else:
                    matches_desc = matches_desc + str(match.player_a) + ' ' + str(match.wins_a) + \
                        '-' + str(match.wins_b) + ' ' + str(match.player_b) + '\n'

        emjA = ''
        emjB = ''
        labelA = 'Player: '
        labelB = 'Player: '
        if str(self.event.get_victory()) == '2':
            labelB = 'WINNERS: '
            labelA = 'losers: '
            emjA = ':skull:'
            emjB = ':trophy:'
        elif str(self.event.get_victory()) == '1':
            labelA = 'WINNERS: '
            labelB = 'losers: '
            emjA = ':trophy:'
            emjB = ':skull:'
        elif str(self.event.get_victory()) == '0':
            emjA = '🍕'
            emjB = '🍕'

        embed.add_field(name='Team A ' + str(emjA),
                        value=f'{labelA}{playersA}\nWin: {winA}', inline=False)
        embed.add_field(name='Team B ' + str(emjB),
                        value=f'{labelB}{playersB}\nWin: {winB}', inline=False)
        embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                        value=f'{matches_desc}', inline=False)
        return embed