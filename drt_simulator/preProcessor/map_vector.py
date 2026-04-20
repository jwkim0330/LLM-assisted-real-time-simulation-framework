import json

# JSON 파일을 로드하고 벡터를 추가하는 전체 코드
file_path = 'map_graph.json'

# JSON 파일 로드
with open(file_path, 'r') as file:
    map_data = json.load(file)

# 노드 데이터와 링크 데이터를 추출
nodes = map_data['nodes']
links = map_data['links']

# 각 링크에 대해 벡터를 계산하여 추가
for link in links:
    # 링크의 source와 target이 인덱스일 가능성이 있으므로 이를 인덱싱하여 사용
    source_node = nodes[int(link['source'])]
    target_node = nodes[int(link['target'])]
    
    # 벡터 계산
    vector_x = target_node['x'] - source_node['x']
    vector_y = target_node['y'] - source_node['y']
    
    # 벡터 추가
    link['vector'] = {'x': vector_x, 'y': vector_y}

# 업데이트된 JSON 파일을 저장
updated_file_path = 'map_graph_with_vectors.json'
with open(updated_file_path, 'w') as file:
    json.dump(map_data, file, indent=4)

print("업데이트된 파일 저장 경로:", updated_file_path)
