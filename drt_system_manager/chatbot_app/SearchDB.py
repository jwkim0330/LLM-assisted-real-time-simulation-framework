# DB를 이용
import os
import psycopg2
from psycopg2 import sql

# 접근 가능한 칼럼
ALLOWED_COLUMNS = {
    "currenttime",
    "shuttle_id",
    "shuttle_state",
    "cur_dst",
    "cur_node",
    "cur_path",
    "cur_psgr",
    "cur_psgr_num"
}

# Database 연결
DB_DSN = os.getenv("DB_DSN", "")


# input 예시 {'shuttle_id': 'SHUTTLE0005', 'select_column': 'cur_node'}
def find_DB(a, b):
    select_columns = b

    # 2) 화이트리스트 검증
    invalid = [c for c in select_columns if c not in ALLOWED_COLUMNS]
    if invalid:
        raise ValueError(f"허용되지 않은 컬럼 이름: {invalid}")

    # 3) DB 연결
    conn = psycopg2.connect(DB_DSN)
    try:
        with conn.cursor() as cur:
            # 4) SQL 조립: select_columns 리스트를 Identifier로 안전하게 변환
            fields = sql.SQL(",").join(sql.Identifier(col) for col in select_columns)
            print("fields:",fields)
            
            query = sql.SQL("""
                SELECT {fields}
                FROM vehicle_kpi
                WHERE shuttle_id = %s
            ORDER BY currenttime DESC
                LIMIT 1
            """).format(fields=fields)

            # 5) 실행
            cur.execute(query, (a,))
            row = cur.fetchone()

            # 6) 결과 매핑
            if not row:
                return {}

            # select_columns 순서대로 값 매핑
            result = dict(zip(select_columns, row))
            print("매핑결과 확인:", result, type(result))
            return result


    finally:
        conn.close()
