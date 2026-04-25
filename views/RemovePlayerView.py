import discord
from classes.State import State
from views.BaseView import BaseTempView
from classes.Players import Players
from classes.Player import Player

class RemovePlayerView(BaseTempView):
    def __init__(self, players: Players):
        super().__init__() 
        self.mention = None

        for ploop in players.get_players():
            p:Player = ploop
            button = discord.ui.Button(label=p.get_name(), style=discord.ButtonStyle.red)

            async def callback(interaction: discord.Interaction, player=p):
                await interaction.response.defer()
                self.mention = player.get_mention()

                original_view = State.get_eventView(interaction.channel.id)

                await original_view.remove_player(self.mention)                
                await interaction.edit_original_response(content=f"Player {self.mention} removed.", view=None)
            
            button.callback = callback
            self.add_item(button)