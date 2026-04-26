import discord
import functions
from classes.State import State
import db.db_event as db_event
from views.RunningEventView import RunningEventView

from views.BaseView import BaseTempView

class ConfirmStartView(BaseTempView):
    def __init__(self, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        self.add_button(label="Start Event", callback=self.yes_callback, style=discord.ButtonStyle.green)

    async def yes_callback(self, interaction: discord.Interaction):
        await self.parent_view.update_message(interaction, clean_btns=True)
        await self.send_message(interaction, content="⏳ Event starting...", view=None)

        event=db_event.create_event(
            interaction.guild_id,
            interaction.channel_id,
            interaction.user.mention,
            interaction.channel.category_id,
            self.parent_view.players
        )
        running_msg = await self.send_message(interaction, content="Event started!", 
                                              view=RunningEventView(interaction, event=event))
        db_event.update_event_message_id(event.get_id(), running_msg.id)
        
        await self.send_message(interaction, content="Event started!")
        functions.channelnameopen(interaction.channel, event.get_event_name())