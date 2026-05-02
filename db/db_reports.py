import psycopg2
import asyncio
from db.sql_log import Sql_Log
from db.sql_report import Sql_Report
import db.db_conn as db

OPEN_MATCHES=Sql_Report.open_matches
PLAYER_HISTORY=Sql_Report.player_history
PLAYER_VS=Sql_Report.player_vs
READ_EVENTS=Sql_Report.read_events
READ_SCORE=Sql_Report.read_score

def read_report(guild, channel, user, report_func, **kwargs):
    if callable(report_func):
        asyncio.create_task(
            asyncio.to_thread(Sql_Log.log, guild, channel, user, report_func.__name__, str(kwargs))
        )
        conn = None
        rows = None
        try:
            conn = db.get_connection()
            with conn.cursor() as cur:
                rows = report_func(cur, guild, channel, user, **kwargs)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                conn.close()
        return rows
    else:
        raise ValueError(f"Report '{report_func.__name__}' not found.")
