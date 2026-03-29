import pandas
import psycopg2
from urllib.parse import urlparse
from datetime import date
from decouple import config
from classes.Matches import Matches
from classes.Players import Players
from classes.Event import Event

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


def read_player_vs(ctx_guild, ctx_channel, player = None):
    conn = None
    rows = None
    if player is not None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            cur.execute(SQL_PLAYER_VS, (player.mention, ctx_guild, player.mention, ctx_guild, player.mention, ctx_guild,))
            rows = cur.fetchall()
            conn.commit()
            cur.close()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return rows


def read_score(ctx_guild, ctx_channel, player = None):
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
                """, (ctx_guild, ctx_guild, ctx_guild, ctx_guild, ctx_guild, (True if player is None else False), (None if player is None else player.mention), (True if player is not None else False),))
        rows = cur.fetchall()
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows


def read_events(ctx_guild, ctx_channel, channel=False):
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
                        FROM event  WHERE guild = '%s' AND """
        if channel:
            query_events = query_events + " channel = '%s' "
        else:
            query_events = query_events + " '%s' IS NOT NULL "
        query_events = query_events + "ORDER BY date;"
        cur.execute(query_events, (ctx_guild, ctx_channel,))
        rows = cur.fetchall()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows


def player_history(ctx_guild, ctx_channel):
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
                GROUP BY player ORDER BY event_count DESC;""", (ctx_guild,))
        rows = cur.fetchall()
        conn.commit()
        cur.close()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    finally:
        if conn is not None:
            conn.close()
    return rows
