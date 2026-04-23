import discord

from views.BaseView import BaseTempView

class ConfirmCloseView(BaseTempView):
    def __init__(self, interaction: discord.Interaction = None):
        super().__init__()
        self.confirmed = False
        self.confirmation_interaction = interaction

        yes_button = discord.ui.Button(label="Close Event", style=discord.ButtonStyle.red)
        yes_button.callback = self.yes_callback
        self.add_item(yes_button)

    async def yes_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.confirmed = True
        # Update the confirmation message to "Event closed"
        if self.confirmation_interaction:
            await self.confirmation_interaction.edit_original_response(content="⏳ Event closing...", view=None)
        self.stop()  # stop the view to end interaction
