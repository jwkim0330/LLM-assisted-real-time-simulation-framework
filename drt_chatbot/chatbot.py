from SetGptModel.ModelSetting import client, makeup_response
import math

# Chatbot 
class Chatbot:
    # gpt model / system 역할 / 지시사항
    def __init__(self, model, system_role, instruction):
        self.context = [{"role": "system", "content": system_role}]
        self.model = model
        self.instruction = instruction
        self.max_token_size = 16 * 1024
        self.available_token_rate = 0.9
    
    # context에 사용자 대화내용 추가 / [{"role": "system", "content": system_role}] 이후 user의 요청만 추가된다.
    def add_user_message(self, user_message):
        self.context.append({"role": "user", "content": user_message}) # user_message 저장
        
                  
    
    # instruction(제한)을 마지막에 설정 -> 강조
    def send_request(self):
        self.context[-1]['content'] += self.instruction 
        return self._send_request()
    
    # GPT에 User message 저장
    def _send_request(self):
        try:
            # OpenAI API를 통해 채팅 완성 요청을 생성
            # create() 메서드는 GPT 모델에게 메시지를 보내고 응답을 받는 API 호출
            print("context", self.context)
            response = client.chat.completions.create(
                model=self.model,          # 사용할 GPT 모델 
                messages=self.context,     # 이전 대화 내용들
                temperature=0,             # 응답의 창의성 조절 (0: 일관된 응답, 1: 창의적 응답)
                top_p=1,                   # 응답 다양성 조절 (1: 모든 토큰 고려)
                max_tokens=256,            # 응답의 최대 토큰 수 제한
                frequency_penalty=0,       # 자주 사용되는 단어에 대한 페널티
                presence_penalty=0         # 새로운 토픽 도입에 대한 페널티
            ).model_dump()  # Pydantic 모델을 딕셔너리 형태로 변환하여 JSON 직렬화 가능하게 만듦
            
        except Exception as e:
            print(f"Exception 오류({type(e)}) 발생:{e}")
            if 'maximum context length' in str(e):
                self.context.pop()
                return makeup_response("메시지 조금 짧게 보내줄래?")
            elif 'insufficient_quota' in str(e) or 'quota' in str(e):
                return makeup_response("API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요.")
            else: 
                return makeup_response("챗봇에 문제가 발생했습니다. 잠시 뒤 이용해주세요")
            
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

    def clean_context(self):
        for idx in reversed(range(len(self.context))):
            if self.context[idx]["role"] == "user":
                self.context[idx]["content"] = self.context[idx]["content"].split("instruction:\n")[0].strip()
                break
            
   
    def handle_token_limit(self, response):
        try:
            current_usage_rate = response['usage']['total_tokens'] / self.max_token_size
            exceeded_token_rate = current_usage_rate - self.available_token_rate
            if exceeded_token_rate > 0:
                remove_size = math.ceil(len(self.context) / 10)
                self.context = [self.context[0]] + self.context[remove_size+1:]
        except Exception as e:
            print(f"handle_token_limit exception:{e}")

