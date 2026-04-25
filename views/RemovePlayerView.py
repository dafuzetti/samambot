import discord
from classes.State import State
from views.BaseView import BaseTempView
from classes.Players import Players
from classes.Player import Player

class RemovePlayerView(BaseTempView):
    def __init__(self, players: Players, parent_view=None):
        super().__init__(parent_view=parent_view)
        self.mention = None

        for ploop in players.get_players():
            p:Player = ploop
            button = discord.ui.Button(label=p.get_name(), style=discord.ButtonStyle.red)

            async def callback(interaction: discord.Interaction, player=p):
                await interaction.response.defer()
                self.mention = player.get_mention()

                await self.parent_view.remove_player(self.mention)                
                await interaction.edit_original_response(content=f"Player {self.mention} removed.", view=None)
            
            button.callback = callback
            self.add_item(button)