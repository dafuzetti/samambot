import discord
from classes.State import State
from classes.Match import Match
from classes.Event import Event
from db import db_event

class ReportResultView(discord.ui.View, Event):
    def __init__(self, interaction: discord.Interaction = None, event_data: Event = None):
        super().__init__(timeout=60)
        for match_data in event_data.get_matches(interaction.user.mention):
            label = match_data.get_vs_label(interaction.user.mention)
            button = discord.ui.Button(label=label)

            async def callback(interaction: discord.Interaction, match=match_data):
                view = ResultSelectView(match, event_data)
                await interaction.response.edit_message(
                    content=f"Selected: {match}",
                    view=view
                )

            button.callback = callback
            self.add_item(button)


class ResultSelectView(discord.ui.View, Event):
    def __init__(self, match: Match, event_data: Event):
        super().__init__(timeout=60)
        self.match = match
        self.event_data = event_data

        won_button = discord.ui.Button(label="I won", style=discord.ButtonStyle.success)
        lost_button = discord.ui.Button(label="I lost", style=discord.ButtonStyle.danger)

        async def won_callback(interaction):
            await self.handle_result(interaction, won=True)

        async def lost_callback(interaction):
            await self.handle_result(interaction, won=False)

        won_button.callback = won_callback
        lost_button.callback = lost_callback

        self.add_item(won_button)
        self.add_item(lost_button)

    async def handle_result(self, interaction: discord.Interaction, won: bool):
        view = ScoreView(self.match, self.event_data, won)
        await interaction.response.edit_message(
            content=f"Result saved: {'You won' if won else 'You lost'}",
            view=view
        )

class ScoreView(discord.ui.View):
    def __init__(self, match: Match, event_data: Event, user_won: bool):
        super().__init__(timeout=60)
        self.match = match
        self.user_won = user_won
        self.event_data = event_data

        clean = discord.ui.Button(label="2-0")
        close = discord.ui.Button(label="2-1")

        async def clean_cb(interaction):
            await save_callback(interaction, self.user_won, match_lost=False)

        async def close_cb(interaction):
            await save_callback(interaction, self.user_won, match_lost=True)

        async def save_callback(interaction: discord.Interaction, user_won: bool, match_lost: bool):
            await interaction.response.defer()
            for item in self.children:
                item.disabled = True
            await interaction.edit_original_response(view=None, content="Saving result...")
            
            if self.match.get_player().get_mention() == interaction.user.mention:
                win = 2 if user_won else (1 if match_lost else 0)
                loss = (1 if match_lost else 0) if user_won else 2
            elif self.match.get_opponent().get_mention() == interaction.user.mention:
                loss = 2 if user_won else (1 if match_lost else 0)
                win = (1 if match_lost else 0) if user_won else 2
            
            event_data = db_event.update_matches(interaction.guild.id, interaction.channel.id, self.event_data.event_id, interaction.user.mention, 
                                                 self.match.get_player().get_mention(), self.match.get_opponent().get_mention(), win, loss)
            original_view = State.get_eventView(interaction.channel.id)
            original_view.event = event_data
            await original_view.update_message()
            await interaction.edit_original_response(
                content=f"{'You won' if user_won else 'You lost'}, saved: \nMatch: {event_data.get_match(self.match.get_id())}",
                view=None
            )

        clean.callback = clean_cb
        close.callback = close_cb

        self.add_item(clean)
        self.add_item(close)