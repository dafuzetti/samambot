from classes.State import State

class Player:
    COL_PLAYER = 'player'
    COL_TEAM = 'team'
    DUMMY_PREFIX = "Dummy"
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

    def is_dummy(self) -> bool:
        return self.get_mention().startswith(Player.DUMMY_PREFIX)

    def get_name(self) -> str:
        return State.get_player_name(self.get_mention())
    
    def get_id(self) -> int:
        return int(''.join(filter(str.isdigit, self.get_mention())))
    
    def get_mention(self):
        return self.player
    
    def get_team(self):
        return self.team
    
    def __hash__(self):
        return hash(self.get_mention()) 
    
    def __eq__(self, other):
        return isinstance(other, Player) and self.get_mention() == other.get_mention()