from classes.State import State

class Player:
    COL_PLAYER = 'player'
    COL_TEAM = 'team'
    PLAYER_COLUMNS = [COL_PLAYER, COL_TEAM]

    def __init__(self, player_tag: str, team: int):
        self.player = player_tag
        self.team = team

    def __repr__(self):
        return f"{self.get_name()} ({self.get_team()})"
    
    def __str__(self):
        if self.get_name() != self.get_mention():
            return f"{self.get_name()}{self.get_mention()} ({self.get_team()})"
        else:
            return f"{self.get_mention()} ({self.get_team()})"

    def get_name(self) -> str:
        return State.get_player_name(self.get_mention())
    
    def get_id(self) -> int:
        return int(self.get_mention().strip("<@!>"))
    
    def get_mention(self):
        return self.player
    
    def get_team(self):
        return self.team
    
    def __hash__(self):
        return hash(self.get_mention()) 
    
    def __eq__(self, other):
        return isinstance(other, Player) and self.get_mention() == other.get_mention()