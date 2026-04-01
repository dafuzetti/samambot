from classes.Match import Match

class Matches:
    def __init__(self, rows=None):
        self.matches = [
            Match(r[0], r[1], r[2], r[3], r[4])
            for r in rows or []
        ]

    def set_result(self, index, wins_a, wins_b):
        self.matches[index].set_result(wins_a, wins_b)

    def len(self):
        return len(self.matches)

    def get_matches(self):
        return self.matches

    def set_matches(self, matches):
        self.matches = matches

    def get_match(self, match_id):
        for m in self.matches:
            if m.id == match_id:
                return m
        return None
    
    def __repr__(self):
        return repr(self.matches)

    def set_match_by_winner(self, winner_tag, loser_tag, game_loss) -> Match:
        for m in self.matches:
            if isinstance(m, Match):
                if {m.get_player(), m.get_opponent()} == {winner_tag, loser_tag}:
                    if m.get_player() == winner_tag:
                        m.set_wins(2)
                        m.set_losses(0 if game_loss == 0 else 1)
                    else:
                        m.set_wins(0 if game_loss == 0 else 1)
                        m.set_losses(2)
                    return self.get_match(m.get_id())
        return None