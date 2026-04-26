import discord
import functions
import db.db_event as db_event
from views.RunningEventView import RunningEventView

from views.BaseView import BaseTempView

class ConfirmStartView(BaseTempView):
    def __init__(self, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)
        if self.parent_view.players.len() < 4 and len(self.parent_view.players.get_players(team=1)) < 2 and len(self.parent_view.players.get_players(team=2)) < 2:
            self.add_button(label="Add up to 4 dummyes", callback=self.yes_callback, style=discord.ButtonStyle.grey, custom_id="4")
        if self.parent_view.players.len() < 6 and len(self.parent_view.players.get_players(team=1)) < 3 and len(self.parent_view.players.get_players(team=2)) < 3:
            self.add_button(label="Add up to 6 dummyes", callback=self.yes_callback, style=discord.ButtonStyle.grey, custom_id="6")
        if self.parent_view.players.len() < 8:
            self.add_button(label="Add up to 8 dummyes", callback=self.yes_callback, style=discord.ButtonStyle.grey, custom_id="8")
        if self.parent_view.players.get_ready():
            self.add_button(label="Start Event", callback=self.yes_callback, style=discord.ButtonStyle.green, custom_id="start")

    async def yes_callback(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] != "start":
            self.parent_view.add_dummyes_to_fill(seats=int(interaction.data["custom_id"]))
        await self.start_event(interaction)

    async def start_event(self, interaction: discord.Interaction):
        await self.parent_view.update_message(interaction, clean_btns=True)
        await self.send_message(interaction, content="⏳ Event starting...", view=None)

        event=db_event.create_event(
            interaction.guild_id,
            interaction.channel_id,
            interaction.user.mention,
            interaction.channel.category_id,
            self.parent_view.players
        )
        running_msg = await self.send_message(interaction, view=RunningEventView(interaction, event=event))
        db_event.update_event_message_id(event.get_id(), running_msg.id)
        
        await self.send_message(interaction, content="Event started!")
        functions.channelnameopen(interaction.channel, event.get_event_name())