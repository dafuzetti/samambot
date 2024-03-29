import pandas
import psycopg2
import discord
from urllib.parse import urlparse
from datetime import date
from decouple import config

SQL_INSERT_EVENT = """INSERT INTO event(guild, channel, date, teams, type)
            VALUES(%s, %s, %s, %s, %s) RETURNING id;"""
SQL_UPDATE_EVENT = """UPDATE event SET victory = %s WHERE id = %s;"""
SQL_UPDATE_MOVEEVENT = """UPDATE event SET channel = %s WHERE id = %s AND guild = '%s';"""
SQL_INSERT_TEAMS = """INSERT INTO teams(event, player, team)
            VALUES(%s, %s, %s);"""
SQL_DELETE_TEAMS = """DELETE FROM teams WHERE event = '%s';"""
SQL_DELETE_PLAYER = """DELETE FROM teams WHERE event = '%s' AND PLAYER = %s;"""
SQL_INSERT_MATCH = """INSERT INTO match(event, player, opponent)
            SELECT %s, %s, %s WHERE NOT EXISTS (SELECT id FROM
            match WHERE event = %s AND player = %s and opponent = %s);"""
SQL_UPDATE_MATCH = """UPDATE match SET win = %s, lose = %s 
            WHERE event = %s AND player = %s AND opponent = %s;"""
SQL_PLAYER_VS = """SELECT
                    TE.PLAYER,
                    SUM(WIN) AS MA_WIN,
                    (SELECT COUNT(1) FROM EVENT, TEAMS T1 
                        WHERE 
                            EVENT.ID = T1.EVENT
                        AND T1.TEAM = VICTORY
                        AND T1.PLAYER = %s
	 	                AND EVENT.GUILD = '%s'
                        AND T1.EVENT = (SELECT EVENT FROM TEAMS T2 WHERE T2.EVENT = T1.EVENT AND T2.TEAM != T1.TEAM AND T2.PLAYER = TE.PLAYER)) AS EV_WIN,
                    COUNT(TE.PLAYER) GAMES
                FROM
                    (
                    SELECT PLAYER, CASE WHEN LOSE=2 THEN 1 ELSE 0 END as WIN FROM MATCH, EVENT WHERE OPPONENT = %s AND MATCH.EVENT = EVENT.ID AND EVENT.GUILD = '%s' 
                    union all 
                    SELECT OPPONENT, CASE WHEN WIN=2 THEN 1 ELSE 0 END as WIN FROM MATCH, EVENT WHERE PLAYER = %s AND MATCH.EVENT = EVENT.ID AND EVENT.GUILD = '%s' 
                    ) AS TE 
                GROUP BY PLAYER
                ORDER BY GAMES DESC
                LIMIT 10"""
SQL_TEAM_FORMATION = """UPDATE
                            TEAMS
                        SET
                            TEAM = N_TEAM
                        FROM
                        (SELECT
                            event n_event,
                            player n_PLAYER,
                            CASE WHEN MOD(ROW_NUMBER() OVER (ORDER BY points DESC), 2) = 1 THEN 
                                1 ELSE 
                                2 END AS N_TEAM
                        FROM
                        (SELECT
                            te.player,
                            COALESCE((SELECT
                                            COUNT(1)
                                        FROM 
                                            EVENT,
                                            TEAMS
                                        WHERE
                                            EVENT.ID = TEAMS.EVENT
                                        AND TEAMS.PLAYER = te.PLAYER
                                        AND EVENT.VICTORY = TEAMS.TEAM) , 0) as points,
                            event
                        FROM 
                            TEAMS te
                        WHERE
                            te.EVENT = %s))
                        WHERE
                            EVENT = n_event
                        AND PLAYER = n_PLAYER"""
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


async def send_file(ctx):
    file_path = None
    target_channel = discord.utils.get(
        ctx.guild.channels, name='db')
    with open(file_path, 'rb') as file:
        file_data = discord.File(file)
        await target_channel.send(file=file_data)


def read_player_vs(ctx, player = None):
    conn = None
    rows = None
    if player is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_PLAYER_VS, (player.mention, ctx.guild_id, player.mention, ctx.guild_id, player.mention, ctx.guild_id,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return rows


def read_score(ctx, player = None):
    conn = None
    rows = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """SELECT
                    victory,
                    champs,
                    win,
                    matches,
                    player,
                    ROUND((victory::numeric * 100)/ champs::numeric, 2) event_stat,
                    ROUND((win::numeric * 100)/ matches::numeric, 2) match_stat
                FROM
                (SELECT
                    te.player,
                    COALESCE(SUM(1) filter (where ev.victory = te.team), 0) as victory,
                    count(te.team) as champs,
                    (
                    (SELECT COUNT(ma.id) from MATCH as ma, EVENT evv WHERE ma.EVENT = evv.ID AND evv.GUILD = '%s'AND te.player = ma.player AND ma.win = 2)
                        +
                    (SELECT COUNT(ma.id) from MATCH as ma, EVENT evv WHERE ma.EVENT = evv.ID AND evv.GUILD = '%s' AND te.player = ma.opponent AND ma.lose = 2)
                    ) win,
                    (SELECT COUNT(ma.id) from MATCH as ma, EVENT evv WHERE ma.EVENT = evv.ID AND evv.GUILD = '%s' AND (te.player = ma.player OR  ma.opponent = te.player)) matches,
                    CEIL((SELECT MAX(CT) FROM (SELECT COUNT(event) AS CT from teams, event evv where teams.EVENT = evv.ID AND evv.GUILD = '%s' group by player))/10.0) as treshhold
                FROM 
                    teams as te,
                    event as ev
                WHERE
                    ev.id = te.event
                AND ev.victory IS NOT NULL
                AND ev.guild = '%s'
                AND (%s OR te.player = %s)
                GROUP BY te.player)
                WHERE
                (%s OR champs >= treshhold)
                ORDER BY event_stat DESC, match_stat DESC, champs DESC, matches DESC, player DESC
                LIMIT 20
                """, (ctx.guild_id, ctx.guild_id, ctx.guild_id, ctx.guild_id, ctx.guild_id, (True if player is None else False), (None if player is None else player.mention), (True if player is not None else False),))
        rows = cur.fetchall()
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows


