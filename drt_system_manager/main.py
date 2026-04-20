# 1. 표준 라이브러리 & 데이터 핸들링
import random
import psycopg2
import pandas as pd
import plotly.express as px
import requests
from collections import defaultdict
import math

# 1-1. 셔틀 정보 전처리 & 지표 계산
from shuttle_info import transform_cur_path, compute_shuttle_metrics

# 2. Dash & Plotly
import dash
from dash import dcc, html, callback_context, dash_table, no_update
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dash_table import DataTable

# 프로젝트 루트 모듈
from shuttle_info import transform_cur_path, compute_shuttle_metrics
import data_utils

# 4. KPI 유틸
from kpi_utils import (
    count_running_shuttles,
    compute_avg_occupancy,
    compute_rejection_rate
)

import os 
# 1) 이 파일이 있는 디렉토리 (프로젝트 루트)
BASE_DIR = os.path.dirname(__file__)
# 2) assets 폴더 경로
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

import base64
from io import BytesIO
from PIL import Image

#####
import data_utils
from Environment.EnvironmentLoader import EnvironmentLoader
node_data=EnvironmentLoader("./JSON/",["map_graph_with_vectors", "passengerInfo", "shuttleInfo", "setup"]).getConfiguration().getConfiguration("node_data")
def find_nearest_nodes(x, y,nodeInfo, num_neighbors=1):
        x=(x-126)*10000
        y=(y-37)*10000
        distances = []
        for node_id, coordinates  in nodeInfo.items():
            node_x, node_y = coordinates 
            distance = ((x - node_x) ** 2 + (y - node_y) ** 2) ** 0.5
            distances.append((distance, node_id))
        distances.sort()
        nearest_nodes = [node_id for _, node_id in distances[:num_neighbors]]
        return nearest_nodes


#####

# ──────────────────────────────────────────────────────────────
# 설정: 전체 셔틀 수
# ──────────────────────────────────────────────────────────────
global TOTAL_SHUTTLES
TOTAL_SHUTTLES = 8

# ──────────────────────────────────────────────────────────────
# 유틸리티: 색상 할당 & CSV 읽기
# ──────────────────────────────────────────────────────────────
available_colors = px.colors.qualitative.Plotly
shuttle_colors = {}
# ──────────────────────────────────────────────────────────────
# 3) 셔틀 ID → 고정 색 아이콘 파일 매핑
#    assets 폴더에 passenger_636EFA.png 등 미리 만들어 두셔야 합니다.
passenger_icon_map = {
    "SHUTTLE0001": "/assets/passenger_636EFA.png",
    "SHUTTLE0002": "/assets/passenger_EF553B.png",
    "SHUTTLE0003": "/assets/passenger_00CC96.png",
    "SHUTTLE0004": "/assets/passenger_AB63FA.png",
    "SHUTTLE0005": "/assets/passenger_FFA15A.png",
    "SHUTTLE0006": "/assets/passenger_19D3F3.png",
    "SHUTTLE0007": "/assets/passenger_FF6692.png",
    "SHUTTLE0008": "/assets/passenger_B6E880.png",
    # (필요한 만큼 더 추가)
}
# 배차 전 기본 아이콘
default_passenger_icon = "/assets/passenger_gray.png"
# ──────────────────────────────────────────────────────────────

def assign_shuttle_color(sid):
    if sid not in shuttle_colors:
        if len(shuttle_colors) < len(available_colors):
            shuttle_colors[sid] = available_colors[len(shuttle_colors)]
        else:
            while True:
                c = f"#{random.randint(0,0xFFFFFF):06x}"
                if c not in shuttle_colors.values():
                    shuttle_colors[sid] = c
                    break
    return shuttle_colors[sid]

def read_csv_with_fallback(path):
    for enc in ['utf-8','cp949','euc-kr']:
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"모든 인코딩 시도 실패: {path}")

mapping_df = read_csv_with_fallback(
    os.path.join(ASSETS_DIR, "mapping.csv")
)
# 컬럼명이 'id' 와 'NODE_NAME' 이므로, 그대로 사용합니다.
node_name_map = mapping_df.set_index("id")["NODE_NAME"].to_dict()
# ──────────────────────────────────────────────────────────────
# 지도 좌표 & 노드 이름 매핑 로드
# ──────────────────────────────────────────────────────────────
df_map   = read_csv_with_fallback(os.path.join(ASSETS_DIR, "위도경도_바인딩.csv"))
df_nodes = read_csv_with_fallback(os.path.join(ASSETS_DIR, "cor_node.csv"))
df_links = read_csv_with_fallback(os.path.join(ASSETS_DIR, "cor_link.csv"))

latlon_dict = (
    df_map
      .rename(columns={"위도":"lat","경도":"lon"})
      .set_index("id")[["lat","lon"]]
      .to_dict("index")
)

df_nodes = df_nodes.rename(columns={"NODE_NAME":"node_name","x":"lon","y":"lat"})
coord_to_name = {
    (row.lon, row.lat): row.node_name
    for _, row in df_nodes.iterrows()
}


# ──────────────────────────────────────────────────────────────
# 전역 상태 변수
# ──────────────────────────────────────────────────────────────
global all_rows
all_rows = []
global last_loaded_time
last_loaded_time = 0.0
global current_index
current_index = 0
global all_passenger_rows
all_passenger_rows = []
global last_loaded_pass_time
last_loaded_pass_time = 0.0
global latest_time
latest_time = 0.0

global shuttle_paths
shuttle_paths = {}  # sid → [{lon,lat,node_name}, …]
global current_shuttles
current_shuttles = {}  # sid → (lon,lat,occupancy)

