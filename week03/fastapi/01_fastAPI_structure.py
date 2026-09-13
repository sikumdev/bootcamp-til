"""
title: FastAPI 프로젝트 구조 
tags: [fastapi]
"""

#== HTTP 요청은 뭘로 이루어지나

#! 메서드(Method) — 무엇을 하려는가. 동사 역할            GET, POST
#! URL(경로)      — 어디에 요청하는가                  /health, /chat/
#! 헤더(Headers)  — 부가 정보. 메타데이터              Content-Type: application/json
#! 바디(Body)     — 전달할 데이터. 주로 POST 에서 씀    {"message": "안녕"}

#! 조회는 GET, 데이터 보내면서 요청하면 POST.
#! GET 은 바디를 거의 안 씀 → 값을 넘기려면 URL 뒤에 ?key=value 로 붙임.


#== 폴더 구조
#> 한 파일에 다 넣으면 금방 못 찾음. 역할별로 쪼개는 것.

# --8<-- [start:tree]
# my_llm_service/               ← 프로젝트 루트 (uvicorn 실행 위치)
# │
# ├── app/                      ← Python 패키지 (__init__.py 필요)
# │   ├── __init__.py           ← "app 폴더를 Python 패키지로 인식" 선언
# │   │
# │   ├── main.py               ← ① 앱 초기화 + 라우터 등록 (안내 데스크)
# │   ├── dependencies.py       ← ② Depends 주입 대상 (LLM 싱글턴 등)
# │   │
# │   ├── routers/              ← ③ HTTP 엔드포인트 정의 (URL·메서드·파라미터)
# │   │   ├── __init__.py
# │   │   ├── health.py         ←    GET /health
# │   │   └── chat.py           ←    POST /chat/, POST /chat/stream
# │   │
# │   ├── services/             ← ④ 비즈니스 로직 (LLM 호출, 프롬프트, 후처리)
# │   │   ├── __init__.py
# │   │   └── llm_service.py    ←    get_chat_response()
# │   │
# │   └── schemas/              ← ⑤ Pydantic 데이터 모델 (요청·응답 타입 계약서)
# │       ├── __init__.py
# │       └── chat.py           ←    ChatRequest, ChatResponse
# │
# ├── .env                      ← API 키 보관. 절대 Git 에 올리지 않음
# ├── .gitignore                ← .env, .venv/ 포함 필수
# └── requirements.txt          ← pip install -r requirements.txt

# uvicorn app.main:app 로 실행 → 루트에서 실행해야 app 을 찾음
#(1)> __init__.py 는 빈 파일이어도 됨. "이 폴더는 패키지다" 라는 표시일 뿐
#(1)> 이게 없으면 from app.routers import chat 이 실패함
# --8<-- [end:tree]

#! 핵심 규칙 → routers 는 services 를 부르지만, services 는 routers 를 몰라야 함.
#! 화살표가 한쪽으로만 흐르는 것(단방향 의존성).
#! 서로 부르기 시작하면 나중에 순환 임포트로 터짐.


#== main.py — 안내 데스크

# --8<-- [start:main]
# app/main.py
# 역할: 앱 초기화 + 라우터 등록 (안내 데스크)
#(1)> 이 파일은 "어떤 URL을 어느 라우터가 처리하는가"만 담당


from fastapi import FastAPI
from app.routers import chat, health, items
# from app.routers import chat  →  app/routers/chat.py 를 모듈로 임포트
#(2)> → 이 임포트가 성공하려면 app/__init__.py, app/routers/__init__.py 가 존재해야 함


app = FastAPI(
    title="LG CNS AI 서비스",                     # /docs 상단 서비스명
    description="MCP 기반 Agentic AI 서비스 개발자 과정 미니프로젝트",  # /docs 설명
    version="0.1.0",                              # /docs 버전 표시
)


# include_router: "이 라우터를 앱에 연결해라" — 부서를 안내 데스크에 등록하는 것
#(5)> include_router 로 각 파일의 router 를 갖다 붙이는 구조
app.include_router(health.router)
# health.router: health.py 안의 router = APIRouter() 인스턴스
#(3)> prefix 없음 → health.py 안의 @router.get("/health") 가 그대로 /health

app.include_router(chat.router, prefix="/chat", tags=["Chat"])
# prefix="/chat" 
#(4)>   → chat.py 안의:
#(4)>   @router.post("/")       → 실제 등록 URL: POST /chat/
#(4)>   @router.post("/stream") → 실제 등록 URL: POST /chat/stream 
#(4)>   tags=["Chat"] → /docs에서 Chat 그룹으로 묶임

app.include_router(items.router, tags=["Items"])

# --8<-- [end:main]

#! prefix 와 tags 차이
#! prefix="/chat" → 실제 URL 앞에 붙음. 기능에 영향을 줌
#! tags=["Chat"]  → /docs 화면에서 그룹으로 묶는 라벨. 동작에는 영향 없음

