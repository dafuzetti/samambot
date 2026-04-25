from classes.Player import Player

class Match:
    COL_ID = "id"
    COL_PLAYER_A = "player_a"
    COL_TEAM_PLAYER_A = "team_a"
    COL_WINS_A = "wins_a"
    COL_PLAYER_B = "player_b"
    COL_TEAM_PLAYER_B = "team_b"
    COL_WINS_B = "wins_b"

    def __init__(self, id: int, player_a: str, team_a: int, player_b: str, team_b: int, wins_a: int = 0 , wins_b: int = 0):
        self.id = id
        self.player_a = Player(player_tag=player_a, team=team_a)
        self.wins_a = wins_a
        self.player_b = Player(player_tag=player_b, team=team_b)
        self.wins_b = wins_b

    def have_player(self, player_tag):
        return player_tag == self.player_a.get_mention() or player_tag == self.player_b.get_mention()

    def get_player(self) -> Player:
        return self.player_a

    def get_opponent(self) -> Player:
        return self.player_b

    def get_wins(self):
        return self.wins_a
    
    def get_losses(self):
        return self.wins_b

    def set_wins(self, wins):
        self.wins_a = wins

    def set_losses(self, losses):
        self.wins_b = losses

    def get_vs_label(self, player_tag):
        if self.wins_a == 0 and self.wins_b == 0:
            if player_tag == self.player_a.get_mention():
                    return f"{self.player_b.get_name()}"
            elif player_tag == self.player_b.get_mention():
                    return f"{self.player_a.get_name()}"
            else:
                return f"{self.player_a.get_name()} vs {self.player_b.get_name()}"
        else:
            return f"{self.player_a.get_name()} {self.wins_a}-{self.wins_b} {self.player_b.get_name()}"
    
    def get_id(self):
        return self.id

    def __repr__(self):
        return f"{self.player_a.get_name()} ({self.wins_a}) vs ({self.wins_b}) {self.player_b.get_name()}"
    
    def __str__(self):
        if self.wins_a == 0 and self.wins_b == 0:
            return f"○ {self.player_a.get_name()} - {self.player_b.get_name()}"
        return f"● {self.player_a.get_name()} {self.wins_a}-{self.wins_b} {self.player_b.get_name()}"