# ──────────────────────────────────────────────────────────────
# DB 로우 로드 함수
# ──────────────────────────────────────────────────────────────
def load_new_db_rows():
    global all_rows, last_loaded_time
    try:
        print(f"[DEBUG] load_new_db_rows 시작 - last_loaded_time: {last_loaded_time}")
        
        cur.execute("""
           SELECT
                -- 문자열로 받을 필드들 (원래 TEXT 컬럼)
                scenario_info     AS scenario_info,   -- TEXT
                shuttle_id        AS shuttle_id,      -- TEXT
                shuttle_state     AS shuttle_state,   -- TEXT
                cur_dst           AS cur_dst,         -- TEXT
                cur_path          AS cur_path,        -- TEXT
                cur_psgr          AS cur_psgr,        -- TEXT
                cur_node          AS cur_node,        -- TEXT

                -- 숫자로 받을 필드들
                currenttime::DOUBLE PRECISION  AS currenttime,   -- float
                cur_psgr_num::DOUBLE PRECISION AS cur_psgr_num   -- float
            FROM vehicle_kpi
            WHERE (currenttime::DOUBLE PRECISION) > %s
            ORDER BY (currenttime::DOUBLE PRECISION) ASC
            LIMIT 5000
        """, (last_loaded_time,))
        
        rows = cur.fetchall()
        print(f"[DEBUG] DB 쿼리 결과 - 가져온 행 수: {len(rows) if rows else 0}")
        
        if not rows:
            print("[DEBUG] 새로운 데이터가 없습니다.")
            return
            
        cols = [d[0] for d in cur.description]
        processed_count = 0
        
        for r in rows:
            rec = dict(zip(cols, r))
            if rec["currenttime"] is None:
                continue
            rec["path_nodes"] = transform_cur_path(
                rec.get("cur_path",""),
                latlon_dict,
                coord_to_name
            )
            all_rows.append(rec)
            processed_count += 1
            
        print(f"[DEBUG] 처리된 행 수: {processed_count}")
        
        if all_rows:
            all_rows.sort(key=lambda r: r["currenttime"])
            last_loaded_time = all_rows[-1]["currenttime"]
            print(f"[DEBUG] last_loaded_time 업데이트: {last_loaded_time}")
            
    except Exception as e:
        print(f"[ERROR] load_new_db_rows 실행 중 오류: {e}")
        import traceback
        traceback.print_exc()

def load_new_passenger_rows():
    global all_passenger_rows, last_loaded_pass_time

    # 1) 새로 추가된 행(calltime > last_loaded_pass_time)
    #    + 기존 대기 중이던 승객 중에서 success가 NULL→Not NULL 로 바뀐 행도 함께 조회
    cur.execute("""
        SELECT
          passenger_id::BIGINT            AS passenger_id,       -- int
          psgrnum::BIGINT                 AS psgrnum,            -- int
          arr_node::BIGINT                AS arr_node,           -- int
          calltime::DOUBLE PRECISION      AS calltime,           -- float
          waitstarttime::BIGINT           AS waitstarttime,      -- int
          dep_node                        AS dep_node,           -- str
          dep_node_expanded               AS dep_node_expanded,  -- str
          shuttleid                       AS shuttleid,          -- str
          boardingtime::DOUBLE PRECISION  AS boardingtime,       -- float
          expectedwaitingtime::DOUBLE PRECISION AS expectedwaitingtime, -- float
          expectedarrivaltime::DOUBLE PRECISION AS expectedarrivaltime, -- float
          arrivaltime::DOUBLE PRECISION   AS arrivaltime,        -- float
          success::Boolean                         AS success             -- str (NULL 포함)
        FROM passengers_kpi
       WHERE (calltime::DOUBLE PRECISION) > %s
          OR (
               (calltime::DOUBLE PRECISION) <= %s
               AND success IS NOT NULL
             )
       ORDER BY (calltime::DOUBLE PRECISION) ASC
    """
    , (last_loaded_pass_time, last_loaded_pass_time))

    rows = cur.fetchall()
    if not rows:
        return

    cols = [desc[0] for desc in cur.description]

    # 2) 기존 리스트에 있는 레코드 인덱스를 key로 매핑
    existing = {
        (r["passenger_id"], r["calltime"]): idx
        for idx, r in enumerate(all_passenger_rows)
    }

    # 3) 페칭한 각 행을 신규/업데이트로 분기
    for r in rows:
        rec = dict(zip(cols, r))
        key = (rec["passenger_id"], rec["calltime"])
        if key in existing:
            # 이미 있던 레코드: success 등 필드를 업데이트
            all_passenger_rows[ existing[key] ].update(rec)
        else:
            # 새로운 호출 기록: 리스트에 추가
            all_passenger_rows.append(rec)

    # 4) calltime 순으로 재정렬
    all_passenger_rows.sort(key=lambda x: x["calltime"])

    # 5) last_loaded_pass_time 갱신: 가장 큰 calltime
    last_loaded_pass_time = max(r["calltime"] for r in all_passenger_rows)


def create_stats_box(stats_cards):
    """
    실시간 현황판을 담은 카드 컴포넌트 반환
    stats_cards: 기존에 정의하신 4개의 KPI 카드(운영 셔틀/평균 탑승객/누적 탑승객/거절률)를 담은 Div
    """
    return dbc.Card(
        [
            html.H4(
                "실시간 현황",
                style={
                    "fontWeight": "bold",
                    "textAlign": "center",
                    "marginBottom": "1rem"
                }
            ),
            stats_cards
        ],
        style={
            "borderRadius": "12px",
            "backgroundColor": "#fff",
            "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
            "padding": "1rem",
            "marginBottom": "1rem"
        }
    )

