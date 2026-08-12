"""
title: 스키마와 라우터 — Field 제약 · 토큰 계산
tags: [fastapi]
"""

#== schemas/chat.py — Field 로 제약 걸기

# --8<-- [start:schema]

# Pydantic v2부터는 Optional[str] 대신 str | None 사용을 권장
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """클라이언트가 POST /chat/ 로 보내는 요청 형식."""

    
    message: str = Field(
        min_length=1,                          # 빈 문자열("") 차단 — 빈 프롬프트 방지
        max_length=2000,                       # 과도한 입력 차단 — 토큰 비용 폭탄 방지
        description="사용자 입력 메시지",          # /docs Swagger UI에 표시되는 필드 설명
        examples=["오늘 회의 내용을 요약해줘"],     # /docs Try it out 기능의 예시 값
    )

    
    session_id: str = Field(
        default="default",                     # 클라이언트가 보내지 않으면 "default" 사용
        description="대화 세션 구분자 (LangSmith 트레이스 필터에 활용 가능)",
    )

 
    temperature: float = Field(
        default=0.7,                           # 기본값: 적당히 창의적인 중간값
        ge=0.0,   # ge = greater than or equal → 0.0 미만 값 차단 (음수 방지)
        le=2.0,   # le = less than or equal   → 2.0 초과 값 차단 (OpenAI 허용 범위 상한)
        description="LLM 창의성 조절 (0=매번 같은 답변, 2=매번 다른 창의적 답변)",
    )



class ChatResponse(BaseModel):
    """서버가 반환하는 응답 형식.

    response_model=ChatResponse 로 엔드포인트에 등록하면
    - 내부 전용 필드(예: 원가 정보)가 자동으로 제거됨 (보안)
    - /docs에 응답 스키마가 자동 문서화

    """

    message: str          = Field(description="AI 응답 내용")
    session_id: str       = Field(description="요청과 동일한 세션 ID (대화 추적용)")
    model: str            = Field(description="사용된 LLM 모델명 (예: gpt-4o-mini)")
    tokens_used: int | None = Field(
        default=None,
        description="사용된 토큰 수 — 현재는 None 반환, 향후 비용 추적에 활용 예정"
    )

# --8<-- [end:schema]

#! 여기 description 은 LLM 이 읽는 게 아님. 사람이 /docs 에서 보는 것.
#! 구조화 출력·툴 스키마에서 쓰던 description 과 목적이 다름. 같은 문법인데 독자가 다름.

#! temperature 를 받아놓고 정작 안 쓰고 있음.
#! 쓰려면 요청마다 llm 설정을 바꿔야 하는데, 싱글턴이라 곤란함.→ 체인을 부를 때 넘기는 방법이 따로 있음(with_config)


#== model_config — 모델 전체에 거는 규칙
#> Field 가 필드 하나하나의 규칙이라면, model_config 는 모델 전체의 규칙.
#> ConfigDict 로 씀. 셋 다 기본값이 있어서 안 쓰면 기본 동작으로 감.
 
