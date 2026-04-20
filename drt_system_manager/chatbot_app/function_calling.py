from common import client, model, makeup_response 
import json
from pprint import pprint 
from func_specs import func_specs
from function_collection import calculate_on_time_arrival_rate,search_DB, calculate_passenger_avg_waiting_time,calculate_prediction_error,calculate_boarding_success_rate,calculate_weighted_avg_passengers


# 함수 끝 -----------------------------------------------------------------------------------------    


# 외부 데이터를 가져와 다시 GPT한테 전달한다.
class FunctionCalling:
    
    def __init__(self,model):
        # 딕셔너리 데이터를 통해 함수 스펙에 정의된 함수명과 실제 함수를 연결, GPT가 함수를 호출하라고 알려주면 대응하는 실제 함수를 
        # 찾기 위한 매핑 정보
        self.available_functions={
        
            "search_DB": search_DB,
            "calculate_passenger_avg_waiting_time": calculate_passenger_avg_waiting_time,
            "calculate_prediction_error": calculate_prediction_error,
            "calculate_boarding_success_rate": calculate_boarding_success_rate,
            "calculate_on_time_arrival_rate": calculate_on_time_arrival_rate,
            "calculate_weighted_avg_passengers": calculate_weighted_avg_passengers
        }
        self.model = model
    
    # GPT가 사용자 메시지에 적합한 함수가 무엇인지 분석한다.(처음)
    def analyze(self, user_message, func_specs):
        try:
            response = client.chat.completions.create(
                    model=model.basic,
                    messages=[{"role": "user", "content": user_message}],
                    functions=func_specs,
                    function_call="auto", 
                )
            message = response.choices[0].message
            message_dict = message.model_dump() 
            print()
            print("타임라인: 분석")
            print()
            pprint(("message_dict(받는 메시지 딕셔너리)=>", message_dict))
            return message_dict
        except Exception as e:
            print("Error occurred(analyze):",e)
            return makeup_response("[analyze 오류입니다]")
        
    # analze가 분석한 결과를 입력으로 받아서 실제 함수를 호출한 후 그 결괏값을 바탕으로 최종 응답을 생성
    def run(self, analyzed_dict, context):
        print()
        print("타임라인: run")
        print()
        # analyzed_dict에서 분석한 결과로 이용해야 함수를 쓴다.
        func_name = analyzed_dict["function_call"]["name"]
        print("func_name:",func_name)
        func_to_call = self.available_functions[func_name]
        print("func_to_call:",func_to_call)
        try:
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
            print("func_args:",func_args)
            # 챗GPT가 알려주는 매개변수명과 값을 입력값으로하여 실제 함수를 호출한다.
            func_response = func_to_call(**func_args)
            print("func_response:", func_response)
            context.append({
                "role": "function", 
                "name": func_name, 
                "content": str(func_response)
            })
            # Add system message to request complete but concise information
            context.insert(0, {
                "role": "system",
                "content": "Please include all information from the content. Focus on presenting the facts without unnecessary elaboration.'content'에 있는 정보로만 답변해주세요."
            })
            print("context:", context)
            return client.chat.completions.create(model=self.model,messages=context).model_dump()            
        
        except Exception as e:
            print("Error occurred(run):",e)
            return makeup_response("[run 오류입니다]")