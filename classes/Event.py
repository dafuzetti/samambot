from classes.Matches import Matches
from classes.Players import Players

class Event:
    def __init__(self, guild_id, channel_id, event_id=None, matches: Matches=None, teams=2, victory=None):
        self.guild_id = guild_id
        self.channel_id = channel_id

        self.event_id = event_id
        self.matches = matches
        self.teams = teams
        self.victory = victory
        
    def load(self):
        return
    
    def refresh(self):
        self.load()

    def get_iterrows(self):
        return self.matches.get_iterrows()

    def __repr__(self):
        return f"<Event id={self.channel_id}>"

    def set_matches(self, matches: Matches):
        self.matches = matches

    def get_players(self) -> Players:
        return self.matches.get_players()
    
    def get_channel_tag(self):
        return f"<#{self.channel_id}>"