class Match:
    COL_PLAYER_A = "P-A"
    COL_WINS_A = "W-A"
    COL_PLAYER_B = "P-B"
    COL_WINS_B = "W-B"
    MATCH_COLUMNS = [COL_PLAYER_A, COL_WINS_A, COL_PLAYER_B, COL_WINS_B]
    RESULTS = ["2x0", "2x1", "1x2", "0x2"]

    def __init__(self, id: int, player_a: str, player_b: str, wins_a: int = 0 , wins_b: int = 0):
        self.id = id
        self.player_a = player_a
        self.player_a_name = player_a
        self.wins_a = wins_a
        self.player_b = player_b
        self.player_b_name = player_b
        self.wins_b = wins_b

    def set_result(self, wins_a, wins_b):
        self.wins_a = wins_a
        self.wins_b = wins_b

    def get_player(self):
        return self.player_a

    def get_opponent(self):
        return self.player_b

    def get_wins(self):
        return self.wins_a
    
    def get_losses(self):
        return self.wins_b

    def set_wins(self, wins):
        self.wins_a = wins

    def set_losses(self, losses):
        self.wins_b = losses

    def set_names(self, player_a_name, player_b_name):
        self.player_a_name = player_a_name
        self.player_b_name = player_b_name

    def get_vs_label(self, player_tag):
        if self.wins_a == 0 and self.wins_b == 0:
            if player_tag == self.player_a:
                    return f"{self.player_b_name}"
            elif player_tag == self.player_b:
                    return f"{self.player_a_name}"
            else:
                return f"{self.player_a_name} vs {self.player_b_name}"
        else:
            return f"{self.player_a_name} {self.wins_a}-{self.wins_b} {self.player_b_name}"
    
    def get_id(self):
        return self.id

    def __repr__(self):
        return f"{self.player_a} ({self.wins_a}) vs {self.player_b} ({self.wins_b})"
    
    def __str__(self):
        return f"{self.player_a} ({self.wins_a}) vs {self.player_b} ({self.wins_b})"