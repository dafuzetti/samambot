import asyncio
import math

import discord
import discord.ui
import pandas as pd
import db.db_event as db_event
import functions
from classes.Matches import Matches
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

        self.selected_match_index = None
        self.selected_result = None

        match_options = []
        for idx, row in self.event.matches.get_iterrows():
            player_a = self.get_member_name(interaction, row[Matches.COL_PLAYER_A])
            player_b = self.get_member_name(interaction, row[Matches.COL_PLAYER_B])
            label = f"{player_a} vs {player_b}"
            match_options.append(discord.SelectOption(label=label, value=str(idx)))

        self.match_select = discord.ui.Select(
            placeholder="Select a match",
            options=match_options,
            custom_id="select_match"
        )
        self.match_select.callback = self.match_select_callback
        self.add_item(self.match_select)

        # Dropdown 2: select result
        result_options = [
            discord.SelectOption(label="2×0", value="2x0"),
            discord.SelectOption(label="2×1", value="2x1"),
            discord.SelectOption(label="1×2", value="1x2"),
            discord.SelectOption(label="0×2", value="0x2"),
        ]
        self.result_select = discord.ui.Select(
            placeholder="Select result",
            options=result_options,
            custom_id="select_result"
        )
        self.result_select.callback = self.result_select_callback
        self.add_item(self.result_select)

        # Save button
        self.save_button = discord.ui.Button(
            label="Save Result",
            style=discord.ButtonStyle.green,
            custom_id="save_result"
        )
        self.save_button.callback = self.save_callback
        self.add_item(self.save_button)

    def get_member_name(self, interaction: discord.Interaction, user_id: str):
        member = interaction.guild.get_member(int(user_id.replace("<@", "").replace(">", "")))
        if member:
            return member  # or use member.mention for tag
        return f"Unknown ({user_id})"
    
    async def match_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.selected_match_index = int(interaction.data['values'][0])

    async def result_select_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.selected_result = interaction.data['values'][0]

    async def save_callback(self, interaction: discord.Interaction):
        processing, msg = await self.is_processing()
        if processing:
            await interaction.response.send_message(msg, ephemeral=True)
            return
        await interaction.response.defer()

        if self.selected_match_index is None or self.selected_result is None:
            return

        row = self.event.matches.get_match(self.selected_match_index)
        a_wins, b_wins = map(int, self.selected_result.split("x"))
        self.event = db_event.update_matches(self.event.guild_id, self.event.channel_id, self.event.event_id, 
                                             row[Matches.COL_PLAYER_A], row[Matches.COL_PLAYER_B], a_wins, b_wins)

        await self.update_message(interaction)
        functions.channelnameopen(interaction.channel, self.event.event_id)

    def build_embed(self):
        if self.event.victory is not None:
            self.clear_items()
        embed = self.print_event_started(self.event)
        return embed

    async def is_processing(self):
        if self.processing_player:
            return True, f"⏳ Event is already starting by: {self.processing_player}"
        return False, None

    async def update_message(self, interaction: discord.Interaction):
        if self.message is not None:
            await self.message.edit(embed=self.build_embed(), view=self)


    def print_event_started(self, event_obj: Event):
        list = event_obj.matches.to_list()
        str_title = "__**Event ID:**__ " + str(event_obj.event_id)
        embed = discord.Embed(title=str_title, color=0x03f8fc)
        count = len(list)
        matches = ''
        playersA = ''
        playersB = ''
        pos = 0
        winA = 0
        winB = 0
        nrp = math.sqrt(count)
        toadd = 1

        for match in list:
            pos = pos + 1
            if str(match[1]) == '2':
                winA = winA + 1
            if str(match[3]) == '2':
                winB = winB + 1
            if pos == toadd:
                playersA = playersA + match[0]
                playersB = playersB + match[2]
                toadd = toadd + nrp + 1
            if match[1] == match[3] and match[3] == 0:
                matches = matches + str(match[0]) + \
                    ' - ' + str(match[2]) + '\n'
            else:
                matches = matches + str(match[0]) + ' ' + str(match[1]) + \
                    '-' + str(match[3]) + ' ' + str(match[2]) + '\n'

        emjA = ''
        emjB = ''
        labelA = 'Player: '
        labelB = 'Player: '
        if str(event_obj.victory) == '2':
            labelB = 'WINNERS: '
            labelA = 'losers: '
            emjA = ':skull:'
            emjB = ':trophy:'
        elif str(event_obj.victory) == '1':
            labelA = 'WINNERS: '
            labelB = 'losers: '
            emjA = ':trophy:'
            emjB = ':skull:'
        elif str(event_obj.victory) == '0':
            emjA = '🍕'
            emjB = '🍕'

        embed.add_field(name='Team A ' + str(emjA),
                        value=f'{labelA}{playersA}\nWin: {winA}', inline=False)
        embed.add_field(name='Team B ' + str(emjB),
                        value=f'{labelB}{playersB}\nWin: {winB}', inline=False)
        embed.add_field(name=f'Pairings: {winA + winB}/{count}',
                        value=matches, inline=False)
        return embed

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

        await self.update_message(interaction)
        State.remove_event(interaction.channel.id)
        self.event = db_event.close_event(self.guild_id, self.channel_id, self.event.event_id)
        await self.update_message(interaction)
        functions.channelnameclose(interaction.channel)
        await confirm_view.confirmation_interaction.edit_original_response(content="Event closed!", view=None)


class ConfirmCloseView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction = None):
        super().__init__(timeout=30)  # optional timeout
        self.confirmed = False
        self.confirmation_interaction = interaction

        # Yes button
        yes_button = discord.ui.Button(label="Yes", style=discord.ButtonStyle.red)
        yes_button.callback = self.yes_callback
        self.add_item(yes_button)

        # No button
        no_button = discord.ui.Button(label="No", style=discord.ButtonStyle.gray)
        no_button.callback = self.no_callback
        self.add_item(no_button)

    async def yes_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.confirmed = True
        # Update the confirmation message to "Event closed"
        if self.confirmation_interaction:
            await self.confirmation_interaction.edit_original_response(content="⏳ Event closing...", view=None)
        self.stop()  # stop the view to end interaction

    async def no_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.confirmed = False
        self.stop()  # stop the view to end interaction