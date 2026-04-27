import asyncio

from classes.Event import Event
import discord
import functions
from classes.State import State
import db.db_event as db_event
import os
import csv

from views.BaseView import BaseTempView

class ConfirmCloseView(BaseTempView):
    def __init__(self, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        self.add_button(label="Close Event", callback=self.yes_callback, style=discord.ButtonStyle.red)

    async def yes_callback(self, interaction: discord.Interaction):
        await self.send_message(interaction, content="⏳ Event closing...", view=None)

        event: Event = db_event.close_event(interaction.guild.id, interaction.channel.id, interaction.user.mention)
        await self.parent_view.update_message(interaction, event=event)

        asyncio.create_task(self.send_log(interaction, event))

        await self.send_message(interaction, content="Event closed!", view=None)

        State.remove_event(interaction.channel.id)
        functions.channelnameclose(interaction.channel)

    async def send_log(self, interaction: discord.Interaction, event: Event):
        try:
            log_channel = None
            for channel in interaction.guild.channels:
                if channel.name == "samambot_log" and isinstance(channel, discord.TextChannel):
                    log_channel = channel
                    break
                
            if log_channel:
                category_name = getattr(interaction.channel.category, "name", "Event") if interaction.channel.category else "Event"
                csv_file = db_event.generate_event_csv(event, category_name)
                if csv_file and os.path.exists(csv_file):
                    with open(csv_file, 'rb') as f:
                        await log_channel.send(file=discord.File(f, csv_file))
                    os.remove(csv_file)
        except Exception as error:
            print(f"Error sending event log: {error}")

def generate_event_csv(event: Event, category_name: str = "no_season") -> str:
    try:
        filename = f"{category_name}_event{event.get_event_name()}_{event.get_id()}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Match ID', 'Player A', 'Wins A', 'Wins B', 'Player B']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for match in event.get_matches():
                writer.writerow({
                    'Match ID': match.id,
                    'Player A': str(match.get_player()),
                    'Wins A': match.get_wins(),
                    'Wins B': match.get_losses(),
                    'Player B': str(match.get_opponent())
                })
        
        return filename
    except Exception as error:
        print(f"Error generating CSV: {error}")
        return None