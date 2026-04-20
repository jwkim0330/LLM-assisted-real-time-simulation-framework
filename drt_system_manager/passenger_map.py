# passenger_map.py

import logging
import plotly.graph_objects as go

logger = logging.getLogger(__name__)

# Dash assets 폴더에 passenger.png 를 넣어두면 이 URL 로 자동 호스팅됩니다.
ICON_URL = "url(/assets/passenger.png)"

def filter_passengers(passenger_rows, latest_time):
    """
    all_passenger_rows 중에서
      - pending: success is None
      - boarded: success is True
      - rejected: success is False
    으로 분류한 뒤 세 개의 리스트를 반환.
    calltime > latest_time 인 건 무시.
    """
    logger.debug(f"[filter_passengers] 시작: latest_time={latest_time}, 전체 rows={len(passenger_rows)}")
    pending, boarded, rejected = [], [], []

    for idx, r in enumerate(passenger_rows):
        ct = r.get("calltime")
        if ct is None or ct > latest_time:
            logger.debug(f"[filter_passengers] 스킵 idx={idx}, calltime={ct}")
            continue

        s = r.get("success")
        if s is None:
            pending.append(r)
        elif s:
            boarded.append(r)
        else:
            rejected.append(r)

    logger.debug(f"[filter_passengers] 결과: pending={len(pending)}, boarded={len(boarded)}, rejected={len(rejected)}")
    return pending, boarded, rejected


def make_passenger_trace(rows, latlon_dict, name, icon_url=ICON_URL, size=30):
    """
    rows 의 dep_node 값을
      1) int ID → latlon_dict 매핑
      2) tuple/list (lon, lat) → 바로 사용
      3) 문자열 "(lon, lat)" → 파싱
    후 Scattermapbox Trace 를 반환. 유효 좌표 없으면 None 반환.
    """
    logger.debug(f"[make_passenger_trace] 시작: name={name}, rows={len(rows)}")
    lats, lons = [], []

    for idx, r in enumerate(rows):
        raw = r.get("dep_node_expanded")
        lon, lat = None, None

        # 1) 이미 튜플/리스트 형태
        if isinstance(raw, (tuple, list)) and len(raw) == 2 \
           and all(isinstance(x, (int, float)) for x in raw):
            lon, lat = raw[0], raw[1]
            logger.debug(f"[make_passenger_trace] idx={idx} raw tuple → lon={lon}, lat={lat}")

        # 2) 문자열 "(lon, lat)" 형태
        elif isinstance(raw, str) and raw.startswith("(") and raw.endswith(")"):
            try:
                parts = raw.strip("()").split(",", 1)
                lon, lat = float(parts[0]), float(parts[1])
                logger.debug(f"[make_passenger_trace] idx={idx} raw str → lon={lon}, lat={lat}")
            except Exception as e:
                logger.error(f"[make_passenger_trace] idx={idx} str 파싱 실패 raw={raw}, error={e}")

        # 3) 그 외(기존): 정수 ID 로 간주
        else:
            try:
                nid = int(raw)
                coord = latlon_dict.get(nid)
                if coord:
                    lon, lat = coord["lon"], coord["lat"]
                    logger.debug(f"[make_passenger_trace] idx={idx} raw id={nid} → lon={lon}, lat={lat}")
                else:
                    logger.warning(f"[make_passenger_trace] idx={idx} id 매핑 실패 nid={nid}")
            except Exception as e:
                logger.error(f"[make_passenger_trace] idx={idx} 잘못된 dep_node={raw}, error={e}")

        # 최종 유효 좌표 체크
        if lon is not None and lat is not None:
            lons.append(lon)
            lats.append(lat)
        else:
            logger.debug(f"[make_passenger_trace] idx={idx} 유효 좌표 누락 raw={raw}")

    logger.debug(f"[make_passenger_trace] 매핑 완료: valid_points={len(lats)}")
    if not lats:
        logger.debug(f"[make_passenger_trace] 유효 좌표 없음(name={name}), None 반환")
        return None

    trace = go.Scattermapbox(
        lat=lats,
        lon=lons,
        mode="markers",
        marker=dict(
            size=size,
            symbol=icon_url,
            allowoverlap=True,
            opacity=0.8
        ),
        name=name
    )
    logger.debug(f"[make_passenger_trace] Trace 생성 완료(name={name})")
    return trace
