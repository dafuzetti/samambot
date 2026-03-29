import pandas as pd

class Players:
    PLAYER = 'player'
    TEAM = 'team'
    PLAYER_COLUMNS = [PLAYER, TEAM]

    def __init__(self, data=None):
        self.df = pd.DataFrame(data or [], columns=self.PLAYER_COLUMNS)

    def get_team(self, team):
        return self.df[self.df[self.TEAM] == team][self.PLAYER].tolist()

    def add_player(self, player, team):
        self.df = self.df.append({self.PLAYER: player, self.TEAM: team}, ignore_index=True)

    def add_players(self, players, team):
        for p in players:
            self.df.loc[len(self.df)] = [p, team]

    def set_players(self, players: pd.DataFrame):
        self.df = players

    def len(self):
        return len(self.df)

    def to_list(self):
        return self.df.values.tolist()

    def __repr__(self):
        return repr(self.df)
    
    def generate_matches(self):
        matches = []

        teams = self.df.groupby(self.TEAM)

        team_dict = {
            team: group['player'].tolist()
            for team, group in teams
        }

        team_ids = list(team_dict.keys())

        for i in range(len(team_ids)):
            for j in range(i + 1, len(team_ids)):
                team_a = team_dict[team_ids[i]]
                team_b = team_dict[team_ids[j]]

                for p1 in team_a:
                    for p2 in team_b:
                        matches.append([p1, p2])

        return matches