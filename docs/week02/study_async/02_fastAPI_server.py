"""
title: FastAPI — 체인을 서비스 API 로 내보내기
tags: [fastapi, async]
"""

#== 서버 구조 및 역할
#> 내 서버는 브라우저에겐 서버, OpenAI 에겐 클라이언트임. 

#! [브라우저] → [내 서버] → [OpenAI]
#!   손님       식당이자 손님    납품업체

#! 내 서버 안에도 층이 나뉨.
#! uvicorn  = 문지기. 8000번 문 열고 HTTP 를 파이썬으로 바꿈. 내 로직은 모름
#! FastAPI  = 매니저. 어느 함수 담당인지 찾고 양식 검사. HTTP 세부는 신경 안 씀
#! 내 코드  = 요리사. 실제 처리

#! uvicorn main:app = "문지기야, 손님 오면 main.py 의 app(매니저)한테 넘겨"
#! asyncio.run() 을 서버 코드에서 안 쓰는 이유 → uvicorn 이 이벤트 루프를 대신 켜줌


#== 첫 서버

# --8<-- [start:first]
from fastapi import FastAPI

app = FastAPI()

# @app.get("/health") = "누가 GET 으로 /health 를 부르면 이 함수 실행"
@app.get("/health")
async def health():
    return {"status": "ok"}

# --8<-- [end:first]

#! 실행: uvicorn main:app --reload
#! main:app  → main.py 파일의 app 객체
#! --reload  → 저장하면 자동 재시작 (개발용)

#! http://127.0.0.1:8000/docs 열면 문서가 자동 생성되고 바로 테스트됨.

#! return {"status": "ok"} 는 파이썬 dict 인데 브라우저엔 JSON 으로 도착함.
#! FastAPI 가 뒤에서 변환해 줌.


#== lifespan — 서버 켤 때 한 번 준비하는 자리

# --8<-- [start:lifespan]
from contextlib import asynccontextmanager

chain = None                      # ① 빈 상자 미리 만들어두기

@asynccontextmanager              # ② 시작/종료 담당이라는 꼬리표
async def lifespan(app: FastAPI):
    global chain                  # ③ 바깥 chain 을 건드리겠다는 선언
    llm = ChatOpenAI(model="gpt-4o-mini")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "너는 친절한 한국어 도우미야."),
        ("human", "{message}"),
    ])
    chain = prompt | llm | StrOutputParser()
    print("서버 시작 - 체인 준비 완료")
    yield                         # ④ 여기서 서버가 돌아감
    print("서버 종료")             # ⑤ 끌 때 실행

app = FastAPI(lifespan=lifespan)  # ⑥ 앱에 연결

# yield 문법
#(1)> yield 위쪽  → 서버 켤 때 1번 (준비)
#(1)> yield         → 서버 돌아가는 동안 여기서 대기
#(1)> yield 아래쪽   → 서버 끌 때 1번 (뒷정리)
#(1)> lifespan=lifespan 은 함수를 부르는 게 아니라 이름만 넘기는 것 (괄호 없음)
# --8<-- [end:lifespan]

#! 왜 필요하냐 → 체인 생성을 엔드포인트 안에 넣으면 요청마다 새로 만듦.
#! 요청 100개면 클라이언트 100개 → 커넥션 폭발.
#! 한 번 만들어놓고 계속 쓰려고 여기서 준비하는 것.

#! global 이 없으면 함수 안에서만 사는 새 변수가 만들어짐.


#== Pydantic 으로 요청 검증

# --8<-- [start:request]
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    #  message: str → 문자열, 필수
    message: str           
    # efault=0.7 → 안 주면 0.7 / ge=0, le=2  → 0 이상 2 이하
    temperature: float = Field(default=0.7, ge=0, le=2)


@app.post("/chat")
async def chat(req: ChatRequest):
    reply = await chain.ainvoke({"message": req.message})
    return {"reply": reply}

# req: ChatRequest 한 줄이 (JSON 받기 → 검사 → 객체 변환 → req 에 넣기) 
#(2)> req 는 객체라서 req.message 처럼 점으로 꺼냄 (dict 아님)
# --8<-- [end:request]

#! 양식을 어기면 애초에 객체가 안 만들어짐 → if 문 검사가 필요 없어짐.

#! Fastapi 는 JSON ↔ 파이썬 객체 변환해줌웹브라우저에서 요청이 오면  JSON → 파이썬 객체 변환
#! 웹브라우저에서 요청이 오면  JSON → 파이썬 객체로 변환
#! 웹브라우저에 응답 보낼때는 파이썬 객체 → JSON 으로 변환
#! 그래서 json.loads/dumps 를 안 씀. 스트리밍만 예외.(스트리밍은 자동변환 기능 없음)

#! 그리고 같은 Pydantic 클래스가 세 군데서 재활용됨.
#! API 검증    → FastAPI 가 스키마로 바꾸고 FastAPI 가 검사 (안에서 끝남)
#! 구조화 출력 → LangChain 이 스키마로 바꿔 보내고 LLM 이 읽음
#! 툴 스키마   → LangChain 이 스키마로 바꿔 보내고 LLM 이 읽음
#! 셋 다 "클래스 → JSON 스키마" 로 바뀌는 건 같음. 누가 바꾸고 누가 읽느냐만 다름.


#== ★ async def + ainvoke 조합
#> 이 파트의 핵심.

#! async def + ainvoke  → 최선. 이벤트 루프를 안 막음
#! def       + invoke   → 돌아감. FastAPI 가 스레드풀로 보내줌
#! async def + invoke   → 서버 전체 정지. 안전한 줄 알고 루프에서 직접 돌림
#! def       + ainvoke  → 불가능. 일반 def 에서는 await 를 못 씀

#! invoke:  A 3초 → B 6초 → C 9초 (줄서기)
#! ainvoke: A·B·C 전부 3초 (동시)
#! A 는 어느 쪽이든 3초로 같은데 C 가 9초에서 3초가 됨.


#== /ping 실험 — 눈으로 확인하기

# --8<-- [start:ping]
@app.get("/ping")
async def ping():
    return {"pong": True}
# --8<-- [end:ping]

#! 터미널 두 개를 띄우고
#! 1번: curl -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d '{"message":"긴 글 하나 써줘"}'
#! 2번: (1번 응답 오기 전에 즉시) curl http://127.0.0.1:8000/ping
#!
#! ainvoke → /ping 이 즉시 응답
#! invoke  → /chat 이 끝날 때까지 /ping 이 안 옴
