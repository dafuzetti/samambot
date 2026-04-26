import discord
from views.BaseView import BaseTempView
from classes.Player import Player
from db import db_event

class ReplaceDummyView(BaseTempView):
    def __init__(self, players: list[Player], parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message)

        for ploop in players:
            p:Player = ploop
            if p.is_dummy():
                button = discord.ui.Button(label=str(p), style=discord.ButtonStyle.grey, row=p.get_team())

                async def callback(interaction: discord.Interaction, player=p):
                    await self.send_message(interaction, content=f"Replacing dummy {player.get_mention()} with {interaction.user.mention}...")
                    event=db_event.replace_player_in_event(self.parent_view.event.guild_id, self.parent_view.event.channel_id, interaction.user.mention,
                                                            player.get_mention(), interaction.user.mention, event_id=self.parent_view.event.event_id)
                    await self.send_message(interaction, content=f"{player.get_mention()} replaced by dummy {interaction.user.mention}.")
                    await self.parent_view.update_message(interaction, event)
                
                button.callback = callback
                self.add_item(button)