from classes.Matches import Matches
from classes.Players import Players

class Event:
    def __init__(self, guild_id, channel_id, event_id=None, matches: Matches=None, type = 2, victory=None):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.type = type
        self.event_id = event_id
        self.matches = matches
        self.victory = victory
        
    def load(self):
        return
    
    def refresh(self):
        self.load()

    def get_id(self):
        return self.event_id

    def get_victory(self):
        return self.victory 

    def __repr__(self):
        return f"<Event id={self.channel_id}>"

    def set_matches(self, matches: Matches):
        self.matches = matches

    def get_players(self) -> Players:
        return self.matches.get_players()
    
    def get_channel_tag(self):
        return f"<#{self.channel_id}>"
    
    def set_match_by_winner(self, winner_tag, loser_tag, game_loss):
        if self.matches is None:
            return None
        return self.matches.set_match_by_winner(winner_tag, loser_tag, game_loss)
    
    def get_match(self, match_id):
        if self.matches is None:
            return None
        return self.matches.get_match(match_id)

    def get_matches(self, player_tag=None):
        if self.matches is None:
            return []
        return self.matches.get_matches(player_tag)