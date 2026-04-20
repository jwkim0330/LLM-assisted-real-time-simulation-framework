# data_utils.py
import pandas as pd

def get_passenger_records(rows, pid=None, success_vals=None, shuttle_query=None):
    df = pd.DataFrame(rows)
    if df.empty:
        return []

    # 1) calltime 순 정렬
    df = df.sort_values("calltime")

    # 2) 필터링
    if pid is not None:
        df = df[df["passenger_id"] == pid]
    if success_vals:
        df = df[df["success"].isin(success_vals)]
    if shuttle_query:
        df = df[df["shuttleid"].astype(str).str.contains(shuttle_query, na=False)]

    # 3) 반환할 컬럼 순서 지정 (boardingtime 포함)
    cols = [
        "passenger_id", "calltime", "dep_node_expanded", "arr_node",
        "shuttleid", "success",
        "waitstarttime", "boardingtime",                # 신규 추가
        "expectedarrivaltime", "expectedwaitingtime",
        "arrivaltime"
    ]
    return df[cols].to_dict("records")




def get_vehicle_records(rows, shuttle_query=None):
    """
    all_rows 리스트를 받아서
    - shuttle_id 문자열 포함 검색(shuttle_query)
    로 필터링 후 currenttime 순으로 정렬한 dict 리스트를 반환.
    """
    df = pd.DataFrame(rows)
    if df.empty:
        return []
    df = df.sort_values("currenttime")
    if shuttle_query:
        df = df[df["shuttle_id"].str.contains(shuttle_query, na=False)]
    return df.to_dict("records")