def get_psgrnum_for_shuttle(sid):
    """
    주어진 셔틀 ID에 대응되는 승객들의 승객 수(psgrnum)를 합산하여 반환합니다.
    """
    total_psgrnum = 0
    for passenger in all_passenger_rows:
        if passenger["passenger_id"] == sid:
            total_psgrnum = passenger.get("psgrnum", 1)  # 기본값 1로 설정
            return total_psgrnum
    return 0



    
# ──────────────────────────────────────────────────────────────
# DB 연결
# ──────────────────────────────────────────────────────────────


########### <원격 연결> #########
try:
    print("[DEBUG] 원격 DB 연결 시도 중...")
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', ''),
        port=int(os.getenv('DB_PORT', '5432')),
        dbname=os.getenv('DB_NAME', ''),
        user=os.getenv('DB_USER', ''),
        password=os.getenv('DB_PASSWORD', '')
    )
    conn.autocommit = True
    cur = conn.cursor()
    print("[DEBUG] 원격 DB 연결 성공!")
except Exception as e:
    print(f"[ERROR] 원격 DB 연결 실패: {e}")
    print("[DEBUG] 로컬 DB 연결 시도...")
    try:
        DB = dict(
            host=os.getenv('LOCAL_DB_HOST', 'localhost'),
            database=os.getenv('LOCAL_DB_NAME', 'postgres'),
            user=os.getenv('LOCAL_DB_USER', 'postgres'),
            password=os.getenv('LOCAL_DB_PASSWORD', '')
        )
        conn = psycopg2.connect(**DB)
        conn.autocommit = True
        cur = conn.cursor()
        print("[DEBUG] 로컬 DB 연결 성공!")
    except Exception as e2:
        print(f"[ERROR] 로컬 DB 연결도 실패: {e2}")
        print("[ERROR] DB 연결 실패로 인해 앱을 종료합니다.")
        exit(1)
##################################





# ──────────────────────────────────────────────────────────────
# Dash 앱 & 레이아웃 (멀티페이지)
# ──────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.COSMO],
    suppress_callback_exceptions=True
)

# ▶ 대시보드 전용 레이아웃
stats_cards = html.Div(
    style={
        "display": "flex",
        "gap": "1rem",
        "marginBottom": "1rem",
        "justifyContent": "center"
    },
    children=[
        dbc.Card(
            dbc.CardBody([
                html.H6([
                        "운영 셔틀 /",  # 첫 줄
                        html.Br(),
                        "전체 셔틀"   # 둘째 줄
                    ],
                 style={"fontWeight": "600"}),
                html.H5(id="total-shuttles", style={"fontWeight": "bold", "color": "BRIGHT_BLUE"}),
            ]),
            style={"flex": "1", "borderRadius": "12px"}
        ),
        dbc.Card(
            dbc.CardBody([
                html.H6("평균 탑승객", style={"fontWeight": "600"}),
                html.H5(id="avg-occupancy", style={"fontWeight": "bold", "color": "BRIGHT_BLUE"}),
            ]),
            style={"flex": "1", "borderRadius": "12px"}
        ),
        dbc.Card(
            dbc.CardBody([
                html.H6("누적 탑승객", style={"fontWeight": "600"}),
                html.H5(id="cumulative_passenger_num", style={"fontWeight": "bold", "color": "BRIGHT_BLUE"}),
            ]),
            style={"flex": "1", "borderRadius": "12px"}
        ),
        dbc.Card(
            dbc.CardBody([
                html.H6("거절률", style={"fontWeight": "600"}),
                html.H5(id="rejection-rate", style={"fontWeight": "bold", "color": "BRIGHT_BLUE"}),
            ]),
            style={"flex": "1", "borderRadius": "12px"}
        ),
    ]
)


analysis_subtabs = dbc.Tabs(
    [dbc.Tab(label="거절률 높은 지역",   tab_id="tab-rej-area"),
     dbc.Tab(label="대기시간 오차",      tab_id="tab-rej-rank"),
     dbc.Tab(label="이동시간 오차",      tab_id="tab-veh-stats")],
    id="analysis-tabs", active_tab="tab-rej-area"
)
left_panel = html.Div(
    style={"position":"relative","width":"100%","height":"100vh","overflow":"hidden"},
    children=[
                 dcc.Graph(
             id="map-graph", 
             style={"width":"100%","height":"100%"},
             config={'displayModeBar': True, 'scrollZoom': True}
         ),
        dbc.Switch(id="toggle-density", value=False,
                   style={"position":"absolute","top":"10px","left":"10px","zIndex":1001}),
        html.Div("밀집도", style={"position":"absolute","top":"10px","left":"50px","padding":"2px 6px","background":"rgba(0,0,0,0.4)","color":"#fff","borderRadius":"4px","zIndex":1001}),
        dbc.Switch(id="toggle-reject-heatmap", value=False,
                   style={"position":"absolute","top":"40px","left":"10px","zIndex":1001}),
        html.Div("거절 히트맵", style={"position":"absolute","top":"40px","left":"50px","padding":"2px 6px","background":"rgba(0,0,0,0.4)","color":"#fff","borderRadius":"4px","zIndex":1001}),
        html.Div(id="current-time-display", style={"position":"absolute","top":"70px","left":"10px","padding":"6px","background":"rgba(0,0,0,0.6)","color":"#fff","borderRadius":"4px","zIndex":1000}),
        html.Div(id="shuttle-info-card", children=[html.Button("",id="close-shuttle-btn",n_clicks=0,style={"display":"none"})], style={"position":"absolute","top":"100px","left":"10px","zIndex":1002,"width":"280px"}),
    ]
)
# 기존 right_panel 정의를 아래처럼 바꿔주세요.

