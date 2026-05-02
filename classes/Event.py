from discord import player

from classes.Match import Match
from classes.Player import Player

class Event:
    def __init__(self, guild_id, channel_id, event_id=None, matches: list[Match]=None, type = 2, victory=None, sequence=None, message_id=None):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.type = type
        self.event_id = event_id
        self.matches: list[Match] = matches if matches is not None else []
        self.sequence = sequence
        self.victory = victory
        self.message_id = message_id

    def get_id(self):
        return self.event_id

    def get_victory(self):
        return self.victory 

    def __repr__(self):
        return f"<Event id={self.channel_id}>"

    def have_dummyes(self) -> bool:
        return any(m.have_dummy() for m in self.matches)

    def set_matches(self, matches: list[Match]):
        self.matches = matches if matches is not None else []

    def in_event(self, player_tag):
        return any(m.have_player(player_tag) for m in self.matches)

    def get_players(self, team=None) -> list[Player]:
        all_players = [p for m in self.matches for p in (m.get_player(), m.get_opponent())]
        if team is not None:
            all_players = [p for p in all_players if p.get_team() == team]
        return list(dict.fromkeys(all_players))

    def get_channel_tag(self):
        return f"<#{self.channel_id}>"
    
    def get_event_name(self):
        if self.sequence is None:
            return self.event_id
        return self.sequence

    def set_match_by_winner(self, winner_tag, loser_tag, game_loss) -> Match:
        for m in self.matches:
            if isinstance(m, Match):
                if {m.get_player().get_mention(), m.get_opponent().get_mention()} == {winner_tag, loser_tag}:
                    if m.get_player().get_mention() == winner_tag:
                        m.set_wins(2)
                        m.set_losses(0 if game_loss == 0 else 1)
                    else:
                        m.set_wins(0 if game_loss == 0 else 1)
                        m.set_losses(2)
                    return self.get_match(m.get_id())
        return None
    
    def get_match(self, match_id) -> Match:
        for m in self.matches:
            if m.id == match_id:
                return m
        return None

    def get_matches(self, player_tag=None) -> list[Match]:
        if self.matches is None:
            return []
        if player_tag is None:
            return self.matches
        return [m for m in self.matches if m.get_player().get_mention() == player_tag or m.get_opponent().get_mention() == player_tag]

    def print_matches(self, played:bool=None):
        if played is None:
            return '\n'.join(str(m) for m in self.matches)
        if played:
            return '\n'.join(str(m) for m in self.matches if m.get_wins() == 2 or m.get_losses() == 2)
        else:
            return '\n'.join(str(m) for m in self.matches if not (m.get_wins() == 2 or m.get_losses() == 2))

    def print_players(self, team=None):
        players = self.get_players(team=team)
        prefix = 'Players: '
        if team is not None:
            if self.get_victory() is not None:
                prefix = 'WINNERS: ' if self.get_victory() == team else 'losers:'
        return prefix + ', '.join(self.get_player_stats(p.get_mention()) for p in players)
    
    def get_player_stats(self, player_tag):
        wins = self.get_player_wins(player_tag)
        losses = self.get_player_losses(player_tag)
        if wins == 0 and losses == 0:
            return f"{player_tag}"
        return f"{player_tag} {wins}/{losses}"

    def get_player_wins(self, player_tag):
        return sum(1 for m in self.get_matches(player_tag=player_tag) if (m.get_player().get_mention() == player_tag and m.get_wins() == 2) or (m.get_opponent().get_mention() == player_tag and m.get_losses() == 2))

    def get_player_losses(self, player_tag):
        return sum(1 for m in self.get_matches(player_tag=player_tag) if (m.get_player().get_mention() == player_tag and m.get_losses() == 2) or (m.get_opponent().get_mention() == player_tag and m.get_wins() == 2))

    def get_mvp_players(self) -> list[Player]:
        leaders = []
        for p in self.get_players():
            if not leaders:
                leaders = [p]
            else:
                p_wins = self.get_player_points(p.get_mention())
                leader_wins = self.get_player_points(leaders[0].get_mention())
                if p_wins > leader_wins:
                    leaders = [p]
                elif p_wins == leader_wins:
                    leaders.append(p)
        return leaders

    def get_player_points(self, player_tag):
        points = 0
        for m in self.get_matches(player_tag=player_tag):
            if m.get_player().get_mention() == player_tag:
                points += 100 if m.get_wins() == 2 else m.get_wins()
            else:
                points += 100 if m.get_losses() == 2 else m.get_losses()
        return points

    def get_count_matches(self, played:bool=None):
        if played is None:
            return len(self.matches)
        if played:
            return len([m for m in self.matches if m.get_wins() == 2 or m.get_losses() == 2])
        else:
            return len([m for m in self.matches if not (m.get_wins() == 2 or m.get_losses() == 2)])

    def get_wins(self, team):
        count = 0
        for m in self.matches:
            if m.get_wins() == 2 and m.get_player().get_team() == team:
                count += 1
            elif m.get_losses() == 2 and m.get_opponent().get_team() == team:
                count += 1
        return count
    
    def get_team_emoji(self, team) -> str:
        victory = self.get_victory()
        if victory is None:
            return ''
        if victory == 0:
            return '🍕'
        return '🏆' if str(team) == str(victory) else '💀'