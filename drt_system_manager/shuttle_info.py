# shuttle_info.py

import ast, math
from typing import List, Dict, Any

def transform_cur_path(
    s: str,
    latlon_dict: Dict[int, Dict[str, float]],
    coord_to_name: Dict[tuple, str]
) -> List[Dict[str, Any]]:
    """
    cur_path 문자열 →
    [
      {"lon":…, "lat":…, "node_name":…},
      …
    ]
    """
    try:
        nodes = ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return []

    out = []
    for n in nodes:
        try:
            nid = int(n)
            coord = latlon_dict.get(nid)
            if coord:
                lon, lat = coord["lon"], coord["lat"]
                out.append({
                    "lon": lon,
                    "lat": lat,
                    "node_name": coord_to_name.get((lon, lat))
                })
        except Exception:
            continue

    return out

def haversine(
    lat1: float, lon1: float,
    lat2: float, lon2: float
) -> float:
    """
    두 위경도 사이의 거리 (km)
    """
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def compute_shuttle_metrics(
    vehicle_rows: List[Dict[str, Any]],
    sid: str,
    latlon_dict: Dict[int, Dict[str, float]],
    idle_threshold_km: float = 0.01
) -> Dict[str, float]:
    """
    shuttle_id == sid 인 레코드만 골라
      - 평균 탑승자
      - 총 운행 시간 (h)
      - 정체 시간 (h)
      - 누적 이동 거리 (km)
    를 계산해 리턴합니다.
    """
    # 1) 해당 셔틀 레코드 필터링 & 시간순 정렬
    recs = [r for r in vehicle_rows if r.get("shuttle_id") == sid]
    if len(recs) < 2:
        return {
            'average_occupancy': 0.0,
            'run_time_h'        : 0.0,
            'idle_time_h'       : 0.0,
            'total_distance_km' : 0.0
        }
    recs.sort(key=lambda r: r["currenttime"])

    # 2) 평균 탑승자 계산
    occs   = [(r.get("cur_psgr_num") or 0) for r in recs]
    avg_occ = sum(occs) / len(occs)

    # 3) 좌표 타임라인 생성 (path_nodes 우선, 없으면 cur_node fallback)
    timeline: List[tuple] = []
    for r in recs:
        t = r["currenttime"]
        coord = None

        # path_nodes 가 있으면 첫 번째 노드가 현재 위치라고 가정
        pn = r.get("path_nodes") or []
        if pn:
            coord = {"lat": pn[0]["lat"], "lon": pn[0]["lon"]}
        else:
            # 없으면 cur_node → latlon_dict 로 포인트 찾기
            try:
                nid = int(r.get("cur_node"))
                c = latlon_dict.get(nid)
                if c:
                    coord = {"lat": c["lat"], "lon": c["lon"]}
            except (ValueError, TypeError):
                coord = None

        if coord:
            timeline.append((t, coord["lat"], coord["lon"]))

    # 4) 거리·정체 시간 계산
    total_dist = 0.0
    idle_sec   = 0.0

    for (t0, lat0, lon0), (t1, lat1, lon1) in zip(timeline, timeline[1:]):
        dt = t1 - t0
        d  = haversine(lat0, lon0, lat1, lon1)
        total_dist += d
        if d < idle_threshold_km:
            idle_sec += dt

    run_h  = (timeline[-1][0] - timeline[0][0]) / 3600.0 if timeline else 0.0
    idle_h = idle_sec / 3600.0

    return {
        'average_occupancy': round(avg_occ,       2),
        'run_time_h'       : round(run_h,         2),
        'idle_time_h'      : round(idle_h,        2),
        'total_distance_km': round(total_dist,    2)
    }
