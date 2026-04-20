import os
import psycopg2
# PostgreSQL 연결 설정
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_PORT = int(os.getenv("DB_PORT", "5432"))

# 데이터베이스 연결 함수
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
    )
    return conn

def insert_data(id,name,created_at,conn):
    cur=conn.cursor()
    cur.execute("INSERT INTO test_table (id,name,created_at) VALUES (%s,%s,%s)",(id, name, created_at))
    conn.commit()
    cur.close()

conn=get_db_connection()
print(conn)
