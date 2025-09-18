import psycopg2
from psycopg2 import OperationalError

PG_CONNECTION_STRING = "postgresql://postgres:password@localhost:5432/fraud_detection"

def test_postgres_connection():
    try:
        conn = psycopg2.connect(PG_CONNECTION_STRING)
        print("Postgres connection successful!")
        conn.close()
    except OperationalError as e:
        print(f"Postgres connection failed: {e}")

if __name__ == "__main__":
    test_postgres_connection()
