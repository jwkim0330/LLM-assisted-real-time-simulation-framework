import json

# map_graph.json 파일의 경로 설정
file_path = 'JSON/map_graph.json'  # 파일 경로는 실행하는 위치에 따라 상대적입니다.

# 파일을 로드하고 'time' 값을 다시 계산하여 파일에 덮어쓰기 하는 함수
def update_time_in_map_graph(file_path):
    # 파일 로드
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # links 내 각 항목에 대해 'time' 계산
    for link in data['links']:
        # 속도 km/h를 m/s로 변환
        speed_m_s = link['max_spd'] * 1000 / 3600
        # 거리(m)를 속도(m/s)로 나누어 시간(초) 계산
        link['time'] = round(link['length'] / speed_m_s)
    
    # 변경된 데이터를 같은 파일명으로 저장하여 덮어쓰기
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

# 함수 호출
update_time_in_map_graph(file_path)
