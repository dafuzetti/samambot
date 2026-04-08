
import db.db_conn as db
import psycopg2
class Sql_Log:

    @staticmethod
    def log(guild, channel, player, command, call):
        query = """
            INSERT INTO log(guild, channel, player, command, call)
            VALUES (%s, %s, %s, %s, %s)
        """
        conn = None
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                cur.execute(query, (str(guild), str(channel), str(player), str(command), str(call),))
            conn.commit()
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()