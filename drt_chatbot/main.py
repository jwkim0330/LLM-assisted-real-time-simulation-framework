from flask import Flask, render_template, request 
import sys
from SetGptModel.ModelSetting import Model
from chatbot import Chatbot
from Character.characters import system_role, instruction
from function_calling import FunctionCalling
from FuncSpecs import func_specs
from response import make_response_rag


# Chatbot 객체 생성
Hanyang = Chatbot(
    model = Model.gpt_4_mini, # GPT 모델
    system_role = system_role,
    instruction = instruction    
)

func_calling = FunctionCalling(model=Model.advanced)

application = Flask(__name__)

@application.route("/")
def hello():
    return "앱에 탑재할 GPT!" 

@application.route("/chat-app")
def chat_app():
    return render_template("chat.html")

@application.route('/chat-api', methods=['POST'])
def chat_api():
    request_message = request.json['request_message'] # 전달받는 message 출력
    print(f"프롬프트를 통해 전달 받는 메시지: {request_message}")
    
    Hanyang.add_user_message(request_message)

    # 직전 봇 응답을 컨텍스트로 활용 (단독 입력 매핑 정확도 향상)
    prev_assistant = ""
    for msg in reversed(Hanyang.context[:-1]):  # 방금 추가한 user 메시지 제외하고 역순
        if msg.get("role") == "assistant":
            prev_assistant = msg.get("content", "")
            break

    #ChatGPT에게 func_specs을 토대로 사용자 메시지에 호응하는 함수 정보를 분석해 달라고 요청
    analyzed_dict=func_calling.analyze(request_message,func_specs,prev_assistant)
    
    # 챗GPT가 함수 호출이 필요하다고 분석헀는지 여부 체크
    if analyzed_dict.get("function_call"): # function_call == True
        # ChatGPT가 분석해 준 대로 함수 호출 및 응답 저장
        response=func_calling.run(analyzed_dict,Hanyang.context[:])
        Hanyang.add_response(response)
        print(f"[main][analyzed_dict] | ChatGPT가 분석해 준 대로 함수 리턴 값 | {response}")
        
    else: # function_call == False
        # Using RAG
        response = make_response_rag(request_message)
        print(response)
        return {"response_message": response}
        
    # context에 있는 최근 응답 추출
    response_message = Hanyang.get_response_content()
    Hanyang.handle_token_limit(response)
    #Hanyang.clean_context()
    
    #Chat에 나올 데이터
    print("[main] 프롬프트에 나올 응답 메시지: ", response_message)
    return {"response_message": response_message}


if __name__ == "__main__":
    application.run(debug=True)