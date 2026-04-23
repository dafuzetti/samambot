import discord

class BaseView(discord.ui.View):
    def __init__(self, timeout=None, message=None):
        super().__init__(timeout=timeout)
        self.message = message

    def add_button(self, label: str, callback, style=discord.ButtonStyle.primary, row=None, custom_id=None):
        button = discord.ui.Button(label=label, style=style, row=row, custom_id=custom_id)
        button.callback = callback
        self.add_item(button)
        return button

    async def send(self, interaction: discord.Interaction, content: str, ephemeral=False, **kwargs):
        await interaction.response.defer(ephemeral=ephemeral)
        self.message = await interaction.followup.send(
            content, view=self, ephemeral=ephemeral, wait=True, **kwargs
        )


class BaseTempView(BaseView):
    """Short-lived ephemeral views that auto-delete."""
    def __init__(self, timeout=60, message=None, cancel_btn=True):
        super().__init__(timeout=timeout, message=message)

        if cancel_btn:
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.grey, row=4)
            cancel_button.callback = self.no_callback
            self.add_item(cancel_button)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass

    async def dismiss(self, interaction: discord.Interaction):
        self.stop()
        await self.on_timeout()

    async def no_callback(self, interaction: discord.Interaction):
        await self.dismiss(interaction)

class BasePermView(BaseView):
    """Permanent views that persist indefinitely."""
    def __init__(self, message=None):
        super().__init__(timeout=None, message=message)

    async def refresh(self, content: str, **kwargs):
        if self.message:
            try:
                await self.message.edit(content=content, view=self, **kwargs)
            except discord.NotFound:
                pass