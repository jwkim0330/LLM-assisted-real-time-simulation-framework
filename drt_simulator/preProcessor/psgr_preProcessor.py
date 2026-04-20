import json
import matplotlib.pyplot as plt
import os
import pandas as pd

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)



# JSON 파일 불러오기
file_path = '../JSON/map_graph.json'  # 실제 파일 경로로 변경
with open(file_path, 'r') as file:
    data = json.load(file)

nodes = data['nodes']

min_x, max_x, min_y, max_y = 430, 1430, 1510, 2280

# 격자 크기 계산
grid_width = (max_x - min_x) / 9
grid_height = (max_y - min_y) / 9

# 격자별 노드 분류
grid_nodes = {f"Grid_{i+1}": [] for i in range(81)}

# 노드를 올바른 격자에 할당
for node in nodes:
    x, y = node['coordinates']
    grid_x = int((x - min_x) / grid_width)
    grid_y = int((y - min_y) / grid_height)
    grid_id = f"Grid_{(8 - grid_y) * 9 + grid_x + 1}"  # 좌상단을 그리드 1로 시작
    
    grid_nodes[grid_id].append(node['id'])

# 각 격자별 노드 ID 리스트를 문자열로 변환하고 DataFrame 생성
df_grid_nodes = pd.DataFrame([(key, ', '.join(value)) for key, value in grid_nodes.items()], 
                             columns=['Grid ID', 'Node IDs'])

# DataFrame 출력
df_grid_nodes.head(10)  # 처음 10개의 격자만 출력합니다.


csv_file_path = 'grid_nodes.csv'  # 원하는 경로로 변경
df_grid_nodes.to_csv(csv_file_path, index=False)

print(f"CSV 파일이 저장되었습니다: {csv_file_path}")