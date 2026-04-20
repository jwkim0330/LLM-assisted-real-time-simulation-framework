import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from SearchDB import find_DB
import pandas as pd
import psycopg2
from config import DB_CONFIG
import json
import csv
import re

# 노드 매핑 딕셔너리 초기화
node_mapping = {}
try:
    with open('JSON/cor_node.csv', 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'id' in row and 'NODE_NAME' in row:
                node_mapping[row['id']] = row['NODE_NAME']
except Exception as e:
    print(f"Error reading node mapping file: {e}")
    node_mapping = {}

def replace_node_ids(text):
    """텍스트에서 노드 ID를 노드 이름으로 변환"""
    if not text:
        return text
    
    # 노드 ID 패턴 찾기 (예: 'cur_node': '0196' 또는 'cur_node': '0196')
    pattern = r"'cur_node':\s*['\"](\d+)['\"]"
    
    def replace_match(match):
        node_id = match.group(1)
        # 앞의 0을 제거
        node_id = node_id.lstrip('0')
        # 모든 0이 제거된 경우 '0'으로 처리
        if not node_id:
            node_id = '0'
        return f"'cur_node': '{node_mapping.get(node_id, node_id)}'"
    
    return re.sub(pattern, replace_match, text)

def convert_path_nodes(path_str):
    """경로 문자열의 노드 ID들을 노드 이름으로 변환"""
    if not path_str or not isinstance(path_str, str):
        return path_str
    
    # 문자열에서 노드 ID 리스트 추출
    import ast
    try:
        node_ids = ast.literal_eval(path_str)
        # 각 노드 ID를 노드 이름으로 변환
        node_names = []
        for node_id in node_ids:
            # 앞의 0을 제거
            clean_id = str(node_id).lstrip('0')
            if not clean_id:
                clean_id = '0'
            node_names.append(node_mapping.get(clean_id, node_id))
        return str(node_names)
    except:
        return path_str

def search_DB(**kwargs):
    print("search_DB에 들어온 내용: ",kwargs)
    # find_DB()를 통해 필요한 DB 데이터 조회
    answer = find_DB(kwargs["shuttle_id"],kwargs["select_columns"])
    print("\n","answer:",answer,"\n")
    
    # 노드 ID를 노드 이름으로 변환
    if isinstance(answer, str):
        answer = replace_node_ids(answer)
    elif isinstance(answer, list):
        answer = [replace_node_ids(item) if isinstance(item, str) else item for item in answer]
    elif isinstance(answer, dict):
        # cur_path 처리
        if 'cur_path' in answer:
            answer['cur_path'] = convert_path_nodes(answer['cur_path'])
        # cur_node 처리
        if 'cur_node' in answer:
            node_id = str(answer['cur_node'])
            # 앞의 0을 제거
            node_id = node_id.lstrip('0')
            # 모든 0이 제거된 경우 '0'으로 처리
            if not node_id:
                node_id = '0'
            answer['cur_node'] = node_mapping.get(node_id, node_id)
        # 다른 문자열 값들도 변환
        for key, value in answer.items():
            if isinstance(value, str):
                answer[key] = replace_node_ids(value)
    
    return answer

# 승객들의 평균 대기시간을 계산
def calculate_passenger_avg_waiting_time(**kwargs):
    try:
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # passengers_kpi 테이블에서 데이터 조회
        cur.execute("""
            SELECT 
                boardingtime,
                waitstarttime
            FROM passengers_kpi
            WHERE boardingtime IS NOT NULL 
            AND waitstarttime IS NOT NULL
            AND success = 'True'
        """)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        # DataFrame 생성
        df = pd.DataFrame(rows, columns=cols)
    
        if df.empty:
            return 0.0
        
        # 문자열을 float로 변환
        df['boardingtime'] = pd.to_numeric(df['boardingtime'], errors='coerce')
        df['waitstarttime'] = pd.to_numeric(df['waitstarttime'], errors='coerce')
        
        # 결측치 제거
        df = df.dropna(subset=['boardingtime', 'waitstarttime'])
        
        # 대기시간 계산 (boardingtime - waitstarttime)
        df['waiting_time'] = df['boardingtime'] - df['waitstarttime']
        # 평균 대기시간 계산
        avg_wait = df['waiting_time'].mean()
        
        return "system 시간으로 승객의 평균 대기시간은 "+str(avg_wait)+"초 입니다."
        
    except Exception as e:
        print(f"Error calculating average waiting time: {e}")
        return 0.0
        
    finally:
        # DB 연결 종료
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# 예측 대기 시간과 실제 대기 시간의 평균 오차
def calculate_prediction_error(**kwargs):
    try:
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # passengers_kpi 테이블에서 데이터 조회
        cur.execute("""
            SELECT 
                boardingtime,
                waitstarttime,
                expectedwaitingtime
            FROM passengers_kpi
            WHERE boardingtime IS NOT NULL 
            AND waitstarttime IS NOT NULL
            AND expectedwaitingtime IS NOT NULL
            AND success = 'True'
        """)
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        
        # DataFrame 생성
        df = pd.DataFrame(rows, columns=cols)
    
        if df.empty:
            return "데이터가 없습니다."
        
        # 문자열을 float로 변환
        df['boardingtime'] = pd.to_numeric(df['boardingtime'], errors='coerce')
        df['waitstarttime'] = pd.to_numeric(df['waitstarttime'], errors='coerce')
        df['expectedwaitingtime'] = pd.to_numeric(df['expectedwaitingtime'], errors='coerce')
        
        # 결측치 제거
        df = df.dropna(subset=['boardingtime', 'waitstarttime', 'expectedwaitingtime'])
        
        # 실제 대기시간 계산
        df['actual_waiting_time'] = df['boardingtime'] - df['waitstarttime']
        
        # 예측 오차 계산 (절대값)
        df['prediction_error'] = abs(df['expectedwaitingtime'] - df['actual_waiting_time'])
        
        # 평균 예측 오차 계산
        avg_error = df['prediction_error'].mean()
        
        return f"예측 대기 시간과 실제 대기 시간의 평균 오차는 {avg_error:.2f}초 입니다."
        
    except Exception as e:
        print(f"Error calculating prediction error: {e}")
        return "예측 오차 계산 중 오류가 발생했습니다."
        
    finally:
        # DB 연결 종료
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# 승객의 탑승 성공률 계산
def calculate_boarding_success_rate(**kwargs):

    try:
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 전체 승객 수 조회
        cur.execute("""
            SELECT COUNT(*) 
            FROM passengers_kpi
        """)
        total_passengers = cur.fetchone()[0]
        print("total_passengers:",total_passengers)
        # 성공적으로 탑승한 승객 수 조회
        cur.execute("""
            SELECT COUNT(*) 
            FROM passengers_kpi
            WHERE success = 'True'
        """)
        successful_passengers = cur.fetchone()[0]
        print("successful_passengers:",successful_passengers)
        
        if total_passengers == 0:
            return "데이터가 없습니다."
        
        # 성공률 계산
        success_rate = (successful_passengers / total_passengers) * 100
        
        return f"전체 {total_passengers}명의 승객 중 {successful_passengers}명이 성공적으로 탑승했습니다. 탑승 거절률은 {1-success_rate:.2f}% 입니다."
        
    except Exception as e:
        print(f"Error calculating boarding success rate: {e}")
        return "탑승 거절률 계산 중 오류가 발생했습니다."
        
    finally:
        # DB 연결 종료
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# 셔틀의 정시 도착률 계산 
def calculate_on_time_arrival_rate(**kwargs):
  
    try:
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 전체 탑승 시도 횟수 조회, 탑승한 경우만 고려
        cur.execute("""
            SELECT COUNT(*) 
            FROM passengers_kpi
            WHERE boardingtime IS NOT NULL 
            AND waitstarttime IS NOT NULL
            AND expectedwaitingtime IS NOT NULL
        """)
        total_attempts = cur.fetchone()[0]
        print("total_attempts:", total_attempts)
        
        # 정시 도착 횟수 조회 (실제 대기 시간이 예상 대기 시간보다 늦지 않은 경우) 조절 가능
        cur.execute("""
            SELECT COUNT(*) 
            FROM passengers_kpi
            WHERE boardingtime IS NOT NULL 
            AND waitstarttime IS NOT NULL
            AND expectedwaitingtime IS NOT NULL
            AND (CAST(boardingtime AS numeric) - CAST(waitstarttime AS numeric)) <= CAST(expectedwaitingtime AS numeric)+100
        """)
        on_time_arrivals = cur.fetchone()[0]
        print("on_time_arrivals:", on_time_arrivals)
        
        if total_attempts == 0:
            return "데이터가 없습니다."
        
        # 정시 도착률 계산
        on_time_rate = (on_time_arrivals / total_attempts) * 100
        
        return f"전체 {total_attempts}회의 탑승 시도 중 {on_time_arrivals}회가 예상 대기 시간 내에 도착했습니다. 정시 도착률은 {on_time_rate:.2f}% 입니다."
        
    except Exception as e:
        print(f"Error calculating on-time arrival rate: {e}")
        return "정시 도착률 계산 중 오류가 발생했습니다."
        
    finally:
        # DB 연결 종료
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

# 시간 가중 평균을 사용하여 셔틀의 평균 탑승자 수를 계산
def calculate_weighted_avg_passengers(**kwargs):

    try:
        # shuttle_id 파라미터 확인
        if 'shuttle_id' not in kwargs:
            return "셔틀 ID를 지정해주세요."
        
        shuttle_id = kwargs['shuttle_id']
        
        # DB 연결
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 각 시점의 탑승자 수와 시간 정보 조회
        cur.execute("""
            SELECT 
                currenttime,
                cur_psgr_num
            FROM vehicle_kpi
            WHERE cur_psgr_num IS NOT NULL
            AND shuttle_id = %s
            AND CAST(cur_psgr_num AS numeric) > 0
            ORDER BY currenttime
        """, (shuttle_id,))
        rows = cur.fetchall()
        
        if not rows:
            return f"{shuttle_id}에 대한 데이터가 없습니다."
        
        # DataFrame 생성
        df = pd.DataFrame(rows, columns=['currenttime', 'cur_psgr_num'])
        
        # 시간을 numeric으로 변환
        df['currenttime'] = pd.to_numeric(df['currenttime'], errors='coerce')
        df['cur_psgr_num'] = pd.to_numeric(df['cur_psgr_num'], errors='coerce')
        
        # 결측치 제거
        df = df.dropna()
        
        if df.empty:
            return f"{shuttle_id}에 대한 유효한 데이터가 없습니다."
        
        # 시간 간격 계산 (가중치)
        df['time_weight'] = df['currenttime'].diff().fillna(0)
        
        # 가중 평균 계산
        weighted_sum = (df['cur_psgr_num'] * df['time_weight']).sum()
        total_weight = df['time_weight'].sum()
        
        if total_weight == 0:
            return f"{shuttle_id}의 시간 가중치를 계산할 수 없습니다."
        
        weighted_avg = weighted_sum / total_weight
        
        return f"{shuttle_id}의 시간 가중 평균을 적용한 평균 탑승자 수는 {weighted_avg:.2f}명 입니다."
        
    except Exception as e:
        print(f"Error calculating weighted average passengers: {e}")
        return "평균 탑승자 수 계산 중 오류가 발생했습니다."
        
    finally:
        # DB 연결 종료
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()




