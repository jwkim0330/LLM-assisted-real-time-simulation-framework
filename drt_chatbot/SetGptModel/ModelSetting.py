import os
from openai import OpenAI
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)

class Model: 
    basic: str = "gpt-3.5-turbo-1106"
    advanced: str = "gpt-4-1106-preview"
    gpt_4_mini: str = "gpt-4o-mini"
  
# API_KEY 환경변수에서 가져오기
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")

client = OpenAI(api_key=api_key, timeout=30, max_retries=1)


def makeup_response(message, finish_reason="ERROR"):
    return {
                "choices": [
                    {
                        "finish_reason": finish_reason,
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": message
                        }                   
                    }
                ],
                "usage": {"total_tokens": 0},
            }

                