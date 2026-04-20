import json
import matplotlib.pyplot as plt
import os
import pandas as pd

script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)
os.chdir(script_dir)

# JSON 파일 불러오기
file_path = './stop_summary.csv' 
df = pd.read_csv(file_path)

valid_df = df[df['Stop Count'] != 0]
validGridList = valid_df['Number'].tolist()
validGridWeight = valid_df['Number per Stop per Hours'].tolist()

# 'Number per Stop per Hours' 값을 반올림
valid_df['Number per Stop per Hours'] = valid_df['Number per Stop per Hours'].apply(lambda x: round(x, 1))

# stopInfo 생성
stop_info = []
for _, row in valid_df.iterrows():
    # Node IDs를 처리하여 4자리로 패딩, NaN이면 빈 리스트 처리
    if pd.notnull(row['Node IDs']):
        stop_node_ids = [f"{int(float(node_id.strip())):04d}" for node_id in str(row['Node IDs']).split(',') if node_id.strip().isdigit()]
    else:
        stop_node_ids = []

    # Stop 정보를 딕셔너리로 저장
    stop_info.append({
        "gridID": f"{row['Number']:04d}",
        "stopNodeID": stop_node_ids,
        "stopCount": int(row['Stop Count']),
        "perHour": float(row['Number per Stop per Hours'])
    })

# 최종 JSON 구조 생성
final_json = {
    "fileName": "passengerInfo",
    "validGridList": [f"{num:04d}" for num in validGridList],  # 여기도 4자리로 패딩
    "validGridWeight": validGridWeight,
    "avg"
    "stopInfo": stop_info
}

# JSON 파일로 저장
json_file_path = 'passengerInfo.json'
with open(json_file_path, 'w') as f:
    json.dump(final_json, f, indent=4)