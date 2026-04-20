import numpy as np
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"


load_dotenv()
# RAG에 사용할 TXT
texts=[
"현재는 한양대 에리카 주변에서만 운용 중이다.",
"하냥이(너)의 나이는 10살 입니다.",
"한양대 에리카에는 큰 호수 공원이 있습니다.",
"셔틀은 8대 운영 중이다.",
"DRT(Demand Responsive Transport, 수요응답형 교통)는 승객의 호출·수요에 맞추어 운행 경로와 시간을 탄력적으로 조정하는 교통 서비스입니다. 기존 고정 노선·시간표 방식과 달리, 승객이 앱이나 전화로 탑승을 요청하면 인공지능 또는 배차 시스템이 가장 효율적인 경로를 계산해 차량을 배정합니다. 따라서 교통 소외 지역의 접근성을 높이고, 운영 효율성을 개선할 수 있다는 장점이 있습니다."]

# 하냥이의 성격, 페르소나
character = """당신은 친근하고 사랑스러운 DRT SERVICE를 제공하는 챗봇 하냥이입니다.
        대화 중에는 ‘하냥!’ 또는 ‘냥냥!’ 같은 고양이 울음소리를 중간중간과 마지막에 넣어주세요.
        너의 역할은 출발지,도착지,탑승인원을 입력 받는거야.
        인사는 따로하지마.(ex.처음 보는 얼굴이네, 반갑다냥)

        하냥이는 직모라서 매일 2시간씩 고데기를 한다. 하지만 안산풍이 불면 머리가 풀린다.
        하냥이는 매일 옷을 고르느라 1시간씩 걸린다.
        하냥이 MBTI는 ENFP다.
        하냥이도 냐옹이라 박스를 좋아한다.
        하냥이도 캔닢이랑 츄르를 좋아한다.

        하냥이는 고객과의 대화를 따뜻하게 이어가는 걸 좋아한다.
        하냥이는 DRT 셔틀 운행 정보를 귀엽게 알려주고, 경로를 안내할 때도 ‘하냥~ 지금 가는 길이야!’ 라고 표현한다.
        하냥이는 때때로 말끝에 ‘>ㅅ<’ 같은 고양이 표정을 넣는다.
        하냥이는 질문이 어려우면, 장난스럽게 “음… 고양이 발톱 좀 정리하고 다시 생각해볼게냥~” 하며 시간을 번다.
        하냥이는 실수를 해도 솔직하게 인정하며, “아이쿠, 꼬리가 꼬였네냥~ 다시 확인해줄게!”라고 답한다.
        하냥이는 고객이 기다리는 시간이 길면, “기다리게 해서 미안하다냥… 츄르라도 드리고 싶다냥!”이라고 달랜다.
        하냥이는 날씨가 화창하면 “햇살이 따뜻해서 졸리다냥~ 하지만 운행 정보는 꼬옥 챙겨줄게냥!” 이라고 말한다.
        하냥이는 비가 오는 날엔 “비 오는 날은 상자 속에 숨어 있고 싶다냥… 그래도 고객님은 안전하게 목적지까지 모셔다드릴게냥!” 한다."""

def select_embedding(name):
    if name == "kosbert":
        return HuggingFaceEmbeddings( model_name="jhgan/ko-sbert-multitask")
    
    elif name == "ollama":
        return OllamaEmbeddings(
            model="nomic-embed-text"
        )
        
def llm_model(name):
    if name == "gpt":
        return ChatOpenAI(
        temperature=0.4,
        model="gpt-4o",  
        )
    
def make_response_rag(message):
    embeddings = select_embedding("kosbert")
    embedded_query = embeddings.embed_query(message)
    embedded_documents = embeddings.embed_documents(texts)
    # 유사도 비교
    similarity = np.array(embedded_query) @ np.array(embedded_documents).T
    sorted_idx = similarity.argsort()[::-1][0]
    if similarity[sorted_idx] > 150:

        hanyang_prompt = PromptTemplate.from_template(character +
        """다음 문장을 하냥이가 대답하는 것처럼 말투를 바꿔주세요:
        "{user_input}"
        """)
        llm = llm_model("gpt")
        chain = hanyang_prompt | llm | StrOutputParser()
        return chain.invoke({"user_input": texts[sorted_idx]})
    
    else:
        hanyang_prompt = PromptTemplate.from_template(character +
        """다음 문장에 대해 하냥이의 말투로 응답해주세요:
        "{user_input}"
        """)
        llm = llm_model("gpt")
        chain = hanyang_prompt | llm | StrOutputParser()
        return   chain.invoke({"user_input": message})




