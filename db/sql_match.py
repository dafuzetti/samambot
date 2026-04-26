from classes.Match import Match

class Sql_Match:

    @staticmethod
    def create_match(cursor, event_id, player, opponent):
        query = """
            INSERT INTO match(event, player, opponent)
            VALUES (%s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (event_id, player, opponent,))

        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def update_match(cursor, win, lose, event_id, player, opponent):
        query = """
            UPDATE match m
            SET win = %s,
                lose = %s
            FROM event e
            WHERE m.event = e.id
            AND m.event = %s
            AND m.player = %s
            AND m.opponent = %s
            AND e.victory IS NULL;
        """
        cursor.execute(query, (win, lose, event_id, player, opponent,))
        return cursor.rowcount

    @staticmethod
    def read_matches_by_event(cursor, event_id) -> list[Match]:
        query = f"""
            SELECT
                m.id as {Match.COL_ID},
                m.player as {Match.COL_PLAYER_A}, 
                m.opponent as {Match.COL_PLAYER_B}, 
                COALESCE(m.win, 0) as {Match.COL_WINS_A}, 
                COALESCE(m.lose, 0) as {Match.COL_WINS_B},
                t1.team as {Match.COL_TEAM_PLAYER_A},
                t2.team as {Match.COL_TEAM_PLAYER_B}
            FROM match m, teams t1, teams t2
            WHERE m.event=%s 
            AND m.event = t1.event
            AND m.event = t2.event
            AND m.player = t1.player
            AND m.opponent = t2.player

            ORDER BY {Match.COL_PLAYER_A}, {Match.COL_PLAYER_B}
        """
        cursor.execute(query, (event_id,))

        columns = [col[0] for col in cursor.description]

        rows = [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]
        return [Match(**row) for row in rows]