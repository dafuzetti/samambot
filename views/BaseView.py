import asyncio
import discord
from classes.State import State

class BaseView(discord.ui.View):
    def __init__(self, timeout=None, message=None):
        super().__init__(timeout=timeout)
        self.message = message

    def add_button(self, label: str, callback, style=discord.ButtonStyle.primary, row=None, custom_id=None):
        button = discord.ui.Button(label=label, style=style, row=row, custom_id=custom_id)
        button.callback = callback
        self.add_item(button)
        return button

    async def mng_send_message(self, interaction: discord.Interaction, content: str=None, view=None, original_response: discord.Message=None):
        await self.defer_response(interaction)
        msg = None
        msg_view = BaseTempView(cancel_btn=False) if view is None or not isinstance(view, BaseView) else view
        if original_response:
            try:
                msg = await original_response.edit(content=content, embed=msg_view.build_embed(), view=msg_view)
            except discord.NotFound:
                msg = None

        if not msg:
            if isinstance(msg_view, BasePermView):
                msg = await interaction.channel.send(content=content, embed=msg_view.build_embed(), view=msg_view)
            else:
                msg = await interaction.followup.send(content=content, embed=msg_view.build_embed(), ephemeral=True, view=msg_view)

        msg_view.message = msg
        if isinstance(msg_view, BasePermView):
            State.set_eventView(interaction.channel.id, msg_view)
        elif isinstance(msg_view, BaseTempView):
            msg_view.start_timeout()
        return msg

    async def defer_response(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

    def build_embed(self):
        return None
    
class BaseTempView(BaseView):
    """Short-lived ephemeral views that auto-delete."""
    def __init__(self, timeout=30, message=None, cancel_btn=True, parent_view=None):
        super().__init__(timeout=timeout, message=message)
        self.parent_view = parent_view
        self._timeout_task = None

        if cancel_btn:
            cancel_button = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.grey, row=4)
            cancel_button.callback = self.no_callback
            self.add_item(cancel_button)

    async def send_message(self, interaction: discord.Interaction, content: str=None, view=None):
        return await self.mng_send_message(interaction, content=content, view=view, 
                                           original_response=None if isinstance(view, BasePermView) else self.message)

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.delete()
            except discord.NotFound:
                pass
        if self.parent_view:
            self.parent_view.process_end()

    def start_timeout(self):
        if self._timeout_task:
            self._timeout_task.cancel()
        self._timeout_task = asyncio.create_task(self._run_timeout())

    async def _run_timeout(self):
        try:
            await asyncio.sleep(self.timeout)
            await self.on_timeout()
        except asyncio.CancelledError:
            pass

    async def dismiss(self):
        self.stop()
        if self._timeout_task:
            self._timeout_task.cancel()
        await self.on_timeout()

    async def no_callback(self, interaction: discord.Interaction):
        await self.dismiss()

class BasePermView(BaseView):
    """Permanent views that persist indefinitely."""
    def __init__(self, message=None):
        super().__init__(timeout=None, message=message)
        self.processing_player = None  # Flag to prevent multiple simultaneous starts
        self.processing_message = "⏳ Processing... Please wait."

    def process_start(self, player_tag):
        self.processing_player = player_tag
        asyncio.ensure_future(self._clear_after())

    def process_end(self, player_tag=None):
        if player_tag is None or (player_tag and self.processing_player == player_tag):
            self.processing_player = None

    async def send_message(self, interaction: discord.Interaction, content: str=None, view=None, original_response=None):
        return await self.mng_send_message(interaction, content=content, view=view, original_response=original_response)

    async def _clear_after(self, delay: int = 120):
        await asyncio.sleep(delay)
        self.process_end()

    async def is_processing(self, interaction: discord.Interaction):
        if self.processing_player and self.processing_player != interaction.user.mention:
            await self.send_message(interaction, f"{self.processing_message} \nBlocked by:{self.processing_player}", ephemeral=True)
            return True
    
        await self.defer_response(interaction)
        return False