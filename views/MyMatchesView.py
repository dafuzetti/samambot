from collections import defaultdict
from classes.State import State
import discord
from views.BaseView import BaseTempView

class MyMatchesView(BaseTempView):
    def __init__(self, interaction: discord.Interaction, rows, parent_view=None, message=None):
        super().__init__(parent_view=parent_view, message=message, cancel_btn=False)
        self.rows = rows
        self.interaction = interaction

    def build_embed(self):
        grouped = self.group_matches()
        total_matches = 0
        user = self.interaction.user
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
                            self.get_event_channel_link(self.interaction.guild, season, e)
                            for e in events
                        )

                        name_cat = "No season"
                        if season is not None:
                            category = self.interaction.guild.get_channel(int(season))
                            if isinstance(category, discord.CategoryChannel):
                                name_cat = category.name

                        value += f"↳ **{name_cat}**: {events_str}\n"

                    embed.add_field(
                        name=f"👤 **{State.get_player_name(opponent)}** ({player_count})",
                        value=value,
                        inline=False
                    )
                event_summary = self.build_event_summary()
                if event_summary:
                    embed.add_field(name="Event summary", value=event_summary, inline=False)
                embed.set_footer(text=f"Total matches: {total_matches}")
            else:
                embed = discord.Embed(title="You don't have any match to play!")
        except Exception:
            embed = discord.Embed(title="Not found")

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

    def build_event_summary(self):
        event_counts = {}
        event_categories = {}
        for player, category, event_id in self.rows:
            event_counts[event_id] = event_counts.get(event_id, 0) + 1
            event_categories[event_id] = category

        if not event_counts:
            return None

        summary_lines = []
        for event_id, count in sorted(event_counts.items(), key=lambda item: str(item[0])):
            category = event_categories.get(event_id)
            link = self.get_event_channel_link(self.interaction.guild, category, event_id)
            match_word = "match" if count == 1 else "matches"
            summary_lines.append(f"{link}-{count} open {match_word}")

        return "\n".join(summary_lines)