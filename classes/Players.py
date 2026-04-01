from classes.Player import Player

class Players:

    def __init__(self, rows=None):        
        self.players = [
            Player(r[0], r[1])
            for r in rows or []
        ]

    def get_team(self, team):
        return [p for p in self.players if p.team == team]

    def get_team_tags(self, team):
        return [p.get_mention() for p in self.players if p.team == team]
    
    def add_player(self, player, team):
        self.players.append(Player(player, team))

    def add_players(self, players, team):
        for p in players:
            self.players.append(Player(p, team))

    def add_teams(self, playersA, playersB):
        for p in playersA:
            self.players.append(Player(p, 1))
        for p in playersB:
            self.players.append(Player(p, 2))

    def len(self):
        return len(self.players)

    def __repr__(self):
        return repr(self.players)
    
    def generate_pairings(self):
        teams = {}

        # group players by team
        for p in self.players:
            teams.setdefault(p.team, []).append(p)

        matches = []

        team_list = list(teams.values())

        # all team pairs
        for i in range(len(team_list)):
            for j in range(i + 1, len(team_list)):
                team_a = team_list[i]
                team_b = team_list[j]

                # all player vs player
                for p1 in team_a:
                    for p2 in team_b:
                        matches.append((p1.get_mention(), p2.get_mention()))

        return matches