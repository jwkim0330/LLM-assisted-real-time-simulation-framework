"""
데이터베이스 연결 설정을 관리하는 설정 파일입니다.
환경 변수에서 값을 읽어옵니다. .env 파일을 참고하세요.
"""
import os

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', ''),
    'user': os.getenv('DB_USER', ''),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', ''),
    'port': os.getenv('DB_PORT', '5432')
}

