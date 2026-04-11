import discord

class RemovePlayerView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, players):
        super().__init__(timeout=30)  # optional timeout
        self.mention = None
        self.confirmation_interaction = interaction

        for p in players:
            button = discord.ui.Button(label=p, style=discord.ButtonStyle.red)

            async def callback(interaction, player=p):
                await interaction.response.defer()
                self.mention = p
                self.stop()
            
            button.callback = callback
            self.add_item(button)

        # No one button
        no_button = discord.ui.Button(label="No one", style=discord.ButtonStyle.green)
        no_button.callback = self.no_callback
        self.add_item(no_button)

    async def no_callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        self.stop()  # stop the view to end interaction