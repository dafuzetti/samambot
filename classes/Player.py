from classes.State import State

class Player:
    COL_PLAYER = 'player'
    COL_TEAM = 'team'
    DUMMY_PREFIX = "Dummy"
    PLAYER_COLUMNS = [COL_PLAYER, COL_TEAM]
    TEAM_MAP= {
        1: "A",
        2: "B"
    }

    def __init__(self, player_tag: str, team: int):
        self.player = player_tag
        self.team = team

    def __repr__(self):
        return f"{self.get_name()} ({self.get_team_name()})"
    
    def __str__(self):
        if self.get_name() != self.get_mention():
            return f"{self.get_name()}{self.get_mention()} ({self.get_team_name()})"
        else:
            return f"{self.get_mention()} Team:{self.get_team_name()}"

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
    
    def get_team_name(self):
        return Player.TEAM_MAP.get(self.get_team(), self.get_team())
    
    def __hash__(self):
        return hash(self.get_mention()) 
    
    def __eq__(self, other):
        return isinstance(other, Player) and self.get_mention() == other.get_mention()