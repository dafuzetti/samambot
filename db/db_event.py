import pandas
import psycopg2
from urllib.parse import urlparse
from datetime import date
from decouple import config
from classes.Matches import Matches
from classes.Players import Players
from classes.Event import Event

SQL_INSERT_EVENT = """INSERT INTO event(guild, channel, date, teams, type)
            VALUES(%s, %s, %s, %s, %s) RETURNING id;"""
SQL_UPDATE_EVENT = """UPDATE event SET victory = %s WHERE id = %s;"""
SQL_UPDATE_MOVEEVENT = """UPDATE event SET channel = %s WHERE id = %s AND guild = '%s' AND victory IS NULL;"""
SQL_INSERT_TEAMS = """INSERT INTO teams(event, player, team)
            VALUES(%s, %s, %s);"""
SQL_INSERT_MATCH = """INSERT INTO match(event, player, opponent)
            SELECT %s, %s, %s WHERE NOT EXISTS (SELECT id FROM
            match WHERE event = %s AND player = %s and opponent = %s);"""
SQL_UPDATE_MATCH = """UPDATE match SET win = %s, lose = %s 
            WHERE event = %s AND player = %s AND opponent = %s AND (select victory from event where id=match.event) is NULL;"""

env = config("ENV")
db_key = config("DB_KEY")


def get_conn():
    database_url = 'postgres://postgres:' + db_key + \
        '@roundhouse.proxy.rlwy.net:13681/railway'
    if env == "TES":
        database_url = 'postgres://postgres:' + db_key + \
            '@roundhouse.proxy.rlwy.net:13681/railway'
    elif env == "PRO":
        database_url = 'postgres://postgres:' + db_key + \
            '@viaduct.proxy.rlwy.net:29301/railway'
    url = urlparse(database_url)
    connection = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return connection


def move_event(ctx_guild, ctx_channel, event_id) -> Event:
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(SQL_UPDATE_MOVEEVENT, (ctx_channel, event_id, ctx_guild))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return read_event(ctx_guild, ctx_channel, event_id)


def read_event(ctx_guild, ctx_channel, event_id) -> Event:
    event_data = None
    conn = None
    row = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, teams, victory FROM event WHERE  guild = '%s' AND id = '%s'",
                    (ctx_guild, event_id))
        row = cur.fetchone()
        if row is not None:
            matches = read_matches(row[0])
            event_data = Event(ctx_guild, ctx_channel, event_id=row[0], matches=matches, teams=row[1], victory=row[2])
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_data


def find_event(ctx_guild, ctx_channel) -> Event:
    event_data = None
    conn = None
    row = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, teams, victory FROM " \
                    " event WHERE guild = '%s' AND channel = '%s' AND victory IS NULL ORDER by id",
                    (ctx_guild, ctx_channel,))
        row = cur.fetchone()
        if row is not None:
            matches = read_matches(row[0])
            event_data = Event(ctx_guild, ctx_channel, event_id=row[0], matches=matches, teams=row[1], victory=row[2])
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_data


