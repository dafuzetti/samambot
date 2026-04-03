import psycopg2
from decouple import config

env = config("ENV")
db_key = config("DB_KEY")

def get_connection():
    database_url = 'postgres://postgres:' + db_key + \
        '@roundhouse.proxy.rlwy.net:13681/railway'
    if env == "TES":
        database_url = 'postgres://postgres:' + db_key + \
            '@roundhouse.proxy.rlwy.net:13681/railway'
    elif env == "PRO":
        database_url = 'postgres://postgres:' + db_key + \
            '@viaduct.proxy.rlwy.net:29301/railway'

    connection = psycopg2.connect(database_url)
    return connection