def read_events(ctx, channel=False):
    conn = None
    rows = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        query_events = """SELECT
                            event.id,
                            event.channel,
                            event.date,
                            event.teams,
                            event.type,
                            event.victory,
                            CONCAT('<#', channel, '>') as chanel_tag,
                            (select count(player) from teams where event.id = teams.event) AS players
                        FROM event WHERE guild = '%s' AND """
        if channel:
            query_events = query_events + " channel = '%s' "
        else:
            query_events = query_events + " '%s' IS NOT NULL "
        query_events = query_events + "ORDER BY date;"
        cur.execute(query_events, (ctx.guild_id, ctx.channel_id,))
        rows = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows

def team_formation(ctx):
    conn = None
    event_id = find_event(ctx)
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_TEAM_FORMATION, (event_id,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return event_id

def move_event(ctx, event_id):
    conn = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(SQL_UPDATE_MOVEEVENT, (ctx.channel_id, event_id, ctx.guild_id))
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()

def read_event(ctx, event_id):
    conn = None
    row = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, CONCAT('<#', channel, '>') as chanel_tag, teams, type, victory FROM event WHERE guild = '%s' AND id = '%s'",
                    (ctx.guild_id, event_id))
        row = cur.fetchone()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return row


def find_event(ctx):
    event_id = None
    conn = None
    row = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM event WHERE guild = '%s' AND channel = '%s' AND victory IS NULL ORDER by id",
                    (ctx.guild_id, ctx.channel_id,))
        row = cur.fetchone()
        if row is not None:
            event_id = row[0]
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_id


def new_player(ctx, player_list, same_team=False):
    conn = None
    event_id = find_event(ctx)
    team = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            for player in player_list:
                if player is not None:
                    cur.execute(SQL_DELETE_PLAYER,
                                (event_id, player.mention,))
                    if team is None or not same_team:
                        cur.execute("""SELECT
                                        TEAM,
                                        COUNT(TEAM) CT
                                    FROM
                                        (SELECT TEAM FROM TEAMS WHERE EVENT = %s UNION ALL SELECT 1 UNION ALL SELECT 2)
                                    GROUP BY TEAM
                                    ORDER BY CT, TEAM LIMIT 1""", (event_id,))
                        row = cur.fetchone()
                        team = row[0]
                    cur.execute(SQL_INSERT_TEAMS,
                                (event_id, player.mention, team,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()


def clear_event(ctx):
    conn = None
    event_id = find_event(ctx)
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_DELETE_TEAMS, (event_id,))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return event_id


def update_matches(ctx, player_w, player_l, lose):
    conn = None
    event_id = find_event(ctx)
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


def save_matches(ctx, list, event = None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            for match in list:
                cur.execute(SQL_INSERT_MATCH, (event_id,
                            match[0], match[1], event_id, match[0], match[1],))
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return event_id


def new_event(ctx, teams: int = 2, type: int = 0):
    conn = None
    event_id = None
    event_date = date.today().strftime("%Y%m%d")
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM event WHERE guild = '%s' AND channel = '%s' AND victory IS NULL",
                    (ctx.guild_id, ctx.channel_id,))
        rows = cur.fetchall()
        if len(rows) == 0:
            cur.execute(SQL_INSERT_EVENT, (ctx.guild_id, ctx.channel_id,
                        event_date, teams, type,))
            event_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return event_id


def close_event(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    if event_id is not None:
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
    return event_id


def read_players(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    rows = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """SELECT player, team 
                    FROM teams, event 
                    WHERE 
                    teams.event = event.id
                    and event=%s ORDER BY team, player""", (event_id,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return dataframe_players(rows)


def player_history(ctx):
    conn = None
    rows = None
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            """SELECT 
                    player, 
                    count(team) as event_count
                FROM 
                    teams, 
                    event
                WHERE
                    teams.event = event.id
                and event.guild = '%s'
                GROUP BY player ORDER BY event_count DESC;""", (ctx.guild.id,))
        rows = cur.fetchall()
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows


def read_matches(ctx, event=None):
    event_id = event
    if event_id is None:
        event_id = find_event(ctx)
    conn = None
    rows = None
    if event_id is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(
                """SELECT 
                    player, 
                    COALESCE(win, 0), 
                    opponent, 
                    COALESCE(lose, 0) 
                FROM 
                    match 
                WHERE 
                    event=%s 
                ORDER BY player, opponent""", (event_id,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
    return dataframe_current(rows)


def dataframe_current(list=None):
    if list is None:
        return pandas.DataFrame(columns=['Team A', 'W-A', 'Team B', 'W-B'])
    else:
        return pandas.DataFrame(list, columns=['Team A', 'W-A', 'Team B', 'W-B'])


def dataframe_players(list=None):
    if list is None:
        return pandas.DataFrame(columns=['player', 'team'])
    else:
        return pandas.DataFrame(list, columns=['player', 'team'])
