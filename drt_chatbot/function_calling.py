from SetGptModel.ModelSetting import client, Model, makeup_response 
from FuncCollection import search_route, confirm_route
import json



class FunctionCalling:
    # 모델 초기화
    def __init__(self,model):
        # 사용할 수 있는 함수
        self.available_functions={
            "search_route": search_route,
            "confirm_route":confirm_route
        }
        self.model = model
    
    # GPT가 사용자 메시지에 적합한 함수가 무엇인지 분석.
    def analyze(self, user_message, func_specs, prev_assistant_message: str = ""):
        try:
            # 이전 대화 컨텍스트를 포함하여 분석
            messages = [
                {"role": "system",
                    "content": """당신은 DRT 셔틀 호출을 도와주는 라우팅 분석기입니다.

[함수 선택 규칙 — 반드시 준수]
1. 사용자 메시지에 경로 정보(출발지, 도착지, 탑승 인원 중 어느 하나라도)가 포함되면 무조건 `search_route` 함수를 호출하라.
   - 메시지에 없는 인자는 빈 문자열("")로 채워서 호출하라.
   - 절대 자연어로 "탑승 인원 알려주세요" 같이 직접 응답하지 마라. 누락 안내는 search_route 함수의 결과 메시지가 담당한다.
   - 서버는 호출 간 출발지/도착지/인원 상태를 누적하므로, 사용자가 한 항목씩 따로 보내도 그대로 호출하면 된다.

   호출 패턴 예시:
     "맥도날드에서 한대앞역까지"        → search_route(departure="맥도날드", destination="한대앞역", passengers="")
     "신촌역에서 3명"                  → search_route(departure="신촌역", destination="", passengers="3")
     "이대역까지"                      → search_route(departure="", destination="이대역", passengers="")
     "한대앞역에서"                     → search_route(departure="한대앞역", destination="", passengers="")
     "2명"  / "3명이요" / "5"          → search_route(departure="", destination="", passengers="2")
     "한양대"  (주소/장소명 단독)       → search_route(departure="한양대", destination="", passengers="")
        ※ 직전 봇 메시지가 "출발지를…"이면 출발지로, "도착지를…"이면 도착지로 매핑하여 호출하라.

2. 사용자가 경로 확인 응답(예: 웅, 응, 맞다냥, 아니, 다시 등)이면 `confirm_route` 함수를 호출하라.

3. 위 두 패턴이 모두 아닌 순수 일반 대화(인사 "안녕", 잡담, 챗봇 자기 소개 질문 등)일 때만 함수 호출 없이 직접 답하라.

말투: 일반 대화 시에만 모든 문장 끝에 '냥' 또는 '하냥' 등 귀여운 톤. 함수 호출 시에는 말투 신경 쓰지 말고 정확히 호출만 해라.
"""
                },
            ]
            # 직전 봇 응답이 있으면 컨텍스트로 추가 (단독 응답 매핑 정확도 ↑)
            if prev_assistant_message:
                messages.append({"role": "assistant", "content": prev_assistant_message})
            messages.append({"role": "user", "content": user_message})
            # GPT에 분석 요청
            response = client.chat.completions.create(
                    model=Model.gpt_4_mini,
                    messages=messages,
                    functions=func_specs,
                    function_call="auto", 
                )
            #  "auto": 모델이 메시지 생성 vs. 함수 호출 중 스스로 선택
            # "none": 절대 호출 안 함
            # {"type":"function","function":{"name":"..."} }: 지정 함수 강제 

            # message: ChatCompletion(id='chatcmpl-C3vnEFgc7PXxEjCAPSVcYwFnErTEc', 
            #             choices=[Choice(finish_reason='stop', index=0, logprobs=None,
            #             message=ChatCompletionMessage(content='안녕하냥! 무엇을 도와줄까냥? 길 안내가 필요하면 알려주라냥~',
            #             refusal=None, role='assistant', annotations=[], audio=None, function_call=None, tool_calls=None))]
            #             , created=1755053176, model='gpt-4.1-mini-2025-04-14', object='chat.completion', service_tier='default',
            #             system_fingerprint='fp_6f2eabb9a5', usage=CompletionUsage(completion_tokens=24, prompt_tokens=347, total_tokens=371,
            #             completion_tokens_details=CompletionTokensDetails(accepted_prediction_tokens=0, audio_tokens=0, reasoning_tokens=0, rejected_prediction_tokens=0), prompt_tokens_details=PromptTokensDetails(audio_tokens=0, cached_tokens=0)))
           
            message = response.choices[0].message # GPT의 응답 중 content 반환 
            message_dict = message.model_dump() # JSON처리
    
            print(f"[FuncCalling][analyze] GPT에서 전달 받는 메시지 | {message_dict}")
            
            return message_dict
        
        except Exception as e:
            print("Error occurred(analyze):",e)
            if 'insufficient_quota' in str(e) or 'quota' in str(e):
                return makeup_response("API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            return makeup_response("[analyze 오류입니다]")
        
    # analze가 분석한 결과를 입력으로 받아서 실제 함수를 호출한 후 그 결괏값을 바탕으로 최종 응답을 생성
    def run(self, analyzed_dict, context):
        # analyzed_dict에서 분석한 결과로 이용해야 함수를 쓴다.
        func_name = analyzed_dict["function_call"]["name"]
        func_to_call = self.available_functions[func_name]
        print(f"[Function_calling][run] | func_Call == True | 함수[{func_name}]로 결과 도출")
        try:
            # 함수 실행
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
            func_response = func_to_call(**func_args) 
            print(f"[Function_calling][run] | 함수[{func_name}]의 리턴 값 | {func_response}")
            
            # search_route 함수인 경우 바로 응답 반환
            if func_name == 'search_route':
                context.append({
                "role": "function", 
                "name": func_name, 
                "content": str(func_response)
            })
                return {"choices": [{"message": {"content": func_response, "role": "assistant"}}]}
            
            if func_name == 'confirm_route':
                context.append({
                "role": "function", 
                "name": func_name, 
                "content": str(func_response)
            })
                return {"choices": [{"message": {"content": func_response, "role": "assistant"}}]}
            
        
            print("타임라인: function_calling.run() 종료")
        
            return client.chat.completions.create(model=self.model,messages=context).model_dump() 
                   
        except Exception as e:
            print("Error occurred(run):",e)
            if 'insufficient_quota' in str(e) or 'quota' in str(e):
                return makeup_response("API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            return makeup_response("[run 오류입니다]")