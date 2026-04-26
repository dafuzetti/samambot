import discord
import functions
from classes.State import State
import db.db_event as db_event

from views.BaseView import BaseTempView

class ConfirmCloseView(BaseTempView):
    def __init__(self, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        self.add_button(label="Close Event", callback=self.yes_callback, style=discord.ButtonStyle.red)

    async def yes_callback(self, interaction: discord.Interaction):
        await self.send_message(interaction, content="⏳ Event closing...", view=None)

        event = db_event.close_event(interaction.guild.id, interaction.channel.id, interaction.user.mention)
        await self.parent_view.update_message(interaction, event=event)

        await self.send_message(interaction, content="Event closed!", view=None)

        State.remove_event(interaction.channel.id)
        functions.channelnameclose(interaction.channel)