class Sql_Report:

    @staticmethod
    def open_matches(cursor, guild, user):
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
        cursor.execute(query, (str(guild), str(user),))
        return cursor.fetchall()