def update_matches(ctx_guild, ctx_channel, event_id, player_w, player_l, lose) -> Event:
    conn = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            updates = cur.execute(
                SQL_UPDATE_MATCH, (2, lose, event_id, player_w, player_l,))
            if updates is None:
                cur.execute(SQL_UPDATE_MATCH,
                            (lose, 2, event_id, player_l, player_w,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return read_event(ctx_guild, ctx_channel, event_id)


def read_matches(event=None) -> Matches:
    conn = None
    rows = None

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            """SELECT 
                player, 
                COALESCE(win, 0), 
                opponent, 
                COALESCE(lose, 0) 
            FROM match 
            WHERE event=%s 
            ORDER BY player, opponent""",
            (event,)
        )

        rows = cur.fetchall()
        cur.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    finally:
        if conn is not None:
            conn.close()

    return Matches(rows)


def close_event(ctx_guild, ctx_channel, event_id) -> Event:
    event_content = None
    conn = None

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """SELECT
                    EVENT,
                    TEAM,
                    COALESCE(SUM(1) filter (where WIN = 2), 0) as WIN,
                    COALESCE(SUM(1) filter (where LOSE = 0), 0) as LOS
                FROM(
                    SELECT
                        M.ID,
                        M.EVENT,
                        M.PLAYER PLAYER,
                        T1.TEAM TEAM,
                        M.WIN,
                        M.LOSE
                    FROM
                        match as M,
                        TEAMS AS T1,
                        TEAMS AS T2
                    WHERE
                        M.EVENT = T1.EVENT
                    AND M.EVENT = T2.EVENT
                    AND M.EVENT = %s
                    AND T1.PLAYER = M.PLAYER
                    AND T2.PLAYER = M.OPPONENT
                    union
                    SELECT
                        M.ID,
                        M.EVENT,
                        M.OPPONENT PLAYER,
                        T2.TEAM TEAM,
                        M.LOSE,
                        M.WIN
                    FROM
                        match as M,
                        TEAMS AS T1,
                        TEAMS AS T2
                    WHERE
                        M.EVENT = T1.EVENT
                    AND M.EVENT = T2.EVENT
                    AND M.EVENT = %s
                    AND T1.PLAYER = M.PLAYER
                    AND T2.PLAYER = M.OPPONENT
                )GROUP BY EVENT, TEAM
                ORDER BY WIN desc, LOS desc
                FETCH FIRST 1 ROW WITH TIES;""", (event_id, event_id,))
        rows = cur.fetchall()
        if rows is not None:
            i = 0
            for row in rows:
                i = i + 1
                if i == 1:
                    cur.execute(SQL_UPDATE_EVENT, (row[1], row[0],))
                elif i == 2:
                    cur.execute(SQL_UPDATE_EVENT, (0, row[0],))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return read_event(ctx_guild, ctx_channel, event_id)


def create_event(ctx_guild, ctx_channel, players:Players) -> Event:
    ret = None
    try:
        event_id = new_event(ctx_guild, ctx_channel)
        new_team(ctx_guild, ctx_channel, event_id, players.get_team(1), True)
        new_team(ctx_guild, ctx_channel, event_id, players.get_team(2), False)
        save_matches(ctx_guild, ctx_channel, event_id, players.generate_matches())
        ret = read_event(ctx_guild, ctx_channel, event_id)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)

    return ret


def new_event(ctx_guild, ctx_channel, teams: int = 2, type: int = 0):
    conn = None
    event_id = None
    event_date = date.today().strftime("%Y%m%d")

    try:
        conn = get_conn()
        cur = conn.cursor()

        cur.execute(
            "SELECT 1 FROM event WHERE guild = %s AND channel = %s AND victory IS NULL",
            (str(ctx_guild), str(ctx_channel))
        )

        if cur.fetchone() is None:
            cur.execute(
                "INSERT INTO event (guild, channel, date, teams, type) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (str(ctx_guild), str(ctx_channel), event_date, teams, type)
            )
            event_id = cur.fetchone()[0]

        conn.commit()
        cur.close()

    except Exception as error:
        print(error)

    finally:
        if conn is not None:
            conn.close()

    return event_id


def new_team(ctx_guild, ctx_channel, event_id, player_list, team_A: bool = True):
    conn = None
    if team_A:
        team_id = 1
    else:
        team_id = 2
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            for player in player_list:
                if player is not None:
                    cur.execute(SQL_INSERT_TEAMS,
                                (event_id, player, team_id,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()


def save_matches(ctx_guild, ctx_channel, event, list):
    event_id = event
    conn = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            for match in list:
                bind_vars = (event_id, match[0], match[1], event_id, match[0], match[1],)
                result = cur.execute(SQL_INSERT_MATCH, bind_vars)
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()