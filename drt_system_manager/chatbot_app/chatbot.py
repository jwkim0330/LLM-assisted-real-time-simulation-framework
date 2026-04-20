from common    import client, model, makeup_response
from rag_utils import RAGManager
import math

# Chatbot 설정 및 Chatbot 함수
class Chatbot:
    
    # 객체 생성시 시스템 초기 설정 (모델,GPT 역할,GPT 규칙)
    def __init__(self, model, system_role, instruction):
        self.context = [{"role": "system", "content": system_role}]
        self.model = model
        self.instruction = instruction
        self.max_token_size = 16 * 1024
        self.available_token_rate = 0.9
        self.rag_manager = RAGManager()
    
    # context에 사용자 대화내용 추가
    def add_user_message(self, user_message):
        # RAG를 통한 컨텍스트 생성
        rag_context = self.rag_manager.create_context(user_message)
        
        # 사용자 메시지와 RAG 컨텍스트 결합
        enhanced_message = f"{user_message}\n\n{rag_context}"
        self.context.append({"role": "user", "content": enhanced_message})
    
    # instruction(제한)을 마지막에 설정
    def send_request(self):
        self.context[-1]['content'] += self.instruction
        return self._send_request()
    
    # GPT에 전달
    def _send_request(self):
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=self.context,
                temperature=0,
                top_p=1,
                max_tokens=256,
                frequency_penalty=0,
                presence_penalty=0
            ).model_dump()
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            if 'maximum context length' in str(e):
                self.context.pop()
                return makeup_response("메시지를 짧게 보내주세요")
            else: 
                return makeup_response("챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요]")
            
        return response

    # GPT 응답 저장
    def add_response(self, response):
        self.context.append({
                "role" : response['choices'][0]['message']["role"],
                "content" : response['choices'][0]['message']["content"],
            }
        )

    # 최근 응답 추출
    def get_response_content(self):
        return self.context[-1]['content']
    # 채팅 내용 초기화
    def clean_context(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break
            
    # 누적 토큰 수가 임계점을 넘지 않도록 제어한다.
    def handle_token_limit(self, response):
        try:
            current_usage_rate = response['usage']['total_tokens'] / self.max_token_size
            exceeded_token_rate = current_usage_rate - self.available_token_rate
            if exceeded_token_rate > 0:
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")

