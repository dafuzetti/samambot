class Player:
    PLAYER = 'player'
    TEAM = 'team'
    PLAYER_COLUMNS = [PLAYER, TEAM]

    def __init__(self, player: str, team: int):
        self.player = player
        self.team = team

    def __repr__(self):
        return f"{self.player} ({self.team})"
    
    def __str__(self):
        return f"{self.player} ({self.team})"
    
    def get_mention(self):
        return self.player