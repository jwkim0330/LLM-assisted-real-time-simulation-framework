# 공유 상태 변수들을 저장하는 모듈

# 전역 상태 변수
current_shuttles = {}  # sid → (lon,lat,occupancy)
shuttle_paths = {}    # sid → [{lon,lat,node_name}, …]
all_rows = []         # DB에서 로드한 모든 행
all_passenger_rows = []  # 승객 데이터 행
latest_time = 0.0     # 최신 시간
TOTAL_SHUTTLES = 8    # 전체 셔틀 수

# 지도 관련 데이터
latlon_dict = {}      # 노드 ID → (lat, lon) 매핑
node_data = {}        # 노드 데이터
node_name_map = {}    # 노드 ID → 노드 이름 매핑

# DB 커서
cur = None

def find_nearest_nodes(x, y, nodeInfo, num_neighbors=1):
    """주어진 좌표에서 가장 가까운 노드를 찾는 함수"""
    x = (x-126)*10000
    y = (y-37)*10000
    distances = []
    for node_id, coordinates in nodeInfo.items():
        node_x, node_y = coordinates 
        distance = ((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5
        distances.append((distance, node_id))
    distances.sort()
    nearest_nodes = [node_id for _, node_id in distances[:num_neighbors]]
    return nearest_nodes 