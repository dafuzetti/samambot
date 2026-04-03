import psycopg2
import db.db_conn as db
from db.sql_match import Sql_Match
from db.sql_team import Sql_Team
from db.sql_event import Sql_Event
from classes.Matches import Matches
from classes.Players import Players
from classes.Event import Event

def update_matches_from_channel(ctx_guild, ctx_channel, winner_tag, loser_tag, game_loss) -> Event:
    event = find_event(ctx_guild, ctx_channel)
    if event is None:
        return "Event not found.", None
    match_result = event.set_match_by_winner(winner_tag, loser_tag, game_loss)
    if match_result is None:
        return "Match not found.", None

    conn = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            Sql_Match.update_match(
                cur,
                match_result.get_wins(),
                match_result.get_losses(),
                event.event_id,
                match_result.get_player(),
                match_result.get_opponent()
            )
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return "Match updated.", read_event(ctx_guild, ctx_channel, event.event_id)

def update_matches(ctx_guild, ctx_channel, event_id, player, opponent, win, lose) -> Event:
    conn = None
    if event_id is not None:
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                Sql_Match.update_match(cur, win, lose, event_id, player, opponent)
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return read_event(ctx_guild, ctx_channel, event_id)

def read_matches(event_id=None) -> Matches:
    conn = None
    rows = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            rows = Sql_Match.read_matches_by_event(cur, event_id)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return Matches(rows)

def save_matches(event_id, matches):
    if event_id is None:
        return
    conn = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            for match in matches:
                Sql_Match.create_match(
                    cur,
                    event_id,
                    match[0],
                    match[1]
                )
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def new_team(event_id, player_list, team):
    if event_id is None:
        return
    conn = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            for player in player_list:
                if player is not None:
                    Sql_Team.add_player_to_team(cur, event_id, player, team)
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def new_event(guild, channel, event_type: int = 2):
    conn = None
    event_id = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            event_id = Sql_Event.create_event(cur, guild, channel, event_type)
        conn.commit()
    except Exception as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_id

def move_event(guild, new_channel, event_id) -> Event:
    conn = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            updated = Sql_Event.move_event(cur, guild, new_channel, event_id)
        conn.commit()
        if updated == 0:
            return None
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return read_event(guild, new_channel, event_id)

def read_event(guild, channel, event_id) -> Event:
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        row = Sql_Event.read_event(cur, guild, channel, event_id)
        if row is None:
            return None
        matches = read_matches(row[0])
        return Event(
            guild,
            channel,
            event_id=row[0],
            matches=matches,
            type=row[1],
            victory=row[2],
            sequence=row[3]
        )
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return None

def find_event(guild, channel) -> Event:
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        row = Sql_Event.find_event(cur, guild, channel)
        if row is None:
            return None
        matches = read_matches(row[0])
        return Event(
            guild,
            channel,
            event_id=row[0],
            matches=matches,
            type=row[1],
            victory=row[2],
            sequence=row[3]
        )
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return None

def create_event(guild, channel, category, players: Players, event_type = 2) -> Event:
    conn = None
    try:
        conn = db.get_connection()
        with conn.cursor() as cur:
            event_id = Sql_Event.create_event(cur, guild, channel, category, event_type)
            for p in players.get_team_tags(1):
                Sql_Team.add_player_to_team(cur, event_id, p, 1)
            for p in players.get_team_tags(2):
                Sql_Team.add_player_to_team(cur, event_id, p, 2)
            for pair in players.generate_pairings():
                Sql_Match.create_match(cur, event_id, pair[0], pair[1])
        conn.commit()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return read_event(guild, channel, event_id)

def close_event(guild, channel, event_id) -> Event:
    conn = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        rows = Sql_Event.get_winners_to_close(cur, event_id)
        if rows:
            if len(rows) > 1:
                winner = 0
            else:
                winner = rows[0][0]
        Sql_Event.set_winning_team(cur, guild, channel, event_id, winner)
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return read_event(guild, channel, event_id)