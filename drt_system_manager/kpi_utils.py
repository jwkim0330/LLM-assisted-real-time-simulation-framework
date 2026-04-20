# kpi_utils.py

from typing import Dict, Tuple

def get_running_sids(
    current_shuttles: Dict[str, Tuple[float, float, int]],
    shuttle_paths: Dict[str, list]
) -> list:
    """
    다음에 이동할 경로(path)가 남아 있는 셔틀 ID 목록을 반환.
    """
    return [
        sid
        for sid in current_shuttles
        if len(shuttle_paths.get(sid, [])) > 1
    ]

def count_running_shuttles(
    current_shuttles: Dict[str, Tuple[float, float, int]],
    shuttle_paths: Dict[str, list]
) -> int:
    """
    다음 경로가 남아 있는 셔틀(=운행 중인 셔틀) 수를 반환.
    """
    return len(get_running_sids(current_shuttles, shuttle_paths))

def compute_avg_occupancy(
    current_shuttles: Dict[str, Tuple[float, float, int]],
    shuttle_paths: Dict[str, list]
) -> float:
    """
    운행 중인(=다음 경로가 있는) 셔틀들의 평균 탑승자 수를 계산.
    """
    sids = get_running_sids(current_shuttles, shuttle_paths)
    if not sids:
        return 0.0
    total_occ = sum(current_shuttles[sid][2] for sid in sids)
    return total_occ / len(sids)

def compute_rejection_rate(
    cursor,
    upto_time: float
) -> float:
    """
    passengers_kpi 테이블에서
    - calltime ≤ upto_time 인 레코드 중
      • success = FALSE 건수(failed_count)
      • success = TRUE  건수(success_count)
      • success IS NULL 건수(null_count)
    를 각각 집계한 뒤,

    거절률 = failed_count / (failed_count + success_count + null_count) × 100
    """
    cursor.execute(
        """
        SELECT
          COUNT(*) FILTER (WHERE calltime::DOUBLE PRECISION <= %s AND success::Boolean  = FALSE) AS failed_count,
          COUNT(*) FILTER (WHERE calltime::DOUBLE PRECISION <= %s AND success::Boolean  = TRUE ) AS success_count,
          COUNT(*) FILTER (WHERE calltime::DOUBLE PRECISION <= %s AND success::Boolean  IS NULL) AS null_count
        FROM passengers_kpi
        """,
        (upto_time, upto_time, upto_time)
    )
    failed, success, nulls = cursor.fetchone()
    denom = failed + success + nulls
    if denom == 0:
        return 0.0
    return (failed / denom) * 100
