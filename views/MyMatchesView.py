from collections import defaultdict
import discord
import functions
import db.db_reports as db_reports

class MyMatchesView(discord.ui.View):
    def __init__(self, rows):
        super().__init__(timeout=None)
        self.rows = rows

    async def build_embed(self, interaction, user):
        grouped = self.group_matches()
        total_matches = 0
        try:
            if len(self.rows) > 0:
                embed = discord.Embed(title=f"{user.display_name} Open Games:")

                for opponent, seasons in grouped.items():
                    value = ""
                    player_count = 0

                    for season, events in seasons.items():
                        player_count += len(events)
                        total_matches += len(events)

                        events_str = ", ".join(
                            self.get_event_channel_link(interaction.guild, season, e)
                            for e in events
                        )

                        name_cat = "No season"
                        if season is not None:
                            category = interaction.guild.get_channel(int(season))
                            if isinstance(category, discord.CategoryChannel):
                                name_cat = category.name

                        value += f"↳ **{name_cat}**: {events_str}\n"

                    embed.add_field(
                        name=f"👤 **{self.get_display_name(interaction, opponent)}** ({player_count})",
                        value=value,
                        inline=False
                    )
                embed.set_footer(text=f"Total matches: {total_matches}")
            else:
                embed = discord.Embed(title="You don't have any match to play!")
        except Exception:
            embed = discord.Embed(title="User not found")

        return embed
    
    def get_event_channel_link(self, guild, category_id, event_id):
        if category_id is None:
            return str(event_id)
        category = guild.get_channel(int(category_id))
        if not category:
            return str(event_id)

        target = f"_{event_id}_"

        for ch in category.channels:
            if target in ch.name:
                return f"https://discord.com/channels/{guild.id}/{ch.id}"

        return str(event_id)

    def group_matches(self):
        data = defaultdict(lambda: defaultdict(list))
        for player, category, event_id in self.rows:
            data[player][category].append(event_id)
        return data
    
    def get_display_name(self, interaction, mention: str):
        user_id = int(mention.strip("<@!>"))
        member = interaction.guild.get_member(user_id)
        return member.display_name if member else mention