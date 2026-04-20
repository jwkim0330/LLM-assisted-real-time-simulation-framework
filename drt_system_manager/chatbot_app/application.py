from flask import Flask, render_template, request 
import sys
import json
from common import model
from chatbot import Chatbot
from characters import system_role, instruction
from function_calling import FunctionCalling,func_specs
from rag_utils import RAGManager

# RAG 매니저 초기화
rag_manager = RAGManager()

# knowledge_base.json에서 문서 로드
with open('JSON/knowledge_base.json', 'r', encoding='utf-8') as f:
    knowledge_docs = json.load(f)
    #print("knowledge_docs:", knowledge_docs)
    rag_manager.add_documents(knowledge_docs)

# Chatbot 인스턴스 생성
Hanyang = Chatbot(
    model = model.advanced,
    system_role = system_role,
    instruction = instruction    
)

func_calling = FunctionCalling(model=model.advanced)

application = Flask(__name__)

@application.route("/")
def hello():
    return "웹에 탑재하는 GPT 챗봇!" 

@application.route("/chat-app")
def chat_app():
    return render_template("chat.html")

@application.route('/chat-api', methods=['POST'])
def chat_api():
    
    request_message = request.json['request_message']
    print("request_message:", request_message)
    
    # 먼저 함수 분석 실행
    analyzed_dict = func_calling.analyze(request_message, func_specs)
    if analyzed_dict.get("function_call"):
        response = func_calling.run(analyzed_dict, Hanyang.context[:])
        Hanyang.add_response(response)
        print("response:", response['choices'][0]['message']['content'])
        return {"response_message": response['choices'][0]['message']['content']}
    else:
        # 함수 분석 결과가 없는 경우 RAG 실행
        context = rag_manager.create_context(request_message)
        print("--------------------------context:--------------------------------", context)
        
        if not context.strip() or context.strip() == "관련 정보를 찾을 수 없습니다.":
            # RAG에서도 정보를 찾지 못한 경우
            response = "죄송합니다. 해당 질문에 대한 답변을 찾을 수 없습니다."
            Hanyang.add_response(response)
        else:
            # RAG에서 정보를 찾은 경우
            Hanyang.add_user_message(request_message + "\n\n" + context)
            response = Hanyang.send_request()
            Hanyang.add_response(response)
   
    # 최근 응답 추출
    response_message = Hanyang.get_response_content()
    Hanyang.handle_token_limit(response)
    Hanyang.clean_context()
    print("response_message:", response_message)
    # 출력되는 메시지
    return {"response_message": response_message}


if __name__ == "__main__":
    application.run(debug=True, host='0.0.0.0', port=6789, use_reloader=False)