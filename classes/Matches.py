from classes.Player import Player
from classes.Match import Match

class Matches:
    def __init__(self, rows=None):
        self.matches = [
            Match(**r)
            for r in rows or []
        ]

    def set_result(self, index, wins_a, wins_b):
        self.matches[index].set_result(wins_a, wins_b)

    def len(self):
        return len(self.matches)

    def get_matches(self, player_id=None) -> list[Match]:
        if player_id is None:
            return self.matches
        return [m for m in self.matches if m.get_player().get_mention() == player_id or m.get_opponent().get_mention() == player_id]

    def set_matches(self, matches):
        self.matches = matches

    def in_event(self, player_tag):
        return any(m.have_player(player_tag) for m in self.matches)

    def get_players(self) -> list[Player]:
        all_players = [p for m in self.matches for p in (m.get_player(), m.get_opponent())]
        return list(dict.fromkeys(all_players))

    def get_match(self, match_id) -> Match:
        for m in self.matches:
            if m.id == match_id:
                return m
        return None
    
    def __repr__(self):
        return repr(self.matches)

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