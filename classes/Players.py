from classes.Player import Player

class Players:

    def __init__(self, rows=None):        
        self.players = [
            Player(r[0], r[1])
            for r in rows or []
        ]

    def get_team(self, team):
        return [p for p in self.players if p.team == team]

    def get_players(self, team=None) -> list[Player]:
        return [p for p in self.players if (team is None or p.team == team)]

    def get_players_tags(self, team=None) -> list[str]:
        return [p.get_tag() for p in self.players if (team is None or p.team == team)]

    def get_players_names(self, team=None) -> list[str]:
        return [p.get_name() for p in self.players if (team is None or p.team == team)]
    
    def get_ready(self):
        return (
            self.len() in (4, 6, 8)
            and len(self.get_players_tags(1)) == len(self.get_players_tags(2))
        )

    def add_player(self, player_tag, team, name=None):
        self.remove_player_tag(player_tag)
        if(self.len() < 8 and len(self.get_players_tags(team)) < 4):
            self.players.append(Player(player_tag=player_tag, team=team, name=name))

    def remove_player_tag(self, player_tag):
        for p in self.players:
            player = p if p.get_mention() == player_tag else None
            if player:
                self.players.remove(player)
                return True
        return False

    def add_players(self, players_tags, team):
        for p in players_tags:
            self.add_player(p, team)

    def add_teams(self, playersA, playersB):
        self.add_players(playersA, 1)
        self.add_players(playersB, 2)

    def len(self):
        return len(self.players)

    def __repr__(self):
        return repr(self.players)
    
    def __str__(self):
        return ", ".join(str(p) for p in self.players)
    
    def generate_pairings(self):
        teams = {}

        # group players by team
        for p in self.players:
            teams.setdefault(p.team, []).append(p)

        pairings = []

        team_list = list(teams.values())

        # all team pairs
        for i in range(len(team_list)):
            for j in range(i + 1, len(team_list)):
                team_a = team_list[i]
                team_b = team_list[j]

                # all player vs player
                for p1 in team_a:
                    for p2 in team_b:
                        pairings.append((p1.get_mention(), p2.get_mention()))

        return pairings