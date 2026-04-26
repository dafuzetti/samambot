import discord
from views.BaseView import BaseTempView
from classes.Players import Players
from classes.Player import Player

class ReplaceDummyView(BaseTempView):
    def __init__(self, players: list[Player], parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        for ploop in players:
            p:Player = ploop
            if p.is_dummy():
                button = discord.ui.Button(label=str(p), style=discord.ButtonStyle.grey, row=p.get_team())

                async def callback(interaction: discord.Interaction, player=p):
                    await self.defer_response(interaction)
                    await self.send_message(interaction, content=f"{player.get_mention()} replaced by dummy {interaction.user.mention}.", view=None)
                
                button.callback = callback
                self.add_item(button)