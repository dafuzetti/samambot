import pandas as pd

from classes.Players import Players

class Matches:
    COL_PLAYER_A = "P-A"
    COL_WINS_A = "W-A"
    COL_PLAYER_B = "P-B"
    COL_WINS_B = "W-B"

    MATCH_COLUMNS = [COL_PLAYER_A, COL_WINS_A, COL_PLAYER_B, COL_WINS_B]

    def __init__(self, data=None):
        self.df = pd.DataFrame(data or [], columns=self.MATCH_COLUMNS)

    def set_result(self, index, wins_a, wins_b):
        self.df.at[index, self.COL_WINS_A] = wins_a
        self.df.at[index, self.COL_WINS_B] = wins_b

    def get_iterrows(self):
        return self.df.iterrows()

    def len(self):
        return len(self.df)

    def set_matches(self, matches: pd.DataFrame):
        self.df = matches

    def set_match(self, index, wins_a, wins_b):
        self.df.at[index, self.COL_WINS_A] = wins_a
        self.df.at[index, self.COL_WINS_B] = wins_b

    def get_match(self, index):
        return self.df.iloc[index]

    def to_list(self):
        return self.df.values.tolist()

    def __repr__(self):
        return repr(self.df)
    
    def get_players(self) -> Players:

        team_a_players = self.df[self.COL_PLAYER_A].unique()
        team_b_players = self.df[self.COL_PLAYER_B].unique()

        players = Players()

        for player in team_a_players:
            players.add_player(player, 1)

        for player in team_b_players:
            players.add_player(player, 2)

        return players