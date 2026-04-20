# 함수 스펙 기술 / functions, ChatGPT가 분석할 수 록 함수의 내용을 기술, 위의 함수들에 대한 내용을 정리한다.
func_specs = [
    # search_DB 함수
    {
        "name": "search_DB",
        "description": "scenario_info 테이블에서 셔틀별 특정 컬럼 값을 조회합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "shuttle_id": {
                    "type": "string",
                    "description": "조회할 셔틀 ID (예:SHUTTLE0006,SHUTTLE0004)"
                },
                "select_columns": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {
                                "const": "currenttime",
                                "title": "currenttime",
                                "description": "레코드가 저장된 기준 시각"
                            },
                            {
                                "const": "shuttle_id",
                                "title": "shuttle_id",
                                "description": "셔틀 고유 식별자"
                            },
                            {
                                "const": "shuttle_state",
                                "title": "shuttle_state",
                                "description": "셔틀의 현재 상태 (예: RUNNING, STOPPED)"
                            },
                            {
                                "const": "cur_dst",
                                "title": "cur_dst",
                                "description": "현재 목적지"
                            },
                            {
                                "const": "cur_node",
                                "title": "cur_node",
                                "description": "현재 위치 노드"
                            },
                            {
                                "const": "cur_path",
                                "title": "cur_path",
                                "description": "남은 경로 정보"
                            },
                            {
                                "const": "cur_psgr",
                                "title": "cur_psgr",
                                "description": "현재 탑승 승객 ID 목록"
                            },
                            {
                                "const": "cur_psgr_num",
                                "title": "cur_psgr_num",
                                "description": "현재 탑승 승객 수"
                            }
                        ]
                    },
                    "description": "가져오려는 컬럼 이름들의 리스트",
                    "examples": [
                        ["cur_node", "shuttle_state"],
                        ["cur_dst", "cur_psgr_num"]
                    ]
                },
                
            },
            "required": ["shuttle_id", "select_columns"]
        }
    },
    # calculate_passenger_avg_waiting_time 함수
    {
        "name": "calculate_passenger_avg_waiting_time",
        "description": "승객들의 셔틀 평균 대기 시간을 계산합니다. passengers_kpi 테이블에서 성공적으로 탑승한 승객들의 대기시간(boardingtime - waitstarttime)을 계산하여 평균을 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "returns": {
            "type": "number",
            "description": "평균 대기 시간(초). 소수점 둘째 자리까지 반올림됩니다."
        }
    },
    # calculate_prediction_error 함수
    {
        "name": "calculate_prediction_error",
        "description": "예측 대기 시간과 실제 대기 시간의 차이를 계산합니다. passengers_kpi 테이블에서 예측된 대기 시간(expectedwaitingtime)과 실제 대기 시간(boardingtime - waitstarttime)의 차이를 계산하여 평균 절대 오차(MAE)를 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "returns": {
            "type": "string",
            "description": "예측 오차에 대한 설명과 평균 오차값(초)을 포함한 문자열. 소수점 둘째 자리까지 반올림됩니다."
        }
    },
    # calculate_boarding_success_rate 함수
    {
        "name": "calculate_boarding_success_rate",
        "description": "승객의 탑승 거절률을 계산합니다. passengers_kpi 테이블에서 전체 승객 수와 성공적으로 탑승한 승객 수를 계산하여 (1-성공률)을 백분율로 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "returns": {
            "type": "string",
            "description": "전체 승객 수, 성공한 승객 수, 그리고 성공률(%)을 포함한 설명 문자열. 성공률은 소수점 둘째 자리까지 반올림됩니다."
        }
    },
    # calculate_on_time_arrival_rate 함수
    {
        "name": "calculate_on_time_arrival_rate",
        "description": "셔틀의 정시 도착률을 계산합니다. passengers_kpi 테이블에서 예상 탑승 시간과 실제 탑승 시간을 비교하여 정시 도착률을 백분율로 반환합니다.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "returns": {
            "type": "string",
            "description": "전체 탑승 시도 횟수, 정시 도착 횟수, 그리고 정시 도착률(%)을 포함한 설명 문자열. 정시 도착률은 소수점 둘째 자리까지 반올림됩니다."
        }
    },
    # calculate_weighted_avg_passengers 함수
    {
        "name": "calculate_weighted_avg_passengers",
        "description": "시간 가중 평균을 사용하여 특정 셔틀의 평균 탑승자 수를 계산합니다. scenario_info 테이블에서 지정된 셔틀의 각 시점의 탑승자 수와 시간 정보를 조회하여 시간 간격을 가중치로 사용한 평균을 계산합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "shuttle_id": {
                    "type": "string",
                    "description": "조회할 셔틀 ID (예: SHUTTLE0001)"
                }
            },
            "required": ["shuttle_id"]
        },
        "returns": {
            "type": "string",
            "description": "지정된 셔틀의 시간 가중 평균을 적용한 평균 탑승자 수를 포함한 설명 문자열. 평균값은 소수점 둘째 자리까지 반올림됩니다."
        }
    }
]
