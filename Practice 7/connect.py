import psycopg2
from config import load_config

def get_connection():
    """ Connect to the PostgreSQL database server """
    config = load_config()
    try:
        conn = psycopg2.connect(**config)
        return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(f"Connection error: {error}")
        return None

if __name__ == '__main__':
    get_connection()