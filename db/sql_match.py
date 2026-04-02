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
    def read_matches_by_event(cursor, event_id):
        query = """
            SELECT
                id,
                player, 
                opponent, 
                COALESCE(win, 0), 
                COALESCE(lose, 0) 
            FROM match 
            WHERE event=%s 
            ORDER BY player, opponent       
        """
        cursor.execute(query, (event_id,))
        return cursor.fetchall()