#! 흔한 실수 → prefix 를 "/chat/" 처럼 슬래시로 끝내고
#! router 안에도 "/" 를 쓰면 "/chat//" 가 됨.
#! `prefix 는 슬래시 없이 "/chat", router 경로는 "/" 로 시작하는 게 관례.`


#== health.py — 로직 없는 라우터

# --8<-- [start:health]
# app/routers/health.py
# 역할: GET /health 엔드포인트 하나만 담당
# 서비스 로직이 없으므로 services/ 를 임포트하지 않음

from fastapi import APIRouter

router = APIRouter()
# APIRouter(): 이 파일만의 라우터 인스턴스
#(1)> main.py 의 FastAPI() 앱 전체와 다름 — 부서 내 담당자 수준
#(1)> main.py에서 app.include_router(health.router)로 앱에 연결됨

@router.get("/health", tags=["Health"])
# @router.get → APIRouter 인스턴스의 GET 등록 (app.get 이 아님!)
#(2)> "/health" → main.py에서 prefix 없이 등록되므로 실제 URL도 /health
#(2)>  tags=["Health"] → /docs에서 Health 그룹으로 표시

async def health_check():
    """
    서버 상태를 확인합니다.
    로드 밸런서·쿠버네티스·모니터링 도구가 주기적으로 호출합니다.
    이 엔드포인트가 200을 반환하면 "서버 정상"으로 판단합니다.
    """
    return {"status": "ok", "service": "lgcns-ai-service"}
    # dict 반환 → FastAPI가 JSON 자동 변환
    #(3)> 예상 응답: {"status": "ok", "service": "lgcns-ai-service"}
# --8<-- [end:health]


#== async def 를 언제 쓰나

#! I/O 없음 (dict 리턴, 계산만)                   → async def
#! await 붙는 라이브러리 (httpx, asyncpg)         → async def
#! await 안 붙는 라이브러리 (requests, psycopg2)  → def
#! async def 안에서 블로킹 코드(time.time())      → 절대 금지

#! 헷갈렸던 건 첫 줄. health_check 는 I/O 가 없는데 왜 async def 지?
#! 안 기다리는 함수라 이벤트 루프를 막을 일이 없음. 그래서 async def 여도 안전함.
#! 통일해두면 나중에 안에 await 할 일이 생겨도 안 고쳐도 됨.

#! 반대로 requests 처럼 await 를 못 붙이는 라이브러리를 쓸 거면 def 로 둬야 함.
#! 그래야 FastAPI 가 스레드풀로 보내줌. async def 에 넣으면 서버 전체가 멈춤.


#== chat.py — 라우터는 호출만

# --8<-- [start:chat]
# app/routers/chat.py
# 역할: /chat/ URL 수신, service 함수 호출, 응답 반환
# 이 파일은 LLM 호출 방법을 몰라도 됨 — get_chat_response() 를 호출만 함

from fastapi import APIRouter
from app.services.llm_service import get_chat_response
#(1)> services 레이어를 임포트 — routers는 services를 호출하지만 services는 routers를 몰라야 한다! (단방향 의존성)

router = APIRouter()

@router.post("/")
#(2)> prefix="/chat" (main.py에서 등록) + "/" → 실제 URL: POST /chat/
async def chat_endpoint(message: str, session_id: str = "default"):
    """
    AI 채팅 응답 엔드포인트

    현재 기초 버전: message는 쿼리 파라미터로 전달
    → POST /chat/?message=안녕&session_id=s1
    """
    # service 레이어에 실제 처리 위임 — 라우터는 호출만 함
    response = await get_chat_response(message, session_id)

    return {"message": response, "session_id": session_id}
    # 예상 응답: {"message": "안녕하세요!...", "session_id": "default"}

# --8<-- [end:chat]


#== llm_service.py — 실제 로직

# --8<-- [start:service]
# app/services/llm_service.py
# 역할: "실제로 LLM을 어떻게 호출하는가"만 담당
# routers/가 이 파일의 함수를 "호출"만 함 — 로직을 이해할 필요 없이

from dotenv import load_dotenv
load_dotenv()  

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


async def get_chat_response(message: str, session_id: str) -> str:
    """
    사용자 메시지를 받아 LLM 응답 텍스트를 반환합니다.

    Args:
        message   : 사용자 입력 텍스트 (routers/chat.py에서 전달)
        session_id: 세션 식별자
                    현재는 미사용 — 8/18 DB 기반 대화 이력 구현 시 활용 예정
    Returns:
        str: LLM 응답 텍스트 (AIMessage.content)
    """

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

 
    prompt = ChatPromptTemplate.from_messages([
        ("system", "유용한 AI 어시스턴트입니다. 한국어로 친절하게 답하세요."),
        ("human", "{message}"),   # {message} 자리에 사용자 입력이 채워짐
    ])

    chain = prompt | llm         
                                  
    result = await chain.ainvoke({"message": message})


    return result.content

# --8<-- [end:service]

#! 지금은 요청이 올 때마다 llm 을 새로 만들고 있음.
#! 요청 100개면 클라이언트 100개 → lifespan 이나 Depends 로 한 번만 만들게 고쳐야 함.
