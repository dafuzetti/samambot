class Sql_Report:

    @staticmethod
    def open_matches(cursor, guild, channel, user, report_user):
        query = """
            SELECT 
                player, category, event_id 
            FROM
                (SELECT m.player, m.opponent, COALESCE(e.sequence, e.id) AS event_id, e.category, guild
                FROM match m, event e 
                WHERE
                m.event = e.id
                AND win IS NULL
                AND e.victory IS NULL
                UNION ALL
                SELECT m.opponent as player, m.player as opponent, COALESCE(e.sequence, e.id) AS EVENT_ID, e.category, guild
                FROM match m, event e 
                WHERE
                m.event = e.id
                AND win IS NULL
                AND e.victory IS null)
            WHERE
                    guild = %s
                AND opponent = %s
            ORDER BY PLAYER, CATEGORY, EVENT_ID
        """
        cursor.execute(query, (str(guild), str(report_user),))
        return cursor.fetchall()

    @staticmethod
    def player_history(cursor, guild, channel, user, *args):
        query = """
            SELECT 
                player, 
                count(team) as event_count
            FROM 
                teams, 
                event
            WHERE
                teams.event = event.id
            and event.guild = '%s'
            and player = '%s'
            GROUP BY player ORDER BY event_count DESC;
        """
        cursor.execute(query, (str(guild), str(user),))
        return cursor.fetchall()

    @staticmethod
    def player_vs(cursor, guild, channel, user, opponent):
        query = """
            SELECT
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
            LIMIT 10
        """
        cursor.execute(query, (str(guild), str(user), str(opponent), str(guild), str(user), str(guild)))
        return cursor.fetchall()

    @staticmethod
    def read_score(cursor, guild, channel, user, *args):
        query = """
            SELECT
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
        """
        cursor.execute(query, (str(guild), str(user),))
        return cursor.fetchall()

    @staticmethod
    def read_events(cursor, guild, channel, user, *args):
        query = """
            SELECT
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
            query = query + " channel = '%s' "
        else:
            query = query + " '%s' IS NOT NULL "
        query = query + "ORDER BY date;"
        cursor.execute(query, (str(guild), str(channel)))
        return cursor.fetchall()
