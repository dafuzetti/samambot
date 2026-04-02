class Sql_Team:

    @staticmethod
    def add_player_to_team(cursor, event_id, player, team):
        query = """
            INSERT INTO teams(event, player, team)
            VALUES(%s, %s, %s)
            RETURNING id
        """
        cursor.execute(query, (event_id, player, team,))

        row = cursor.fetchone()
        return row[0] if row else None
