class Player:
    COL_PLAYER = 'player'
    COL_TEAM = 'team'
    PLAYER_COLUMNS = [COL_PLAYER, COL_TEAM]

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

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name
    
    def get_team(self):
        return self.team
    
    def get_player(self):
        return self.player
    
    def get_mention(self):
        return self.player