right_panel = html.Div(
    style={"flex":"0 0 40%", "padding":"10px","overflow":"auto"},
    children=[
        # ───────────────── stats 카드(변경 없음)
        create_stats_box(stats_cards),

        # ───────────────── 운영 분석 지표 패널
        dbc.Card(
            [
                html.H4(
                    "운영 분석 지표",
                    style={
                        "fontWeight": "bold",
                        "textAlign": "center",
                        "marginBottom": "1rem"
                    }
                ),
                # 기존에 analysis_subtabs 로 정의된 탭들
                analysis_subtabs,
                # tab-content 콜백이 여기에 렌더링됩니다.
                html.Div(
                    id="tab-content",
                    style={"padding": "1rem", "background": "#f9f9f9"}
                )
            ],
            style={
                "borderRadius": "12px",
                "backgroundColor": "#fff",
                "boxShadow": "0 2px 6px rgba(0,0,0,0.1)",
                "padding": "0",
                "marginBottom": "1rem"
            }
        ),
    ]
)

visual_layout = html.Div(style={"display":"flex","height":"100vh"}, children=[left_panel, right_panel])


# ──────────────────────────────────────────────────────────────
# 1) 메인 레이아웃
# ──────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────
# 1) 메인 레이아웃
# ──────────────────────────────────────────────────────────────
# … (중략) …

# 1) 메인 레이아웃
main_layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("관리자 대시보드", href="/"),
            dbc.Button("데이터 보기", href="/data", color="light", className="ms-auto")
        ]),
        style={"backgroundColor": "#0e4a84"},
        dark=True,
        className="mb-4"
    ),
    visual_layout,
    dcc.Interval(id="interval", interval=500, n_intervals=0),  # 0.5초마다 업데이트 (안정성 향상)
    dcc.Store(id="show-density", data=False),
    dcc.Store(id="show-reject-heatmap", data=False),
    dcc.Store(id="chat-open", data=False),

    # 2) FAB 버튼 ── 인라인 스타일 제거, ID만 남김
    html.Button(
        "🗨️",
        id="open-chat-btn"
        # style={…} 부분 모두 제거했습니다.
    ),

    # 3) 챗봇 패널 ── style 대신 className="" 만 지정
    html.Div(
        id="chat-panel",
        className="",   # 초기 상태: “open” 클래스가 붙어 있지 않음 → CSS에서 display: none 처리
        children=[
            # (3-1) 닫기 버튼, 인라인 스타일 제거
            html.Button("×", id="close-chat-btn"),

            # (3-2) 대화 내역, 인라인 스타일 제거
            html.Div(id="chat-output"),

            # (3-3) 입력창
            dcc.Textarea(
                id="chat-input",
                placeholder="셔틀 3은 지금 어디에 있어?"
            ),

            # (3-4) 전송 버튼
            html.Div(
                html.Button("Send", id="chat-send"),
                style={"textAlign": "right", "marginTop": "0.5rem"}
                # 버튼 내부만 margin 주기 위해 여전히 간단한 인라인 스타일을 남겼습니다.
            )
        ]
    )
])



# ──────────────────────────────────────────────────────────────
# 2) 데이터 보기 레이아웃
# ──────────────────────────────────────────────────────────────
data_layout = html.Div([
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("데이터 보기", href="/data"),
            dbc.Button("대시보드로 이동", href="/", color="light", className="ms-auto")
        ]),
        style={"backgroundColor": "#0e4a84"},dark=True
    ),
    html.Div([
        # 필터 컨트롤
        html.Div([
            html.Label("승객 ID:"), dcc.Input(id="filter-passenger-id", type="number", placeholder="ID 입력"),
            html.Label("성공 여부:"), dcc.Dropdown(id="filter-success",
                 options=[{"label":"성공","value":True},{"label":"실패","value":False}],
                 multi=True, placeholder="선택", style={"width":"150px"}),
            html.Label("셔틀 ID:"), dcc.Input(id="filter-shuttle-id",type="text",placeholder="S1")
        ], style={"display":"flex","gap":"1rem","padding":"1rem","alignItems":"center"}),
        # 테이블
        html.H5("Passengers KPI"),
        dash_table.DataTable(
            id="table-passengers",
            columns=[
                {"name":"Passenger ID",        "id":"passenger_id"},
                {"name":"Call Time",           "id":"calltime"},
                {"name":"Dep Node",            "id":"dep_node_expanded"},
                {"name":"Arr Node",            "id":"arr_node"},
                {"name":"Shuttle ID",          "id":"shuttleid"},
                {"name":"Success",             "id":"success"},
                {"name":"Wait Start Time",     "id":"waitstarttime"},
                {"name":"Boarding Time",       "id":"boardingtime"},
                {"name":"Expected Arrival",    "id":"expectedarrivaltime"},
                {"name":"Expected Waiting",    "id":"expectedwaitingtime"},
                {"name":"Arrival Time",        "id":"arrivaltime"},
             ],
            page_size=20, filter_action="native", sort_action="native",
            sort_by=[{"column_id":"calltime","direction":"asc"}],
            style_table={"overflowX":"auto"}
        ),
        html.H5("Vehicle KPI", className="mt-4"),
        dash_table.DataTable(
            id="table-vehicles",
            columns=[{"name":c,"id":c} for c in ["currenttime","shuttle_id","cur_node","cur_psgr_num"]],
            page_size=20, filter_action="native", sort_action="native",
            sort_by=[{"column_id":"currenttime","direction":"asc"}],
            style_table={"overflowX":"auto"}
        )
    ])
])

# ──────────────────────────────────────────────────────────────
# 3) 전체 앱 레이아웃 (라우팅)
# ──────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# ──────────────────────────────────────────────────────────────
# 페이지 라우팅 콜백
# ──────────────────────────────────────────────────────────────
@app.callback(
    Output("page-content","children"),
    Input("url","pathname")
)
def display_page(pathname):
    if pathname == "/data":
        return data_layout
    return main_layout

