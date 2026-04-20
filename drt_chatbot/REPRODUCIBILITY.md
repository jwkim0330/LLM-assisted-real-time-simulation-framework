# RAG 챗봇 재현을 위한 기술 명세 (논문용)

아래 항목을 논문의 방법론(Methodology) 또는 보조 자료에 명시하면 재현 가능성이 확보됩니다.

---

## 1. 임베딩 모델 (Retrieval)

| 항목 | 명세 |
|------|------|
| **모델** | jhgan/ko-sbert-multitask (Hugging Face) |
| **구현** | LangChain `HuggingFaceEmbeddings` |
| **용도** | 사용자 질의 및 지식 문서의 벡터화 |

- **버전 고정 권장**: Hugging Face에서 해당 모델의 커밋 해시 또는 날짜를 명시 (예: `jhgan/ko-sbert-multitask@abc1234` 또는 사용 시점 기록).

---

## 2. 유사도 계산 및 검색

| 항목 | 명세 |
|------|------|
| **유사도 지표** | 쿼리 벡터와 문서 벡터의 내적(dot product) |
| **검색 개수** | Top-1 (가장 유사한 문서 1개만 사용) |
| **문서 사용 임계값** | 150 (내적 > 150일 때만 검색된 문서를 프롬프트에 포함, 이하일 때는 사용자 질의만 사용) |

- **주의**: 내적 값은 임베딩 차원 및 정규화 여부에 따라 스케일이 달라지므로, 동일 모델·동일 설정에서만 150이라는 값이 의미 있음.

---

## 3. 생성 모델 (LLM)

| 항목 | 명세 |
|------|------|
| **모델** | OpenAI gpt-4o |
| **API** | OpenAI Chat Completions (LangChain `ChatOpenAI`) |
| **temperature** | 0.4 |
| **기타 파라미터** | top_p, max_tokens 등은 기본값 사용 시 “기본값 사용”이라고 명시 |

- **재현 시**: 동일 모델명(gpt-4o)과 temperature(0.4) 사용. API 버전/날짜가 실험에 영향을 줄 수 있으면 조회 가능한 범위에서 명시 (예: 사용 기간).

---

## 4. 지식 베이스 (RAG 문서)

| 항목 | 명세 |
|------|------|
| **문서 수** | 5개 |
| **저장 위치** | 코드 내 하드코딩 (`response.py`의 `texts` 리스트) 또는 동일 내용의 `RAG.txt` |
| **내용** | DRT 서비스 운용 지역(한양대 에리카), 챗봇 나이, 호수 공원, 셔틀 대수, DRT 정의 및 특성에 대한 설명문 |

- **재현 시**: 논문 보조 자료 또는 저장소에 위 5개 문장을 그대로 제공하는 것이 좋음.

---

## 5. 프롬프트 및 파이프라인

| 항목 | 명세 |
|------|------|
| **캐릭터/시스템 프롬프트** | “하냥이” 페르소나 정의문 (`character` 문자열)을 모든 생성 단계에 공통 포함 |
| **유사도 > 150** | 프롬프트: “다음 문장을 하냥이가 대답하는 것처럼 말투를 바꿔주세요” + 검색된 문서 1개 |
| **유사도 ≤ 150** | 프롬프트: “다음 문장에 대해 하냥이의 말투로 응답해주세요” + 사용자 입력만 사용 |
| **프레임워크** | LangChain (PromptTemplate, LCEL chain, StrOutputParser) |

- **재현 시**: `character` 전문과 두 가지 프롬프트 템플릿 문구를 보조 자료에 포함하면 재현도가 높아짐.

---

## 6. 소프트웨어 환경

| 항목 | 명세 |
|------|------|
| **언어** | Python 3.x (사용 버전 명시, 예: 3.10) |
| **주요 라이브러리** | numpy, langchain-openai, langchain-community, langchain-core, sentence-transformers(HuggingFace 임베딩 사용 시) |
| **재현 권장** | `requirements.txt` 또는 `environment.yml`로 패키지 버전 고정 |

- 논문에는 “실험 환경” 절에서 Python 버전과 위 라이브러리 이름·버전을 표로 정리하는 것을 권장.

---

## 7. 논문 본문에 넣을 수 있는 요약 문단 (예시)

> RAG 모듈은 다음 설정으로 구성하였다. 질의·문서 임베딩에는 Hugging Face의 한국어 SBERT 모델 jhgan/ko-sbert-multitask를 사용하였고, 유사도는 쿼리·문서 벡터의 내적로 계산하였다. 내적이 150을 초과할 때만 가장 유사한 문서 1개를 검색하여 프롬프트에 포함하였고, 그렇지 않을 때는 사용자 질의만으로 응답을 생성하였다. 생성에는 OpenAI gpt-4o 모델(temperature=0.4)을 사용하였으며, 고정된 캐릭터 프롬프트와 함께 LangChain 기반의 단일 체인으로 응답을 생성하였다. 지식 베이스는 DRT 및 서비스 정보를 담은 5개 문장으로 구성하였다.

