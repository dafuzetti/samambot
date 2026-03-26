from asyncio import events

import discord
import discord.ui
import data_base
import functions
import print_embed

class RunningEventView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, events=None, event_id=None, matches=None, event_content=None, players=None):
        super().__init__(timeout=None)
        self.team_a = set()
        self.team_b = set()
        self.message_id = None
        self.guild_id = interaction.guild.id
        self.channel_id = interaction.channel.id
        self.matches = matches
        self.event_content = event_content
        self.event_id = event_id
        self.players = players
        self.events = events
        self.selected_match_index = None
        self.selected_result = None

        match_options = []
        for idx, row in self.matches.iterrows():
            player_a = self.get_member_name(interaction, row['Team A'])
            player_b = self.get_member_name(interaction, row['Team B'])
            label = f"{player_a} vs {player_b}"
            match_options.append(discord.SelectOption(label=label, value=str(idx)))

        self.match_select = discord.ui.Select(
            placeholder="Select a match",
            options=match_options,
            custom_id="select_match"
        )
        self.match_select.callback = self.match_select_callback
        self.add_item(self.match_select)

        # Dropdown 2: select result
        result_options = [
            discord.SelectOption(label="2×0", value="2x0"),
            discord.SelectOption(label="2×1", value="2x1"),
            discord.SelectOption(label="1×2", value="1x2"),
            discord.SelectOption(label="0×2", value="0x2"),
        ]
        self.result_select = discord.ui.Select(
            placeholder="Select result",
            options=result_options,
            custom_id="select_result"
        )
        self.result_select.callback = self.result_select_callback
        self.add_item(self.result_select)

        # Save button
        self.save_button = discord.ui.Button(
            label="Save Result",
            style=discord.ButtonStyle.green,
            custom_id="save_result"
        )
        self.save_button.callback = self.save_callback
        self.add_item(self.save_button)

    def get_member_name(self, interaction: discord.Interaction, user_id: str):
        member = interaction.guild.get_member(int(user_id.replace("<@", "").replace(">", "")))
        if member:
            return member  # or use member.mention for tag
        return f"Unknown ({user_id})"
    
    async def match_select_callback(self, interaction: discord.Interaction):
        self.selected_match_index = int(interaction.data['values'][0])
        await interaction.response.defer()

    async def result_select_callback(self, interaction: discord.Interaction):
        self.selected_result = interaction.data['values'][0]
        await interaction.response.defer()

    async def save_callback(self, interaction: discord.Interaction):
        if self.selected_match_index is None or self.selected_result is None:
            await interaction.response.send_message(
                "You must select a match AND a result!", ephemeral=True
            )
            return

        # Parse result
        row = self.matches.iloc[self.selected_match_index]
        a_wins, b_wins = map(int, self.selected_result.split("x"))
        self.matches.at[self.selected_match_index, 'W-A'] = a_wins
        self.matches.at[self.selected_match_index, 'W-B'] = b_wins

        # Call your external update function to save to DB if needed
        

        # Optionally, update the message embed
        await interaction.response.edit_message(
            embed=self.build_embed(), view=self
        )
    
    def update_buttons(self):
        for item in self.children:
            if item.custom_id == "team_a":
                item.label = f"Win Team A ({len(self.team_a)})"

            if item.custom_id == "team_b":
                item.label = f"Win Team B ({len(self.team_b)})"

    def build_embed(self):
        embed = print_embed.print_event_started(self.matches, self.event_content)
        return embed

    def total_players(self):
        return len(self.team_a) + len(self.team_b)

    async def update_message(self, interaction: discord.Interaction, clean_btns: bool = False):
        msg_id = self.message_id
        await functions.channelnameopen(interaction.channel, self.event_id)

        if msg_id is None:
            return
        channel = interaction.channel
        message = await channel.fetch_message(msg_id)
        view = self
        if clean_btns:
            view.clear_items()
        await message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Close event", style=discord.ButtonStyle.red, custom_id="close_event")
    async def close_event(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Show confirmation popup
        confirm_view = ConfirmCloseView()
        role = discord.utils.get(interaction.guild.roles, name="Samambot Admin")
        if role in interaction.user.roles:
            await interaction.response.send_message(
                "Are you sure you want to close the event?", view=confirm_view, ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "Only users with 'Samambot Admin' role can close events", ephemeral=True
            )

        # Wait until the user clicks Yes/No
        await confirm_view.wait()

        if not confirm_view.confirmed:
            # User canceled
            await interaction.followup.send("Event close canceled.", ephemeral=True)
            return

        # If confirmed, run your original logic
        await interaction.followup.send("Closing event...", ephemeral=True)
        await self.update_message(interaction, clean_btns=True)
        self.events.pop(interaction.channel.id, None)
        data_base.close_event(self.guild_id, self.channel_id, self.event_id)
        self.event_content = data_base.read_event(self.guild_id, self.channel_id, self.event_id)
        await functions.channelnameclose(interaction.channel, self.event_id)
        self.update_buttons()
        await self.update_message(interaction)


class CreatingEventView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, events=None):
        super().__init__(timeout=None)
        self.team_a = set()
        self.team_b = set()
        self.message_id = None
        self.events = events
        self.num_players = [4,6,8]  # Allowed player counts for starting the event

    def total_players(self):
        return len(self.team_a) + len(self.team_b)

    def add_player(self, player: discord.User, team_a: bool = True):
        if player is None:
            return
        if team_a:
            if(len(self.team_a)< 4):  # Assuming a maximum of 4 players per team
                self.team_b.discard(player.id)
                self.team_a.add(player.id)
        else:
            if(len(self.team_b) < 4):  # Assuming a maximum of 4 players per team
                self.team_a.discard(player.id)
                self.team_b.add(player.id)

    def validate_teams(self):
        if self.total_players() in self.num_players and len(self.team_a) == len(self.team_b):
            return False
        return True

    def remove_player(self, player: discord.User):
        self.team_a.discard(player.id)
        self.team_b.discard(player.id)

    def update_buttons(self):
        total = self.total_players()

        for item in self.children:
            if item.custom_id == "start":
                item.disabled = self.validate_teams()

            if item.custom_id == "team_a":
                item.label = f"Join Team A ({len(self.team_a)})"

            if item.custom_id == "team_b":
                item.label = f"Join Team B ({len(self.team_b)})"

    def build_embed(self):
        embed = discord.Embed(title="New Event Lobby")

        team_a = "\n".join(f"<@{u}>" for u in self.team_a) or "—"
        team_b = "\n".join(f"<@{u}>" for u in self.team_b) or "—"

        embed.add_field(name="Team A", value=team_a, inline=True)
        embed.add_field(name="Team B", value=team_b, inline=True)
        embed.set_footer(text=f"Total players: {self.total_players()}")

        return embed

    async def update_message(self, interaction: discord.Interaction, clean_btns: bool = False):
        msg_id = self.message_id
        
        if msg_id is None:
            return
        if clean_btns:
            self.clear_items()
        channel = interaction.channel
        message = await channel.fetch_message(msg_id)

        await message.edit(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Join Team A (0)", style=discord.ButtonStyle.green, custom_id="team_a")
    async def join_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        self.add_player(interaction.user)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Join Team B (0)", style=discord.ButtonStyle.blurple, custom_id="team_b")
    async def join_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        
        self.add_player(interaction.user, team_a=False)
        if interaction.guild.id == 1184558595602391121:  # Only for testing purposes, remove this condition in production
            await interaction.response.defer()
            user: discord.User = interaction.guild.get_member(690644525177110561)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(866339429273305098)
            self.add_player(user, team_a=True)
            user = interaction.guild.get_member(1184558521459671110)
            self.add_player(user, team_a=False)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Drop", style=discord.ButtonStyle.danger, custom_id="drop")
    async def drop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()

        self.remove_player(interaction.user)

        self.update_buttons()
        await self.update_message(interaction)

    @discord.ui.button(label="Start Event", style=discord.ButtonStyle.red, custom_id="start", disabled=True)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.update_message(interaction, clean_btns=True)
        await interaction.response.defer()

        event_id = data_base.new_event(interaction.guild.id, interaction.channel.id)
        data_base.new_team(interaction.guild.id, interaction.channel.id, event_id, self.team_a, True)
        data_base.new_team(interaction.guild.id, interaction.channel.id, event_id, self.team_b, False)

        players = data_base.read_players(interaction.guild.id, interaction.channel.id, event_id)
        functions.start(interaction.guild.id, interaction.channel.id, event_id, players)

        matches = data_base.read_matches(interaction.guild.id, interaction.channel.id, event_id)
        event_content = data_base.read_event(interaction.guild.id, interaction.channel.id, event_id)
        new_view = RunningEventView(
            interaction=interaction,
            events=self.events,
            event_id=event_id,
            matches=matches,
            event_content=event_content,
            players=players
        )
        await functions.channelnameopen(interaction.channel, event_id)

        message = await interaction.followup.send(
            embed=new_view.build_embed(),
            view=new_view
        )

        new_view.message_id = message.id
        self.events[interaction.channel.id] = new_view


class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)  # optional timeout
        self.confirmed = False

        # Yes button
        yes_button = discord.ui.Button(label="Yes", style=discord.ButtonStyle.red)
        yes_button.callback = self.yes_callback
        self.add_item(yes_button)

        # No button
        no_button = discord.ui.Button(label="No", style=discord.ButtonStyle.gray)
        no_button.callback = self.no_callback
        self.add_item(no_button)

    async def yes_callback(self, interaction: discord.Interaction):
        self.confirmed = True
        self.stop()  # stops the view
        await interaction.response.defer()  # we defer because the main button will handle updates

    async def no_callback(self, interaction: discord.Interaction):
        self.confirmed = False
        self.stop()
        await interaction.response.defer()