# ──────────────────────────────────────────────────────────────
# 이하 기존 콜백들 (수정 없이 그대로)
# 1) Primary Tabs 렌더링
# open / close 버튼 누를 때 chat-open 토글
@app.callback(
    Output("chat-open", "data"),
    [Input("open-chat-btn", "n_clicks"),
     Input("close-chat-btn", "n_clicks")],
    prevent_initial_call=True
)
def toggle_chat(open_clicks, close_clicks):
    ctx = callback_context.triggered_id
    return True if ctx == "open-chat-btn" else False

# chat-open 값에 따라 패널 보이기/숨기기
@app.callback(
    Output("chat-panel", "className"),
    Input("chat-open", "data"),
    prevent_initial_call=True
)
def show_hide_chat(opened):
    # opened == True  → "open" 클래스를 붙여 줘서 CSS #chat-panel.open { display:flex } 적용
    # opened == False → 빈 문자열 → display:none 이 CSS에서 처리
    return "open" if opened else ""





@app.callback(
    Output("tab-content", "children"),
    Input("analysis-tabs", "active_tab")
)
def render_tab(active_tab):
    if active_tab == "tab-rej-area":
        return DataTable(
            id="rej-area-table",
            columns=[
                {"name":"지역",     "id":"region"},
                {"name":"거절 횟수","id":"count"}
            ],
            data=[],              # 초기에는 빈 리스트
            page_size=10,
            sort_action="native",
            style_cell={"textAlign":"center"},
            style_header={"fontWeight":"bold"}
        )  
    elif active_tab == "tab-rej-rank":
        return dcc.Graph(id="wait-error-graph")
    else:
        return dcc.Graph(id="travel-error-graph")


# 3) 토글 스토어 업데이트
@app.callback(Output("show-density","data"), Input("toggle-density","value"))
def toggle_density(on): return on
@app.callback(Output("show-reject-heatmap","data"), Input("toggle-reject-heatmap","value"))
def toggle_reject_heatmap(on): return on

