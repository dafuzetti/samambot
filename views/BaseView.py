import asyncio
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
    def __init__(self, timeout=60, message=None, cancel_btn=True, parent_view=None):
        super().__init__(timeout=timeout, message=message)
        self.parent_view = parent_view

        if cancel_btn:
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.grey, row=4)
            cancel_button.callback = self.no_callback
            self.add_item(cancel_button)

    def build_embed(self, interaction):
        return None

    async def on_timeout(self, interaction: discord.Interaction):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
        if self.parent_view:
            self.parent_view.process_end(interaction.user.mention)

    async def dismiss(self, interaction: discord.Interaction):
        self.stop()
        await self.on_timeout()

    async def no_callback(self, interaction: discord.Interaction):
        await self.dismiss(interaction)

class BasePermView(BaseView):
    """Permanent views that persist indefinitely."""
    def __init__(self, message=None):
        super().__init__(timeout=None, message=message)
        self.processing_player = None  # Flag to prevent multiple simultaneous starts
        self.processing_message = "⏳ Processing... Please wait."
        self.reply_message = None
        self.delete_task = None

    def process_start(self, player_tag):
        self.processing_player = player_tag
        asyncio.ensure_future(self._clear_after())

    def process_end(self, player_tag=None):
        if player_tag is None or (player_tag and self.processing_player == player_tag):
            self.processing_player = None

    async def _clear_after(self, delay: int = 120):
        await asyncio.sleep(delay)
        self.process_end()

    async def defer_response(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    async def is_processing(self, interaction: discord.Interaction):
        if self.processing_player and self.processing_player != interaction.user.mention:
            await self.send_message(interaction, f"{self.processing_message} \nBlocked by:{self.processing_player}", ephemeral=True)
            return True
    
        await self.defer_response(interaction)
        return False

    async def send_message(self, interaction: discord.Interaction, content: str=None, view=None):
        msg_view = BaseTempView(cancel_btn=False) if view is None or not isinstance(view, BaseView) else view
        if self.reply_message:
            try:
                await self.reply_message.edit(content=content, embed=msg_view.build_embed(interaction), view=msg_view)
            except discord.NotFound:
                self.reply_message = None

        if not self.reply_message:
            self.reply_message = await interaction.followup.send(content=content, embed=msg_view.build_embed(interaction), ephemeral=True, view=msg_view)
        msg_view.message = self.reply_message
        return self.reply_message

    async def refresh(self, content: str, **kwargs):
        if self.message:
            try:
                await self.message.edit(content=content, view=self, **kwargs)
            except discord.NotFound:
                pass