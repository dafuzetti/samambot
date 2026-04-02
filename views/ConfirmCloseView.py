import discord

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