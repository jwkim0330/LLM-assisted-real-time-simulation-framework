import json
import os
import requests
from shapely.geometry import Point, Polygon
import math

# 모듈 레벨 초기화 — 누적 슬롯
departure = ''
destination = ''
passengers = ''

# 경로가 맞게 입력 됐는지 확인하는 함수
def search_route(**kwargs):
    print(f"[FunctionCollection][search_route] 시작")
    global departure, destination, passengers

    # 새로 들어온 값 (빈 문자열이면 무시)
    new_departure = kwargs.get('departure', '').replace('에서', '').strip()
    new_destination = kwargs.get('destination', '').replace('까지', '').strip()
    new_passengers = kwargs.get('passengers', '').replace('명', '').replace('인', '').strip()

    # 들어온 값만 갱신 (빈 값은 기존 상태 유지)
    if new_departure:
        departure = new_departure
    if new_destination:
        destination = new_destination
    if new_passengers:
        passengers = new_passengers

    print(f"[search_route] 누적 상태 | departure={departure!r}, destination={destination!r}, passengers={passengers!r}")

    # 누락 필드 안내 — 출발지 → 도착지 → 인원 순으로 자연스럽게
    if not departure:
        return "출발지를 입력해달라냥~"
    if not destination:
        return "도착지를 입력해달라냥~"
    if not passengers:
        return "탑승 인원수를 입력해달라냥~"
    
    # 탑승 인원 숫자 검증
    try:
        passengers_int = int(passengers)
        if passengers_int < 1:
            return "탑승 인원수는 1명 이상이어야 한다냥~"
        if passengers_int > 8:
            return "탑승 인원수가 많다냥~"
    except (ValueError, TypeError):
        return "탑승 인원수는 숫자로 입력해달라냥~."
   
    # 최종 확인 질문 반환
    print(f"[FunctionCollection][search_route] 종료")
    return f"입력한 정보를 확인해볼게냥!!\n출발지: {departure}\n도착지: {destination}\n탑승 인원: {passengers}명\n이 정보가 맞냥??"

# 한대앞역 중심점
CENTER_LAT = 37.30218111999512
CENTER_LON = 126.84172413339247
RADIUS_METERS = 2900  # 반경 2900미터

def is_inside_boundary(lat, lon, boundary_coords=None):
    # 두 지점 간의 거리를 계산 (Haversine 공식)
    R = 6371000  # 지구의 반경 (미터)
    
    lat1, lon1 = math.radians(CENTER_LAT), math.radians(CENTER_LON)
    lat2, lon2 = math.radians(lat), math.radians(lon)
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    
    return distance <= RADIUS_METERS

# 경로가 맞는지 확인하는 함수
def confirm_route(**kwargs):
    # 전역 변수로 저장된 출발지, 도착지, 승객 수를 사용하기 위해 선언
    global departure, destination, passengers
    
    # 네이버 지역 검색 API 키 설정
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")
    
    # kwargs 에서 'confirmed' 값을 가져오되, 없으면 False 로 처리
    confirmed = kwargs.get("confirmed", False)

    if confirmed:
        try:
            # 출발지 네이버 검색
            lat_s, lon_s = search_poi_naver(departure, client_id, client_secret)
            # 도착지 네이버 검색
            lat_e, lon_e = search_poi_naver(destination, client_id, client_secret)
        except ValueError as e:
            return f"검색 결과가 없다냥~ {str(e)}"
        except Exception as e:
            return f"검색 중 오류가 발생했다냥~ {str(e)}"

        # 경계선 내부 판별
        if not is_inside_boundary(lat_s, lon_s):
            return "출발지가 경로(파란선) 밖에 있다냥~"
        if not is_inside_boundary(lat_e, lon_e):
            return "도착지가 경로(파란선) 밖에 있다냥~"

        route_data = {
            "departure": departure,
            "destination": destination,
            "passengers": int(passengers),
            "lat_s": lat_s,
            "lon_s": lon_s,
            "lat_e": lat_e,
            "lon_e": lon_e
        }
        # 전역 변수 초기화
        departure = ''
        destination = ''
        passengers = ''
        return f"CLOSE_POPUP:1000:알겠다냥! 경로 검색을 시작할게냥!{json.dumps(route_data, ensure_ascii=False)}"
    else:
        return "냥냥냥..., 다시 얘기해 달라냥."
    

# 네이버 지역 검색 API를 이용해 장소명(query)의 위도·경도를 반환
def search_poi_naver(query: str, client_id: str, client_secret: str):
    # 검색어에 상록구가 포함되어 있지 않으면 추가
    

    # 2) 단원 단어가 없으면 앞에 붙인다.
    
    url = "https://openapi.naver.com/v1/search/local.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": 1
    }
    res = requests.get(url, headers=headers, params=params)
    res.raise_for_status()
    data = res.json()
    items = data.get("items")
    if not items:
        raise ValueError(f"'{query}'에 대한 검색 결과가 없습니다.")
    first = items[0]
    lat = float(first["mapy"])/ 10000000
    lon = float(first["mapx"])/ 10000000
    
    return lat, lon