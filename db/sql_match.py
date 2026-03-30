class Sql_Match:

    @staticmethod
    def create_match(conn, guild_id, channel_id, players):
        query = """
        INSERT INTO matches (guild_id, channel_id, players)
        VALUES (?, ?, ?)
        """
        conn.execute(query, (guild_id, channel_id, players))

    @staticmethod
    def update_match(conn, win, lose, event_id, player, opponent):
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
        with conn.cursor() as cursor:
            cursor.execute(query, (win, lose, event_id, player, opponent))
        conn.commit()