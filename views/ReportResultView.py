import discord
from views.BaseView import BaseTempView
from classes.Match import Match
from classes.Event import Event
import db.db_event as db_event

class ReportResultView(BaseTempView):
    def __init__(self, interaction: discord.Interaction, event_data: Event, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        for match_data in event_data.get_matches(interaction.user.mention):
            label = match_data.get_vs_label(interaction.user.mention)
            button = discord.ui.Button(label=label)

            async def callback(interaction: discord.Interaction, match=match_data):
                await self.send_message(interaction,
                    content=f"Selected: {match}",
                    view=ResultSelectView(match=match, event_data=event_data, message=self.message, parent_view=self.parent_view)
                )

            button.callback = callback
            self.add_item(button)


class ResultSelectView(BaseTempView):
    def __init__(self, match: Match, event_data: Event, message=None, parent_view=None):
        super().__init__(message=message, parent_view=parent_view)
        self.match = match
        self.event_data = event_data

        async def handle_result(interaction: discord.Interaction):
            won = interaction.data["custom_id"] == "won"
            await self.send_message(interaction,
                content=f"You {'won' if won else 'lost'}! What was the score?",
                view=ScoreView(match=self.match, event_data=self.event_data, user_won=won, message=self.message, parent_view=self.parent_view)
            )

        self.add_button(label="I won", style=discord.ButtonStyle.green, callback=handle_result, custom_id="won")
        self.add_button(label="I lost", style=discord.ButtonStyle.red, callback=handle_result, custom_id="lost")



class ScoreView(BaseTempView):
    def __init__(self, match: Match, event_data: Event, user_won: bool, message=None, parent_view=None):
        super().__init__(message=message, parent_view=parent_view)
        self.match = match
        self.user_won = user_won
        self.event_data = event_data

        async def save_callback(interaction: discord.Interaction):
            match_lost = interaction.data["custom_id"] == "close"
            await self.send_message(interaction, content="Saving result...")

            if self.match.get_player().get_mention() == interaction.user.mention:
                win = 2 if self.user_won else (1 if match_lost else 0)
                loss = (1 if match_lost else 0) if self.user_won else 2
            elif self.match.get_opponent().get_mention() == interaction.user.mention:
                loss = 2 if self.user_won else (1 if match_lost else 0)
                win = (1 if match_lost else 0) if self.user_won else 2

            event_data = db_event.update_matches(
                interaction.guild.id, interaction.channel.id, self.event_data.event_id,
                interaction.user.mention, self.match.get_player().get_mention(),
                self.match.get_opponent().get_mention(), win, loss
            )

            await self.parent_view.update_message(interaction, event=event_data)
            await self.send_message(interaction, 
                content=f"{'You won' if self.user_won else 'You lost'}, saved: \nMatch: {event_data.get_match(self.match.get_id())}"
            )

        self.add_button(label="2-0", style=discord.ButtonStyle.green, callback=save_callback, custom_id="clean")
        self.add_button(label="2-1", style=discord.ButtonStyle.green, callback=save_callback, custom_id="close")