---

## 8. 체크리스트 (논문 제출 전 확인)

- [ ] 임베딩 모델명 및 출처(jhgan/ko-sbert-multitask) 명시
- [ ] 유사도 지표(내적) 및 임계값(150) 명시
- [ ] 검색 방식(Top-1) 명시
- [ ] 생성 모델(gpt-4o) 및 temperature(0.4) 명시
- [ ] 지식 베이스 문서 수(5개) 및 대략적 내용 설명
- [ ] Python 버전 및 주요 라이브러리·버전 명시(또는 보조 자료 링크)
- [ ] 캐릭터/프롬프트 요약 또는 보조 자료 제공 여부

이 명세를 논문의 “실험 설정” 또는 “재현 정보”에 반영하면 재현 가능성을 충분히 서술할 수 있습니다.

---

## 9. Chatbot Flow Pseudocode (for Paper)

The following can be used in the Methodology or System Architecture section. All algorithms are in English for direct use in the manuscript.

### Algorithm 1: Chat Response Generation (Chat API)

```
Input:  request_message (user input)
Output: response_message (chatbot response)

 1: CONTEXT ← CONTEXT ∪ { role: "user", content: request_message }
 2: analyzed_dict ← Analyze(request_message, func_specs)     // LLM decides if function call is needed
 3: if analyzed_dict.function_call ≠ null then
 4:     response ← Run(analyzed_dict, CONTEXT)                // execute function and get result
 5:     CONTEXT ← CONTEXT ∪ { role: "assistant", content: response }
 6:     response_message ← GetResponseContent(CONTEXT)
 7:     HandleTokenLimit(CONTEXT)
 8:     return response_message
 9: else
10:     response_message ← MakeResponseRAG(request_message)   // RAG path
11:     return response_message
12: end if
```

---

### Algorithm 2: Function Calling (Analyze and Run)

```
// Analyze: decide whether to call a function and get function name and arguments
Input:  user_message, func_specs (list of function specifications)
Output: message_dict (contains function_call or content)

 1: messages ← [ system_prompt, { role: "user", content: user_message } ]
 2: response ← LLM.chat(messages, functions ← func_specs, function_call ← "auto")
 3: return response.choices[0].message

// Run: execute the chosen function and form the response
Input:  analyzed_dict, context (conversation history)
Output: response (function result or LLM-generated response)

 1: func_name ← analyzed_dict["function_call"]["name"]
 2: func_args ← Parse(analyzed_dict["function_call"]["arguments"])
 3: func_response ← Call(func_name, func_args)    // e.g. search_route, confirm_route
 4: context ← context ∪ { role: "function", name: func_name, content: func_response }
 5: return FormatResponse(func_response)          // this system returns function output as response
```

---

### Algorithm 3: RAG-based Response Generation (MakeResponseRAG)

```
Input:  message (user query)
Output: response_message (chatbot response)

 1: D ← knowledge base document set (texts)
 2: E ← EmbeddingModel  // jhgan/ko-sbert-multitask
 3: q_vec ← E.embed_query(message)
 4: D_vecs ← E.embed_documents(D)
 5: similarity ← q_vec · D_vecs^T                    // dot product (per-document similarity)
 6: sorted_idx ← argmax(similarity)                   // index of most similar document
 7: if similarity[sorted_idx] > θ then               // θ = 150
 8:     retrieved ← D[sorted_idx]
 9:     prompt ← CharacterPrompt + "Rephrase the following in the character's tone: " + retrieved
10: else
11:     prompt ← CharacterPrompt + "Respond to the following in the character's tone: " + message
12: end if
13: response_message ← LLM.generate(prompt)           // gpt-4o, temperature=0.4
14: return response_message
```

---

### Suggested Figure/Algorithm Captions (English)

- **Algorithm 1**  
  Given a user message, the system asks the LLM whether a function call is required. If so, the response is produced via the function-calling path; otherwise, the response is produced via the RAG path.

- **Algorithm 2**  
  Function-calling path: the LLM selects a function and arguments from the specs and user message; the system executes that function and returns its result as the response.

- **Algorithm 3**  
  RAG path: the user query and knowledge base are embedded; the most similar document is retrieved by dot-product similarity. If similarity exceeds threshold θ, that document is used in the prompt; otherwise only the user query is used. The LLM then generates a response in the character’s tone.

---

### One-Paragraph Flow Summary (for Diagram or Main Text)

> On each user input, the system first uses an LLM to decide whether a function call is needed. If so (e.g., search_route or confirm_route), the corresponding function is executed and its result is returned as the response. If not, the RAG module is used: the query and knowledge base are embedded, the most similar document is retrieved by dot-product similarity, and the LLM generates a response in the character’s tone using either the retrieved document (if similarity exceeds θ) or only the user query.
