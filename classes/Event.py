from classes.Match import Match
from classes.Player import Player

class Event:
    def __init__(self, guild_id, channel_id, event_id=None, matches: list[Match]=None, type = 2, victory=None, sequence=None, message_id=None):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.type = type
        self.event_id = event_id
        self.matches: list[Match] = matches if matches is not None else []
        self.sequence = sequence
        self.victory = victory
        self.message_id = message_id

    def get_id(self):
        return self.event_id

    def get_victory(self):
        return self.victory 

    def __repr__(self):
        return f"<Event id={self.channel_id}>"

    def set_matches(self, matches: list[Match]):
        self.matches = matches if matches is not None else []

    def in_event(self, player_tag):
        return any(m.have_player(player_tag) for m in self.matches)

    def get_players(self) -> list[Player]:
        all_players = [p for m in self.matches for p in (m.get_player(), m.get_opponent())]
        return list(dict.fromkeys(all_players))

    def get_channel_tag(self):
        return f"<#{self.channel_id}>"
    
    def get_event_name(self):
        if self.sequence is None:
            return self.event_id
        return self.sequence

    def set_match_by_winner(self, winner_tag, loser_tag, game_loss) -> Match:
        for m in self.matches:
            if isinstance(m, Match):
                if {m.get_player().get_mention(), m.get_opponent().get_mention()} == {winner_tag, loser_tag}:
                    if m.get_player().get_mention() == winner_tag:
                        m.set_wins(2)
                        m.set_losses(0 if game_loss == 0 else 1)
                    else:
                        m.set_wins(0 if game_loss == 0 else 1)
                        m.set_losses(2)
                    return self.get_match(m.get_id())
        return None
    
    def get_match(self, match_id) -> Match:
        for m in self.matches:
            if m.id == match_id:
                return m
        return None

    def get_matches(self, player_tag=None) -> list[Match]:
        if self.matches is None:
            return []
        if player_tag is None:
            return self.matches
        return [m for m in self.matches if m.get_player().get_mention() == player_tag or m.get_opponent().get_mention() == player_tag]
