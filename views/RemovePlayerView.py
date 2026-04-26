import discord
from classes.State import State
from views.BaseView import BaseTempView
from classes.Players import Players
from classes.Player import Player

class RemovePlayerView(BaseTempView):
    def __init__(self, interaction: discord.Interaction, players: Players, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        for ploop in players.get_players():
            p:Player = ploop
            button = discord.ui.Button(label=p.get_name(), 
                                       style=discord.ButtonStyle.red if p.get_mention() != interaction.user.mention else discord.ButtonStyle.green)

            async def callback(interaction: discord.Interaction, player=p):
                await self.defer_response(interaction)

                await self.parent_view.remove_player(interaction, player.get_mention())                
                await self.send_message(interaction, content=f"Player {player.get_mention()} removed.", view=None)
            
            button.callback = callback
            self.add_item(button)