# --8<-- [start:model_config]
from pydantic import BaseModel, ConfigDict, Field
 
 
class ChatRequest(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        #(1)> 정의 안 한 필드가 오면 422. 기본값은 "ignore" (조용히 버림)
        strict=True,
        #(2)> 타입 변환을 안 해줌. 기본은 맞출 수 있으면 알아서 바꿔 줌
        frozen=True,
        #(3)> 만든 뒤에 필드 수정 불가. request.message = "x" → 에러
    )
 
    message: str = Field(min_length=1, max_length=2000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
# --8<-- [end:model_config]
 
 
#== extra — 모르는 필드가 오면
#> 기본값이 "ignore" 라서 조용히 버림. 이게 은근히 위험함.
 
# --8<-- [start:extra]
# 기본 (extra="ignore")
#(1)> temprature 는 오타. 그런 필드는 없음
#(1)> 근데 200 OK 가 나옴. 오타 필드는 버려지고 temperature 는 기본값 0.7 로 동작

{"message": "안녕", "temprature": 2.0}
 
# extra="forbid"
#(2)> 422 — "temprature 라는 필드는 없다" 고 알려 줌
{"message": "안녕", "temprature": 2.0}

# --8<-- [end:extra]

 
 
#== strict — 타입 변환을 안 해줌
#> 기본은 "바꿔서 맞출 수 있으면 바꿔 줌". strict 는 그걸 끄는 것.
 
# --8<-- [start:strict]
# 기본 (느슨한 모드)
# 문자열인데 float 로 바꿔서 통과시켜 줌
{"temperature": "0.7"}

 
# strict=True
# 422 — float 자리에 str 을 보냈기 때문에
{"temperature": "0.7"}

# --8<-- [end:strict]
 

#== frozen — 만든 뒤 수정 불가
 
# --8<-- [start:frozen]
request = ChatRequest(message="안녕")
request.message = "다른 값"
# ValidationError — frozen 인스턴스는 못 고침
# --8<-- [end:frozen]
 
#! 요청 객체는 FastAPI 가 한 번 만들고 끝이라 바꿀 일이 잘 없음.
#! 지금은 굳이 켤 이유가 없어 보임.
#! 부수 효과로 모델이 hashable 해짐 → dict 키나 lru_cache 인자로 쓸 수 있음.
 
 
#== model_json_schema — /docs 가 만들어지는 원리
 
# --8<-- [start:json_schema]
ChatRequest.model_json_schema()
# {'properties': {'message': {'maxLength': 2000, 'minLength': 1, 'type': 'string'}, ...}
#(1)> Field 에 적은 제약이 그대로 JSON Schema 로 나옴
#(1)> FastAPI 가 /docs 를 자동으로 그리는 게 이걸 읽어서 하는 것
# --8<-- [end:json_schema]
 
#! 우리가 Field 로 적은 게 곧 API 문서가 되는 구조.
#! 문서를 따로 안 써도 되는 이유가 이것. 
#! 외부에 API 명세를 공유해야 하면 이 스키마를 기준으로 주면 됨.
 
 
#== 정리 — Field vs model_config
 
#! Field         → 필드 하나의 규칙 (이 값은 1자 이상, 0~2 사이)
#! model_config  → 모델 전체의 규칙 (모르는 필드는 어떻게, 변환은 할지)
 
#! 지금 켤 만한 것 → extra="forbid" 하나.
#! strict 와 frozen 은 "이런 게 있다" 만 알아두고 필요할 때 켜기.


#== routers/chat.py — v1: 체인만 받기

# --8<-- [start:router_v1]
# ① FastAPI 라우터와 의존성 주입 도구
from fastapi import APIRouter, Depends

# ② LangChain 체인 구성 요소
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import tiktoken

# ③ 이 모듈에서 정의한 의존성과 스키마 임포트
from app.dependencies import get_chain
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/", response_model=ChatResponse)   
async def chat_endpoint(
    request: ChatRequest,                         
    chain: Runnable[dict, str] = Depends(get_chain),  
    #(1)> Depends(get_chain) → 캐시된 체인이 들어옴          
):
    """AI 채팅 엔드포인트 — 검증된 요청을 받아 LLM으로 처리 후 반환."""

    result = await chain.ainvoke({"message": request.message})
    # result 타입: str (StrOutputParser 통과 후)
    # 예상 값: "안녕하세요! 무엇을 도와드릴까요?"

    # 토큰 사용량 측정하기
    enc = tiktoken.encoding_for_model("gpt-4o-mini")

    # 반환은 dict 가 아니라 ChatResponse 객체. FastAPI 가 JSON 으로 바꿔 줌
    return ChatResponse(
        message=result,
        session_id=request.session_id,  
        model="gpt-4o-mini",
        tokens_used=len(enc.encode("유용한 AI 어시스턴트입니다."+request.message))
    )


# --8<-- [end:router_v1]

#! 토큰 계산이 정확하지 않음. 시스템 프롬프트 문자열을 손으로 이어붙여서 셌는데,
#! 실제로 나가는 건 role 구분자 같은 게 더 붙은 형태라 실제보다 적게 나옴.
#! 그리고 출력 토큰은 아예 안 셈. 비용은 입력+출력인데 절반만 센 것.

#! 매 요청마다 encoding_for_model() 을 부르는 것도 낭비.
#! 이것도 lru_cache 로 빼는 게 맞음 (dependencies v2 의 get_encoder).


#== routers/chat.py — v2: 프롬프트도 받아서 정확히 세기

# --8<-- [start:router_v2]
async def chat_endpoint(request: ChatRequest, chain: ChainDep, prompt: PromptDep):
    result = await chain.ainvoke({"message": request.message})

    # format_messages 로 실제 나가는 메시지를 만들어서 셈
    #(1)> 손으로 문자열을 잇는 것보다 정확함. 프롬프트를 고쳐도 계산이 따라감
    #(1)> 다만 이것도 입력 토큰만 센 것
    messages = prompt.format_messages(message=request.message)
    enc = get_encoder()
    tokens_used = sum(len(enc.encode(m.content)) for m in messages)

# --8<-- [end:router_v2]


#== routers/chat.py — v3: usage_metadata 쓰기
#> 제일 정확함. 모델이 알려준 숫자를 그대로 쓰는 것.

# --8<-- [start:router_v3]
    response = await chain.ainvoke({"message": request.message})

    usage = response.usage_metadata
    # {'input_tokens': 24, 'output_tokens': 15, 'total_tokens': 39}
    #(1)> OpenAI 가 청구 기준으로 알려준 값을 받는 것
    #(1)> 입력·출력이 다 들어있어서 비용 계산에 그대로 쓸 수 있음

    return ChatResponse(
        message=response.content,
        session_id=request.session_id,
        model=MODEL_NAME,
        tokens_used=usage["total_tokens"],
    )

# --8<-- [end:router_v3]

#! 이 버전은 체인에 StrOutputParser 가 없어야 함.
#! 파서를 붙이면 결과가 str 이 돼서 .usage_metadata 도 .content 도 없음.
#! v3 를 쓰려면 dependencies 에서 prompt | llm 까지만 반환하도록 고쳐야 함.

#! 세 버전 비교
#! v1 tiktoken 손계산      — 부정확. 입력만, 그것도 대충
#! v2 format_messages    — 입력은 정확. 출력은 못 셈
#! v3 usage_metadata     — 입력·출력 다 정확. 대신 파서를 못 씀

#! 파서도 쓰고 usage 도 받고 싶으면 → 파서를 빼고 라우터에서 .content 를 꺼내면 됨.


#== /docs 문서화 — 어디에 쓰면 어디에 나오나
#> Swagger UI(/docs)는 코드에서 자동으로 만들어짐. 어느 자리에 쓰느냐로 표시 위치가 갈림.

#! 코드 요소                    /docs 에서 위치           역할
#! summary="AI 채팅 응답"       엔드포인트 제목 (굵게)       한 줄 요약
#! description="..."           제목 아래 설명            상세 동작 설명
#! responses={422: {...}}      "Responses" 섹션         실패 케이스 문서화
#! 함수 docstring              "Description" 섹션        마크다운 렌더링
#! Field(examples=[...])       "Schema" > "Example"     Try it out 기본값
#! Field(description=...)      각 필드 옆 ? 아이콘         필드별 설명

# --8<-- [start:docs]
@router.post(
    "/",
    response_model=ChatResponse,
    summary="AI 채팅 응답",
    description="사용자 메시지를 받아 LLM 응답을 반환합니다.",
    responses={
        422: {"description": "입력 검증 실패 — message 가 비었거나 2000자 초과"},
        500: {"description": "LLM 호출 실패"},
    },
    tags=["Chat"],
)
async def chat_endpoint(request: ChatRequest, chain: ChainDep):
    """
    ### 사용 예시

    - 일반 질문: `{"message": "오늘 날씨 알려줘"}`
    - 세션 지정: `{"message": "이어서 설명해줘", "session_id": "s1"}`

    세션별 대화 이력은 추후 지원 예정입니다.
    """
    ...

# 정리
#(1)> summary 와 description 을 둘 다 쓰면 docstring 은 무시됨
#(1)> docstring 은 마크다운이 먹혀서 목록·굵게·코드블록을 쓸 수 있음
#(1)> responses 는 실제 동작에 영향 없음. "이런 에러가 날 수 있다" 는 안내일 뿐
#(1)> 200 응답은 response_model 로 이미 잡히니 여기 안 씀
# --8<-- [end:docs]

#! description 과 docstring 은 같은 자리에 나옴 → 둘 다 쓰면 description 이 이김.
#! 짧으면 description=, 길고 마크다운을 쓰고 싶으면 docstring 으로.

#! 여기까지가 전부 "사람이 읽는" 문서임.
#! 같은 Field(description=...) 인데 툴 스키마에서는 LLM 이 읽었음.
#! 문법은 같고 독자만 다르다는 걸 계속 헷갈리지 말 것.

#! /docs 를 잘 써두면 프론트 개발자한테 따로 설명할 게 줄어듦.

#== 왜 ainvoke 여야 하나 (복습)

#! FastAPI 의 이벤트 루프는 단일 스레드임.
#! invoke() 처럼 LLM 응답을 기다리는 동기 작업이 루프를 점령하면
#! 그 3~10초 동안 모든 다른 요청이 응답 불가 상태가 됨.
#! 접속자 10명 중 1명이 동기 호출을 쓰면 나머지 9명도 피해를 봄.