# 4) DB → 메모리 로드
@app.callback(Output("interval","n_intervals"), Input("interval","n_intervals"))
def update_sim(n):
    """
    시뮬레이션 데이터 업데이트 함수
    DB에서 최신 차량/승객 데이터를 로드하고 차량 위치/경로를 실시간으로 업데이트
    
    Args:
        n: interval 컴포넌트의 n_intervals 값 (1초마다 실행 트리거)
    
    Returns:
        n: 입력값을 그대로 반환 (interval 컴포넌트 업데이트용)
    """
    global current_index, latest_time
    
    try:
        # 1. DB에서 새로운 차량/승객 데이터 로드
        print(f"[DEBUG] update_sim 실행 - n_intervals: {n}, current_index: {current_index}")
        
        load_new_db_rows()
        print(f"[DEBUG] load_new_db_rows 완료 - all_rows 길이: {len(all_rows)}")
        
        load_new_passenger_rows()
        print(f"[DEBUG] load_new_passenger_rows 완료 - all_passenger_rows 길이: {len(all_passenger_rows)}")
        
        # 2. 새로 추가된 데이터만 처리 (current_index 이후부터)
        new_data_count = 0
        for row in all_rows[current_index:]:
            new_data_count += 1
            sid = row["shuttle_id"]  # 셔틀 ID
            occ = row.get("cur_psgr_num",0) or 0  # 현재 탑승자 수 (기본값 0)
            pts = row.get("path_nodes",[])  # 경로 노드들
            
            # 3. 셔틀 경로 업데이트
            shuttle_paths[sid] = pts
            
            # 4. 경로가 1개 이하면 정지 상태로 간주하여 탑승자 수 0으로 설정
            if len(pts)<=1: occ=0
            
            # 5. 셔틀 현재 위치 업데이트
            try:
                nid=int(row["cur_node"])  # 현재 노드 ID
                coord=latlon_dict.get(nid)  # 노드 ID → 좌표 변환
                if coord:
                    # 셔틀 위치: (경도, 위도, 탑승자수)
                    current_shuttles[sid] = (coord["lon"], coord["lat"], occ)
            except Exception as e: 
                print(f"[DEBUG] 좌표 변환 실패 - sid: {sid}, cur_node: {row.get('cur_node')}, error: {e}")
                pass  # 좌표 변환 실패 시 무시
            
            # 6. 시뮬레이션 시간 업데이트
            latest_time = row["currenttime"]
        
        print(f"[DEBUG] 새 데이터 처리 완료 - 처리된 행 수: {new_data_count}, latest_time: {latest_time}")
        print(f"[DEBUG] 현재 셔틀 수: {len(current_shuttles)}, 경로 수: {len(shuttle_paths)}")
        
        # 7. 처리 완료된 인덱스 업데이트
        current_index = len(all_rows)
        
    except Exception as e:
        print(f"[ERROR] update_sim 실행 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    
    return n


# 5) 지도 업데이트 (밀집도 + 거절 히트맵 포함)
# ──────────────────────────────────────────────────────────────
@app.callback(
    Output("map-graph","figure"),
    Output("current-time-display","children"),
    Input("interval","n_intervals"),
    State("show-density","data"),
    State("show-reject-heatmap","data")
)

def update_map(n_intervals, show_density, show_reject):
    import math
    fig = go.Figure()

    # (0) 중심 마커
    fig.add_trace(go.Scattermapbox(
        lat=[37.29994127489433], lon=[126.83721112385808],
        mode="markers", marker=dict(size=0), hoverinfo="skip",
        uid="center-marker"
    ))

    # (1) 셔틀 경로 (uid 고정)
    for sid, pts in sorted(shuttle_paths.items()):
        if len(pts) >= 2:
            c = assign_shuttle_color(sid)
            fig.add_trace(go.Scattermapbox(
                lon=[p["lon"] for p in pts],
                lat=[p["lat"] for p in pts],
                mode="lines",
                line=dict(width=3, color=c),
                hoverinfo="skip",
                uid=f"path-{sid}",
            ))

    # (2) 셔틀 위치 (uid 고정)
    for sid, (lon, lat, occ) in sorted(current_shuttles.items()):
        marker_color = text_color = (
            "gray" if len(shuttle_paths.get(sid, [])) <= 1 else assign_shuttle_color(sid)
        )
        fig.add_trace(go.Scattermapbox(
            lon=[lon], lat=[lat],
            mode="markers+text",
            marker=dict(size=14, color=marker_color),
            text=[f"S{sid[-1]} : {occ}명"],
            textposition="top center",
            textfont=dict(color=text_color, size=12),
            customdata=[sid],
            uid=f"shuttle-{sid}",
        ))

    # (3) 일반 승객 밀집도 trace는 항상 유지 (데이터만 비우기)
    pd_lat, pd_lon, pd_z = [], [], []
    if show_density and all_passenger_rows:
        counts = defaultdict(int)
        for r in all_passenger_rows:
            if r.get("calltime", 0) <= latest_time:
                try:
                    nid = int(r.get("arr_node"))
                    if nid in latlon_dict:
                        counts[nid] += 1
                except Exception:
                    pass
        if counts:
            pd_lat = [latlon_dict[n]["lat"] for n in counts]
            pd_lon = [latlon_dict[n]["lon"] for n in counts]
            pd_z   = list(counts.values())

    fig.add_trace(go.Densitymapbox(
        lat=pd_lat, lon=pd_lon, z=pd_z,
        radius=25, colorscale="YlOrRd", showscale=False, opacity=0.6,
        uid="density-passenger",
    ))

    # (4) 거절 히트맵 trace도 항상 유지 (데이터만 비우기)
    rj_lon, rj_lat = [], []
    if show_reject and all_passenger_rows:
        for r in all_passenger_rows:
            if not r.get("success") and r.get("calltime", 0) <= latest_time:
                dep_str = r.get("dep_node_expanded", "")
                try:
                    lon_str, lat_str = dep_str.strip("()").split(",", 1)
                    lon, lat = float(lon_str), float(lat_str)
                    if math.isfinite(lon) and math.isfinite(lat):
                        rj_lon.append(lon); rj_lat.append(lat)
                except Exception:
                    continue

    fig.add_trace(go.Densitymapbox(
        lon=rj_lon, lat=rj_lat, z=[1]*len(rj_lon) if rj_lon else [],
        radius=25,
        colorscale=[[0.0, "rgba(255,200,200,0.0)"], [1.0, "rgba(255,0,0,0.6)"]],
        showscale=False, opacity=0.6,
        uid="density-reject",
    ))

    # (5) 승객 아이콘: 이미지 레이어는 리스트를 만들되, 아래에서 mapbox에 한 번에 세팅
    layers = []
    d = 0.0015

    # hover 용: 매 프레임 trace 개수 변동을 줄이기 위해 하나로 합침
    hv_lon, hv_lat, hv_pid, hv_occ = [], [], [], []

    for r in all_passenger_rows:
        pid = r.get("passenger_id")
        call = r.get("calltime", 0)
        succ = r.get("success")
        arrv = r.get("arrivaltime")
        if succ is not None or latest_time - call > 600 or arrv is not None:
            continue

        dep_str = r.get("dep_node_expanded", "")
        try:
            lon_str, lat_str = dep_str.strip("()").split(",", 1)
            lon, lat = float(lon_str), float(lat_str)
            if not (math.isfinite(lon) and math.isfinite(lat)):
                continue
        except Exception:
            continue

        sid = r.get("shuttleid")
        if sid:
            color = assign_shuttle_color(sid)
            icon = f"/assets/passenger_{color.lstrip('#')}.png"
        else:
            icon = "/assets/passenger_gray.png"

        layers.append({
            "sourcetype": "image",
            "source": icon,
            "coordinates": [
                [lon - d, lat + d],
                [lon + d, lat + d],
                [lon + d, lat - d],
                [lon - d, lat - d],
            ],
            "below": "traces",  # ★ 충돌 방지
        })

        # hover 하나의 trace로 누적
        hv_lon.append(lon); hv_lat.append(lat)
        hv_pid.append(pid); hv_occ.append(get_psgrnum_for_shuttle(pid))

    fig.add_trace(go.Scattermapbox(
        lon=hv_lon, lat=hv_lat,
        mode="markers",
        marker=dict(size=2, opacity=0),
        customdata=list(zip(hv_pid, hv_occ)),
        hovertemplate=("승객 ID: %{customdata[0]}<br>탑승객 수: %{customdata[1]}명<extra></extra>"),
        showlegend=False,
        uid="hover-all-passengers",
    ))

    # (6) mapbox 설정과 layers를 **한 번에** 적용 (중요)
    mapbox_dict = dict(
        style="carto-positron",
        center=dict(lat=37.29994, lon=126.83721),
        zoom=12,
    )
    if layers:
        mapbox_dict["layers"] = layers

    fig.update_layout(
        mapbox=mapbox_dict,      # ★ 한 번에 반영
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False,
        uirevision="static",
        transition_duration=0,   # 안전빵
    )

    return fig, f"최근 업데이트: {latest_time:.0f}"


# ──────────────────────────────────────────────────────────────
# 6) KPI 업데이트 콜백
# ──────────────────────────────────────────────────────────────
# @app.callback: Input이 변경되면 바로 아래있는 함수를 자동으로 실행
@app.callback(
    # Output: 업데이트할 대상들
    [
        Output("total-shuttles",            "children"),
        Output("avg-occupancy",             "children"),
        Output("cumulative_passenger_num", "children"),
        Output("rejection-rate",            "children"),
    ],
    Input("interval","n_intervals") # 실행 트리거
)

def update_kpi(n):
    """
    KPI(핵심 성과 지표) 업데이트 함수
    대시보드의 실시간 지표들을 계산하고 UI에 표시할 형태로 반환
    
    Args:
        n: interval 컴포넌트의 n_intervals 값 (주기적 업데이트 트리거)
    
    Returns:
        tuple: (운영셔틀수, 평균탑승자수, 누적승객수, 거절률) UI 컴포넌트들
    """
    # 1. 운영 중인 셔틀 수 계산 (다음 경로가 남아있는 셔틀)
    running = count_running_shuttles(current_shuttles, shuttle_paths)
    
    # 2. 운영 중인 셔틀들의 평균 탑승자 수 계산
    avg     = compute_avg_occupancy(current_shuttles, shuttle_paths)
    
    # 3. 승객 거절률 계산 (현재 시간까지의 데이터 기준)
    pct     = compute_rejection_rate(cur, latest_time)
    
    # 4. 누적 서비스 승객 수 계산
    # - 성공한 승객 요청만 집계 (success = True/1)
    # - 현재 시간까지의 데이터만 포함
    # - psgrnum이 없으면 기본값 1명으로 처리
    total_served = sum(
        r.get("psgrnum", 1)  # psgrnum 키가 없으면 기본 1명
        for r in all_passenger_rows
        if r.get("success") in (1, True)  # 성공한 요청만
           and r.get("calltime", 0) <= latest_time  # 현재 시간까지
    )
    cumul_num = int(total_served)
    
    # 5. UI 표시용 컴포넌트 생성
    # 운영 셔틀 수 / 전체 셔틀 수 형태로 표시
    total_children = [
        html.Span(str(running)), html.Small("대 / "),
        html.Span(str(TOTAL_SHUTTLES)), html.Small("대"),
    ]
    
    # 평균 탑승자 수 (소수점 1자리)
    avg_children = [
        html.Span(f"{avg:.1f}"), html.Small("명"),
    ]
    
    # 누적 승객 수
    cum_children = [
        html.Span(str(cumul_num)), html.Small("명"),
    ]
    
    # 거절률 (소수점 1자리, % 단위)
    rej_children = [
        html.Span(f"{pct:.1f}"), html.Small("%"),
    ]
    
    return total_children, avg_children, cum_children, rej_children

# ──────────────────────────────────────────────────────────────
# 7) 챗봇 메시지 처리 콜백
# ──────────────────────────────────────────────────────────────
@app.callback(
    Output("chat-output","children"),  # 업데이트할 대상: 챗봇 대화 출력 영역
    [Input("chat-send","n_clicks"),    # 실행 트리거: 전송 버튼 클릭 횟수
     State("chat-input","value"),      # 현재 상태: 사용자 입력 텍스트
     State("chat-output","children")], # 현재 상태: 기존 대화 내역
    prevent_initial_call=True          # 초기 로드 시 콜백 실행 방지
)
def handle_chat(user_msg, history):
    if not user_msg or user_msg.strip()=="":
        raise PreventUpdate

    # Flask REST API로 POST 요청
    try:
        # 1. 요청 설정
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # 2. POST 요청 전송
        response = requests.post(
            "http://127.0.0.1:6789/chat-api", # CHATGPT SERVER 연결
            json={"request_message": user_msg},
            headers=headers,
            timeout=15  # 타임아웃 15초로 설정
        )
        
        # 3. 응답 확인
        response.raise_for_status()
        bot_msg = response.json().get("response_message", "응답 오류")
        
    except requests.exceptions.Timeout:
        bot_msg = "응답 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    except requests.exceptions.ConnectionError:
        bot_msg = "서버에 연결할 수 없습니다. Flask 서버가 실행 중인지 확인해주세요."
    except Exception as e:
        bot_msg = f"오류가 발생했습니다: {str(e)}"

    def bubble(text, who):
        """
        who == "user" → class="chat-bubble user"
        who == "bot"  → class="chat-bubble bot"
        CSS 파일에서 .chat-bubble.user / .chat-bubble.bot 규칙을 정의해 두었으므로
        인라인 스타일은 빼고, className만 붙여 줍니다.
        """
        class_name = f"chat-bubble {who}"  # "chat-bubble user" 또는 "chat-bubble bot"
        return html.Div(
            html.Span(text, className=class_name),
            # 텍스트 정렬을 위해만 style 남김
            style={"textAlign": "right" if who=="user" else "left", "marginBottom": "8px"}
        )


    return (history or []) + [bubble(user_msg,"user"), bubble(bot_msg,"bot")]

# ──────────────────────────────────────────────────────────────
# 8) 셔틀 클릭 → 상세 카드 콜백
# ──────────────────────────────────────────────────────────────
@app.callback(
    Output("shuttle-info-card","children"),
    [Input("map-graph","clickData"), Input("close-shuttle-btn","n_clicks")]
)
def display_shuttle_card(clickData, close_clicks):
    trig = callback_context.triggered_id
    if trig == "close-shuttle-btn":
        return [html.Button("", id="close-shuttle-btn", n_clicks=0,
                            style={"display":"none"})]
    if trig == "map-graph" and clickData and "points" in clickData:
        sid = clickData["points"][0].get("customdata")
        if not sid: raise PreventUpdate
        lon, lat, occ = current_shuttles.get(sid, (None,None,None))
        if lon is None: raise PreventUpdate

        curr_name = next(
            (name for (x,y),name in coord_to_name.items()
             if abs(x-lon)<1e-4 and abs(y-lat)<1e-4),
            "알 수 없음"
        )
        path = shuttle_paths.get(sid, [])
        next_name = path[1]["node_name"] if len(path)>1 else "정보 없음"
        metrics = compute_shuttle_metrics(all_rows, sid, latlon_dict)

        card = dbc.Card([
            dbc.CardHeader([
                html.Span("셔틀 상세 정보"),
                html.Button("×", id="close-shuttle-btn", n_clicks=0,
                            style={"float":"right","border":"none",
                                   "background":"transparent","fontSize":"18px",
                                   "lineHeight":"1","padding":"0 6px","cursor":"pointer"})
            ]),
            dbc.CardBody([
                html.P(f"ID: {sid}", className="card-title"),
                html.P(f"현재 위치: {curr_name}"),
                html.P(f"탑승 인원: {occ}명"),
                html.P(f"다음 위치: {next_name}"),
                html.Hr(),
                html.P(f"평균 탑승자: {metrics['average_occupancy']}명"),
                html.P(f"운행 시간 (h): {metrics['run_time_h']}"),
                #html.P(f"정체 시간 (h): {metrics['idle_time_h']}"),
                #html.P(f"누적 거리 (km): {metrics['total_distance_km']}"),
            ])
        ], color="light", outline=True)
        return [card]

    raise PreventUpdate

@app.callback(
    Output("table-passengers", "data"),
    [
        Input("filter-passenger-id", "value"),
        Input("filter-success", "value"),
        Input("filter-shuttle-id", "value"),
    ]
)
def update_passenger_table(pid, succ, sq):
    """
    all_passenger_rows에서 pid, success, shuttleid 필터를 적용한 후
    결과를 반환합니다.
    """
    return data_utils.get_passenger_records(
        rows=all_passenger_rows,
        pid=pid,
        success_vals=succ,
        shuttle_query=sq
    )


@app.callback(Output("table-vehicles","data"),
              Input("filter-shuttle-id","value"))
def update_vehicle_table(sq):
    return data_utils.get_vehicle_records(all_rows, shuttle_query=sq)

@app.callback(
    Output("wait-error-graph", "figure"),
    Input("interval", "n_intervals")
)

####################################################
def update_wait_error_graph(n):
    df = pd.DataFrame(all_passenger_rows)
    df = df[df["success"].isin([True, 1])]
    if df.empty or not {"boardingtime","calltime","expectedwaitingtime"}.issubset(df.columns):
        return go.Figure()

    df = df.dropna(subset=["boardingtime","calltime","expectedwaitingtime"])
    df["actual_wait"] = df["boardingtime"] - df["calltime"]
    df["wait_error"] = df["expectedwaitingtime"] - df["actual_wait"]

    # 히스토그램 그리기
    fig = px.histogram(
        df,
        x="wait_error",
        nbins=30,
        title="예상 대기시간 – 실제 대기시간 분포",
        labels={"wait_error": "대기시간 차이 (초)"},    # x축 레이블
        color_discrete_sequence=["blue"],            # 막대 파란색
        template="plotly_white"                      # 배경 흰색 테마
    )

    # y축 제목을 "횟수"로 변경, 여백 조정
    fig.update_layout(
        yaxis_title="횟수",
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig
@app.callback(
    Output("travel-error-graph", "figure"),
    Input("interval", "n_intervals")
)
def update_travel_error_graph(n):
    # 1) DataFrame 생성
    df = pd.DataFrame(all_passenger_rows)

    df = df[df["success"].isin([True, 1])]
    # 2) 필요한 컬럼 검사
    need = {"boardingtime", "arrivaltime", "expectedarrivaltime"}
    if df.empty or not need.issubset(df.columns):
        return go.Figure()

    # 3) 실제 이동시간 계산 & 오차 계산
    df = df.dropna(subset=list(need))
    df["actual_travel"] = df["arrivaltime"] - df["boardingtime"]
    df["travel_error"]  = df["expectedarrivaltime"] - df["actual_travel"]

    # 4) 히스토그램 그리기
    fig = px.histogram(
        df,
        x="travel_error",
        nbins=30,
        title="예상 이동시간 – 실제 이동시간 분포",
        labels={"travel_error": "이동시간 차이 (초)"},
        color_discrete_sequence=["blue"],  # 파란색
        template="plotly_white"            # 흰 배경
    )
    fig.update_layout(
        yaxis_title="횟수",
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# ──────────────────────────────────────────────────────────────
# 3) update_rej_area_table 콜백: node_id → 한글 이름 매핑 적용
# ──────────────────────────────────────────────────────────────
@app.callback(
    Output("rej-area-table","data"),
    Input("interval","n_intervals")
)
def update_rej_area_table(n):
    from collections import Counter

    failed = [r for r in all_passenger_rows if r.get("success") is False]
    cnt = Counter()
    for r in failed:
        dep = r.get("dep_node_expanded","")
        try:
            lon, lat = map(float, dep.strip("()").split(",",1))
        except:
            continue
        nid = find_nearest_nodes(lon, lat, node_data, 1)[0]
        cnt[nid] += 1

    top10 = [(nid,c) for nid,c in cnt.items() if c>=1]
    top10.sort(key=lambda x: x[1], reverse=True)
    top10 = top10[:10]

    rows = []
    for nid, c in top10:
        # 문자열 nid → 정수로 변환 시도
        try:
            lookup_id = int(nid)
        except ValueError:
            lookup_id = nid

        # mapping.csv 의 int id와 매칭
        name = node_name_map.get(lookup_id, nid)
        rows.append({"region": name, "count": c})

    return rows


# ──────────────────────────────────────────────────────────────
# 10. 실행
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False,port=7777)
