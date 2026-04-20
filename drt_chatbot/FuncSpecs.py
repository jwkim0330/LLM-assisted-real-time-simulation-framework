# 함수 스펙 기술 / functions, ChatGPT가 분석에 이용
# ChatGPT에게 함수 호출 가이드 제공: 
# 사용자 메시지를 분석해서 어떤 함수를 호출해야 하는지 ChatGPT가 판단할 수 있도록 도움
# 자연어 → 구조화된 데이터 변환: 사용자의 자연어 입력을 파라미터로 변환하는 규칙 정의
# 함수 호출 자동화: 사용자 입력에 따라 적절한 함수를 자동으로 호출하도록 설정


func_specs = [
    {
  "name": "search_route",
  "description": "클라이언트가 입력한 출발지, 도착지, 탑승 인원 값을 단순히 분리합니다. 입력값은 공백이나 특수문자를 포함할 수 있으며, 이를 적절히 처리해야 합니다. 줄바꿈이나 과도한 공백은 제거하고 실제 주소나 명칭만 추출해야 합니다. 또한 탑승인원이 입력된 경우 단위는 제거합니다.",
  "parameters": {
    "type": "object",
    "properties": {
      "departure": {
        "type": "string",
        "description": "출발지 주소 또는 명칭, 입력값의 줄바꿈과 과도한 공백은 제거하고 실제 주소만 추출"
      },
      "destination": {
        "type": "string",
        "description": "도착지 주소 또는 명칭, 입력값의 줄바꿈과 과도한 공백은 제거하고 실제 주소만 추출"
      },
      "passengers": {
        "type": "string",
        "description": "탑승 인원 수, '명' 등의 단위는 제거하고 숫자만 추출",
      }
    },
    "required": ["departure", "destination", "passengers"]
  },
  "examples": [
    {
      "user_message": "강남역에서 홍대입구역까지 2명이서 가고 싶어요",
      "arguments": {
        "departure": "강남역",
        "destination": "홍대입구역",
        "passengers": "2"
      }
    },
    {
      "user_message": "상록구 학사5길1에서 한대앞역까지 1명",
      "arguments": {
        "departure": "상록구 학사5길1",
        "destination": "한대앞역",
        "passengers": "1"
      }
    },
    {
      "user_message": "\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n\n                                                              상록구 학사5길1에서 한대앞역까지 1명",
      "arguments": {
        "departure": "상록구 학사5길1",
        "destination": "한대앞역",
        "passengers": "1"
      }
    },
    {
      "user_message": "서울역에서 인천공항까지 4명 탑승",
      "arguments": {
        "departure": "서울역",
        "destination": "인천공항",
        "passengers": "4"
      }
    },
    {
      "user_message": "잠실역에서 강남역까지 1명",
      "arguments": {
        "departure": "잠실역",
        "destination": "강남역",
        "passengers": "1"
      }
    },
    {
      "user_message": "신촌역에서 이대역까지 3명이서 갈래요",
      "arguments": {
        "departure": "신촌역",
        "destination": "이대역",
        "passengers": "3"
      }
    },
    {
      "user_message": "신촌역에서 3명이서 갈래요",
      "arguments": {
        "departure": "신촌역",
        "destination": "",
        "passengers": "3"
      }
    },
    {
      "user_message": "이대역까지 3명이서 갈래요",
      "arguments": {
        "departure": "",
        "destination": "이대역",
        "passengers": "3"
      }
    }
  ]
},
    {
  "name": "confirm_route",
  "description": "사용자가 경로 정보를 확인했는지 여부를 나타냅니다.",
  "parameters": {
    "type": "object",
    "properties": {
      "confirmed": {
        "type": "boolean",
        "description": "사용자가 정보를 확인했으면 true, 아니면 false"
      }
    },
    "required": ["confirmed"]
  },
   "examples": [
    {
      "user_message": "응",
      "arguments": { "confirmed": True }
    },
    {
      "user_message": "맞아",
      "arguments": { "confirmed": True }
    },
    {
      "user_message": "웅",
      "arguments": { "confirmed": True }
    },
    {
      "user_message": "맞다냥",
      "arguments": { "confirmed": True }
    },
    {
      "user_message": "아니야",
      "arguments": { "confirmed": False }
    },
    {
      "user_message": "아니",
      "arguments": { "confirmed": False }
    },
    {
      "user_message": "다시",
      "arguments": { "confirmed": False }
    },
    {
      "user_message": "다시 알려줘",
      "arguments": { "confirmed": False }
    }
  ]
}



    ]
