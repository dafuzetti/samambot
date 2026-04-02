from datetime import date

class Sql_Event:

    @staticmethod
    def read_event(cursor, guild, channel, event_id):
        query = """
            SELECT id, type, victory 
            FROM event 
            WHERE guild = %s
            AND channel = %s
            AND id = %s
        """
        cursor.execute(query, (str(guild), str(channel), event_id))
        return cursor.fetchone()

    @staticmethod
    def find_event(cursor, guild, channel):
        query = """
            SELECT id, type, victory 
            FROM event 
            WHERE  guild = %s
            AND channel = %s
            AND victory IS NULL
            ORDER BY id
        """
        cursor.execute(query, (str(guild), str(channel),))
        return cursor.fetchone()
    
    @staticmethod
    def create_event(cursor, guild, channel, category, event_type):
        event_date = date.today().strftime("%Y%m%d")
        query = """
            WITH input AS (
                SELECT  %s::text AS guild,
                        %s::text AS channel,
                        %s::text AS category,
                        %s::int4 AS event_date,
                        %s::int4 AS event_type
            ),
            max_count AS (
                SELECT COALESCE(COUNT(sequence), 0) + 1 AS next_count
                FROM event, input
                WHERE event.guild = input.guild
                AND (event.category = input.category OR (event.category IS NULL AND input.category IS NULL))
            )
            INSERT INTO event (guild, channel, category, date, type, sequence)
            SELECT guild, channel, category, event_date, event_type, next_count
            FROM input, max_count
            RETURNING id;
        """

        cursor.execute(query, (guild, channel, category, event_date, event_type))

        row = cursor.fetchone()
        return row[0] if row else None

    @staticmethod
    def move_event(cursor, guild, new_channel, new_category, event_id):
        query = """
            UPDATE event 
            SET channel = %s,
                category = %s
            WHERE id = %s 
            AND guild = %s
            AND victory IS NULL;
        """
        cursor.execute(query, (str(new_channel), str(new_category), event_id, str(guild)))
        return cursor.rowcount

    @staticmethod
    def set_winning_team(cursor, guild, channel, event_id, winning_team):
        query = """
            UPDATE event SET victory = %s 
            WHERE guild = %s
            AND channel = %s
            AND id = %s
        """
        cursor.execute(query, (winning_team, str(guild), str(channel), event_id,))
        return cursor.rowcount

    @staticmethod
    def get_winners_to_close(cursor, event_id):
        query = """
            WITH base AS (
                SELECT %s::bigint AS event_id
            )
            SELECT
                TEAM
            FROM (
                SELECT
                    T1.TEAM AS TEAM,
                    M.WIN,
                    M.LOSE
                FROM match M
                JOIN base b ON M.EVENT = b.event_id
                JOIN teams T1 ON T1.EVENT = M.EVENT AND T1.PLAYER = M.PLAYER
                JOIN teams T2 ON T2.EVENT = M.EVENT AND T2.PLAYER = M.OPPONENT

                UNION

                SELECT
                    T2.TEAM AS TEAM,
                    M.LOSE AS WIN,
                    M.WIN AS LOSE
                FROM match M
                JOIN base b ON M.EVENT = b.event_id
                JOIN teams T1 ON T1.EVENT = M.EVENT AND T1.PLAYER = M.PLAYER
                JOIN teams T2 ON T2.EVENT = M.EVENT AND T2.PLAYER = M.OPPONENT
            ) t
            GROUP BY TEAM
            ORDER BY SUM(CASE WHEN WIN = 2 THEN 1 ELSE 0 END) DESC,
                    SUM(CASE WHEN LOSE = 0 THEN 1 ELSE 0 END) DESC
            FETCH FIRST 1 ROW WITH TIES;
        """
        cursor.execute(query, (event_id,))
        return cursor.fetchall()