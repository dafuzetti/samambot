import discord
import functions
from classes.State import State
import db.db_event as db_event

from views.BaseView import BaseTempView

class ConfirmCloseView(BaseTempView):
    def __init__(self, parent_view=None):
        super().__init__(parent_view=parent_view)

        yes_button = discord.ui.Button(label="Close Event", style=discord.ButtonStyle.red)
        yes_button.callback = self.yes_callback
        self.add_item(yes_button)

    async def yes_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        await interaction.edit_original_response(content="⏳ Event closing...", view=None)

        event = db_event.close_event(interaction.guild.id, interaction.channel.id, interaction.user.mention)
        await self.parent_view.update_message(event=event)

        await interaction.edit_original_response(content="Event closed!", view=None)
        State.remove_event(interaction.channel.id)
        functions.channelnameclose(interaction.channel)