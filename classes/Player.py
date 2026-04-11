class Player:
    PLAYER = 'player'
    TEAM = 'team'
    PLAYER_COLUMNS = [PLAYER, TEAM]

    def __init__(self, player: str, team: int, name=None):
        self.player = player
        self.name = name if name else player
        self.team = team

    def __repr__(self):
        return f"{self.player} ({self.team})"
    
    def __str__(self):
        if self.name != self.player:
            return f"{self.name}{self.player} ({self.team})"
        else:
            return f"{self.player} ({self.team})"

    
    def get_mention(self):
        return self.player