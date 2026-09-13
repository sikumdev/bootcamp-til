"""
title: SSE 스트리밍
tags: [fastapi]
"""

#== 왜 스트리밍이 필요한가
#> TTFT(Time To First Token) — 사용자가 요청을 보낸 뒤 첫 글자가 화면에 뜨기까지의 시간.

#! 일반 HTTP 방식 → 서버가 답변을 전부 만든 뒤에 한 번에 보냄.
#! 스트리밍 방식 → 서버가 토큰을 만드는 즉시 하나씩 보냄.
#! 사용자는 0.3~0.8초 만에 첫 글자를 보고, 그 뒤로 계속 타이핑되듯 이어짐.

#! 답변이 다 나오기까지 걸리는 총 시간은 두 방식이 똑같음.
#! 서버 입장에서도 이득임. 답변을 다 만들어놓고 보내는 게 아니라
#! 만드는 동시에 보내니까 메모리에 통째로 들고 있을 필요가 없음.


#== 잠깐 — Starlette 이 뭐냐
#> 한 줄로 말하면 "FastAPI 의 부모 클래스".
 
# --8<-- [start:starlette]
 층이 세 겹임

 uvicorn      ← 서버. 포트를 열고 HTTP 요청을 받아 파싱함
    ↓
 Starlette    ← 웹 프레임워크 기본기 (라우팅, Request/Response, 미들웨어)
    ↓
 FastAPI      ← Starlette 을 상속받아 편의 기능을 얹음
    ↓
 내 코드

# 직접 찍어본 결과
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
 
print(FastAPI.__mro__[1])   # <class 'starlette.applications.Starlette'>
#(1)> FastAPI 가 Starlette 을 상속받은 게 맞음
 
print(Request.__module__)            # starlette.requests
print(JSONResponse.__module__)       # starlette.responses
print(StreamingResponse.__module__)  # starlette.responses

# fastapi 에서 import 했지만 실제 출신은 전부 starlette
#(2)> FastAPI 가 편의상 자기 이름으로 다시 내보내 주는 것뿐임
# --8<-- [end:starlette]

#! FastAPI 가 새로 만든 건 생각보다 적음. 핵심은 세 가지.
#! ① Pydantic 자동 검증  ② Depends (의존성 주입)  ③ /docs 자동 생성
#! 웹 프레임워크로서의 기본 동작은 대부분 Starlette 것을 그대로 씀.
 
#! 지금까지 쓴 것 중 Starlette 소속
#! Request · JSONResponse · StreamingResponse · TestClient
#! `@app.middleware` 와 `@app.exception_handler` 는 FastAPI 가 다시 정의하긴 하는데
#! 실제 동작은 Starlette 의 미들웨어 구조 위에서 돌아감.
 
#== Starlette을 알아야 하는 이유

#> ① 에러 메시지에 starlette 경로가 뜸.
#! FastAPI 만 쓴 것 같은데 stack trace 에 starlette/responses.py 가 나오면 당황함.
 
#> ② 검색할 때 유리함. 스트리밍·미들웨어 문제는 FastAPI 문서보다
#! Starlette 문서가 자세함. FastAPI 문서도 "자세한 건 Starlette 보라" 고 넘기는 게 많음.
 
#> 이 노트에서 Starlette 이 주어인 것들 (전부 FastAPI 가 아니라 이 층에서 일어남)
#! · media_type 에 charset=utf-8 을 붙이는 것
#! · 스트리밍 시작 후에는 500 응답을 만들어놓고 버리는 것
#! · 클라이언트가 끊기면 generator 를 취소하는 것


#== HTTP 응답이 어떻게 생겼는지부터
#> SSE 를 이해하려면 "헤더" 와 "바디" 를 먼저 구분해야 함.
#> 서버가 클라이언트에게 보내는 HTTP 응답은 아래 네 부분으로 이루어짐.

# --8<-- [start:http_shape]
HTTP/1.1 200 OK                          ← ① 상태 줄 (성공/실패)
Content-Type: text/event-stream          ┐
Cache-Control: no-cache                  ├ ② 헤더 — 맨 처음 딱 한 번만 나감
X-Accel-Buffering: no                    ┘
                                         ← ③ 빈 줄 — "헤더 끝. 이제부터 바디"
event: message                           ┐
data: {"content": "파"}                   │
                                         │
event: message                           ├ ④ 바디 — 여기가 계속 흘러나오는 부분
data: {"content": "이"}                   │
                                         │
event: message                           ├ ④ 바디 — 여기가 계속 흘러나오는 부분
data: {"content": "썬"}                   │
                                         │
event: done                              │
data: {"content": "[DONE]"}              ┘
# --8<-- [end:http_shape]

#! 헤더는 ② 부분(Content-Type 등)뿐이고, `event:` `data:` 는 ④ 바디 안에 있음.
#! `이름: 값` 이라는 생김새가 헤더랑 똑같아서 착각하기 쉬움. 위치가 다른 것.

#! 서버가 헤더 `Content-Type: text/event-stream` 을 넣는 이유 →
#! 클라이언트에게 "지금부터 보낼 바디는 SSE 형식이니 그렇게 읽어라" 고 알려주는 것.

#! 헤더는 맨 처음 한 번만 나가고 그 뒤로는 바디만 계속 흐름.
#! → 스트리밍이 시작된 뒤에는 상태 코드도 헤더도 절대 못 바꿈. 




#== SSE 응답 끝 알리는 방식
#> 스트리밍 응답에는 `Content-Length` 헤더가 없음.
#> 서버가 답변을 다 만들기 전에 헤더를 먼저 보내야 하는데 그 시점엔 길이를 모르니까.
#> → `그래서 서버는 "언제 끝나는지" 를 다른 방법으로 알려줘야 함.`

#! HTTP/1.1 이면 uvicorn 이 `Transfer-Encoding: chunked` 를 붙여서 그 역할을 함.
#! 조각마다 길이를 앞에 적어 보내고, 마지막에 길이 0 을 보내서 "끝" 을 알리는 방식.
#! → 클라이언트가 "연결이 끊긴 것" 과 "정상적으로 다 받은 것" 을 구분할 수 있음.

# --8<-- [start]
  · TestClient        — 실제 HTTP 를 안 타고 앱을 직접 부르는 거라 아예 안 생김
  · HTTP/2            — 이 헤더 자체가 금지됨. 프레임 구조라 chunked 가 필요 없음
  · 브라우저 개발자도구  — 전송용 헤더라 브라우저가 처리하고 목록에서 빼기도 함
  · nginx 뒤          — 홉 단위 헤더라 프록시가 떼고 자기 방식으로 다시 붙임
 로컬에서 uvicorn 띄우고 `curl -v` 로 보면 HTTP/1.1 이라 보임.

# --8<-- [end]

#! 우리가 실제로 신경 쓸 건 Transfer-Encoding 이 아니라 그 위 줄임
#! → "Content-Length 가 없다" = "서버가 다 만들기 전에 보내기 시작했다".


#== SSE 프로토콜 구조 — 바디에 쓰는 형식
#> 서버가 응답 헤더에 `Content-Type: text/event-stream` 을 넣고,
#> 응답 바디에 아래 형식으로 텍스트를 계속 써 보내면 그게 SSE 임.

# --8<-- [start:protocol]
# (아래는 전부 응답 바디 안의 내용)
event: message
data: {"content": "파"}

event: message
data: {"content": "이"}

event: message
data: {"content": "썬"}

event: done
data: {"content": "[DONE]"}
# --8<-- [end:protocol]

#! 서버가 지켜야 할 규칙이 세 줄이 전부임.
#! `event: [타입]` — 이 이벤트가 무슨 종류인지. 서버가 생략하면 클라이언트는 "message" 로 봄
#! `data: [내용]`  — 실제로 전달할 값
#! 빈 줄 하나       — "이벤트 하나가 여기서 끝났다" 는 구분자

#! 빈 줄이 제일 중요함. 서버가 빈 줄을 안 보내면
#! 규격대로 읽는 클라이언트(브라우저 EventSource)는 "아직 이벤트가 안 끝났나" 하고 계속 기다림 → 화면이 안 갱신됨.
#! 그래서 서버가 만드는 문자열은 반드시 `\n\n` (줄바꿈 두 번) 으로 끝나야 함.

#== SSE 프로토콜 구조 (심화)

#> 우리가 짠 httpx 클라이언트는 `data:` 로 시작하는 줄만 골라 바로 처리함.
#> 그래서 빈 줄이 없어도 우리 테스트는 통과함. but, 브라우저에 붙이면 그때 터짐.


#! 한 이벤트에 `data:` 줄을 여러 개 쓸 수도 있음.
#! 그러면 클라이언트가 줄바꿈으로 이어 붙여서 하나로 만들어 줌.
#! → 여러 줄을 보내는 규격상의 방법이 이거임. 우리는 JSON 방식을 쓰는 것.

#! `우리 서비스가 쓰는 이벤트 타입 3가지`
#! message — 서버가 토큰 하나를 보낼 때
#! done    — 서버가 "답변이 다 끝났다" 고 알릴 때
#! error   — 서버가 "중간에 문제가 생겼다" 고 알릴 때


#== 세 가지 방식 비교 — 왜 SSE 를 고르나

# --8<-- [start:compare]

방식        연결 유지     연결 방식          LLM 적합성       기존 인프라
SSE        유지함        HTTP 연결 유지      최적            그대로 사용
WebSocket  유지함        프로토콜 업그레이드   되지만 과잉설계   추가 설정 필요
폴링        안 함        짧은 요청 반복       비효율           그대로 사용

# 데이터 방향
SSE        서버 → 클라 (한 방향)
WebSocket  서버 ↔ 클라 (양방향)
폴링        클라가 요청할 때만 서버 → 클라
# --8<-- [end:compare]

#! LLM 답변은 서버가 클라이언트에게 일방적으로 흘려보내기만 하면 됨.
#! 답변이 나오는 도중에 클라이언트가 서버로 뭘 보낼 일이 없음.
#! → 양방향 통신인 WebSocket 은 안 쓰는 기능까지 딸려오는 과한 선택.

#! SSE 는 프로토콜을 바꾸지 않음. 그냥 HTTP 응답 하나를 길게 끄는 것뿐임.
#! WebSocket 은 연결을 다른 프로토콜로 승격시켜서 중간 장비 설정을 손봐야 함.

#! `폴링`은 클라이언트가 "다 됐어? 다 됐어?" 를 1초마다 물어보는 방식.
#! 대부분의 요청이 "아직" 이라는 답만 받고 끝나서 낭비가 큼.


#== 서버가 data 를 왜 JSON 으로 감싸나
#> 토큰 문자열을 그대로 넣으면 프로토콜이 깨지는 경우가 있음.

# --8<-- [start:why_json]
# LLM 이 줄바꿈이 들어간 토큰을 뱉었다고 치면
token = "안녕\n반가워"

# ① 서버가 그대로 넣는 경우 → SSE 형식이 깨짐
#(1)> 클라이언트는 중간의 \n 을 보고 "data 필드가 여기서 끝" 이라고 판단함
#(1)> 뒤의 "반가워" 는 알 수 없는 줄로 취급돼서 버려짐
"data: 안녕\n반가워\n\n"

# ② 서버가 JSON 으로 감싸는 경우 → 안전
#(2)> json.dumps 가 실제 줄바꿈을 \\n 이라는 글자 두 개로 바꿔 줌
#(2)> 진짜 줄바꿈이 아니게 되니까 클라이언트가 한 줄로 제대로 읽음
'data: {"content": "안녕\\n반가워"}\n\n'
# --8<-- [end:why_json]

#! "data 는 JSON 형식 권장" 이라고만 배웠는데 이유가 이거였음.
#! SSE 의 data 필드 안에는 실제 줄바꿈 문자가 들어가면 안 됨.
#! JSON 으로 감싸면 줄바꿈이 자동으로 안전한 형태로 바뀜.
#! LLM 이 코드블록이나 목록을 답변으로 주면 줄바꿈이 반드시 나옴 → 사실상 필수임.


#== yield 가 뭐냐 — generator 기초
#> return 은 값을 주고 함수가 끝남. yield 는 값을 주고 그 자리에 멈춰 있음.

# --8<-- [start:yield]
def f():
    yield 1
    yield 2
    yield 3


for x in f():
    print(x)
# 1
# 2
# 3
# --8<-- [end:yield]

#! return 은 "다 만들어서 한 번에 준다", yield 는 "하나씩 그때그때 준다".
#! LLM 은 토큰을 하나씩 뱉으니까 우리 함수도 yield 구조여야 맞음.

#! 함수 안에 yield 가 하나라도 있으면 그 함수는 generator 가 됨.
#! `f()` 를 불러도 함수 몸통이 바로 안 돌아감. `for 로 돌리기 시작해야 실행됨.`


#== 네 가지 함수 유형 — async generator 의 자리
#> "동기냐 비동기냐" × "한 번 반환이냐 여러 번 반환이냐" 조합.

# --8<-- [start:four_types]
import asyncio


def f1():
    return [1, 2, 3]
    

def f2():
 #(2)> generator — 하나씩 주긴 하는데 동기라서 안에서 await 을 못 씀
    yield 1
    yield 2
   

async def f3():
    #(3)> async 함수 — 기다릴 수는 있는데 반환은 결국 한 번뿐
    await asyncio.sleep(0)
    return [1, 2, 3]


async def f4():
     #(4)> async generator — 기다릴 수도 있고 하나씩 줄 수도 있음. 이게 우리가 쓸 것
    for i in [1, 2, 3]:
        await asyncio.sleep(0)
        yield i

# 부르는 쪽 문법이 유형마다 다름
result1 = f1()                 
for x in f2():                 
    print(x)


async def main():
    result3 = await f3()       # await
    async for x in f4():       # async for  ← 오늘 쓰는 패턴
        print(x)


asyncio.run(main())
# --8<-- [end:four_types]

#! LLM 토큰 스트리밍에 필요한 조건이 두 개임.
#! ① 우리 코드가 LLM 응답을 기다려야 하니까 → 비동기 필수
#! ② LLM 이 토큰을 여러 개 주니까 → 여러 번 반환 필수
#! 둘을 동시에 만족하는 건 async generator 하나뿐. 그래서 이걸 씀.

#! `async def` 안에 `yield` 가 있으면 async generator 임.
#! 부를 때 `await f4()` 가 아니라 `async for x in f4()` 로 씀. 문법이 다름.


#== 전체 데이터 흐름 — 우리가 만드는 건 3번 하나

# --8<-- [start:flow]
1. 사용자 → 서버   POST /chat/stream, 바디 {"message": "질문"}
      ▼
2. LangChain      chain.astream(...) 이 토큰을 하나씩 뱉음
      │             (LangChain 이 이미 async generator 로 만들어 둔 것)
      ▼
3. 우리 코드       token_generator() 가 토큰을 SSE 문자열로 바꿔서 yield
      │             "event: message\ndata: {...}\n\n"
      ▼
4. FastAPI        StreamingResponse 가 그 문자열을 HTTP 바디로 흘려보냄
      ▼
5. 클라이언트      curl -N / httpx / 브라우저가 한 줄씩 받아서 화면에 출력
# --8<-- [end:flow]

#! 우리가 짜는 3번의 유일한 책임 = "LangChain 이 준 토큰 → SSE 형식 문자열" `변환`
#! 토큰을 만드는 건 LangChain 이 하고, HTTP 로 보내는 건 FastAPI 가 알아서 함.

#! 역할이 이렇게 나뉘어 있어서 생기는 함정이 하나 있음 → 에러 처리 (아래에서 다룸).


#== sse_event 유틸 — 우리가 만드는 변환 함수

# --8<-- [start:sse_util]
# app/utils/sse.py
import json


def sse_event(data: str, event: str = "message") -> str:
    """토큰 문자열을 받아 SSE 형식 문자열로 바꿔서 돌려준다."""
    return (
        f"event: {event}\n"
        f"data: {json.dumps({'content': data}, ensure_ascii=False)}\n\n"
        #(1)> ensure_ascii=False — 이걸 안 주면 json.dumps 가 한글을 \uc548\ub155 처럼 바꿔버림. 
        #(1)> 동작은 하는데 로그로 볼 때 못 읽고 용량도 커짐
        #(1)> 문자열 끝이 \n\n 인 게 중요. 빈 줄 하나가 "이벤트 끝" 표시라서
    )


if __name__ == "__main__":
    print(repr(sse_event("안녕")))
    # 'event: message\ndata: {"content": "안녕"}\n\n'

    print(repr(sse_event("[DONE]", event="done")))
    # 'event: done\ndata: {"content": "[DONE]"}\n\n'

# --8<-- [end:sse_util]

#! 관례가 콜론(:) 뒤에 공백 있는 쪽이라 공백을 넣는 걸로 통일함.
#! 대신 클라이언트에서 자를 때 그 공백을 고려해야 함 (아래 클라이언트 코드 참고).


#== repr() 이 뭐냐
#> 파이썬이 값을 "코드에 적었을 때의 모습" 으로 보여주는 함수.

# --8<-- [start:repr]
s = "안녕\n반가워"

print(s)
#(1)> 안녕
#(1)> 반가워        ← \n 이 실제 줄바꿈으로 동작해서 눈에 안 보임

print(repr(s))
#(2)> '안녕\n반가워'  ← \n 이 글자 그대로 보이고 따옴표까지 붙음
# --8<-- [end:repr]

#! SSE 는 줄바꿈이 몇 개인지가 곧 프로토콜임.
#! print 로 찍으면 줄바꿈이 실제 줄바꿈으로 동작해서 몇 개인지 셀 수가 없음.
#! repr 로 찍어야 `\n\n` 이 제대로 두 개 들어갔는지 눈으로 확인됨.
#! 공백·줄바꿈·탭이 문제될 때 꺼내 쓰는 디버깅 도구라고 생각하면 됨.


#== 스트리밍 엔드포인트 v1 → v2 → v3

# --8<-- [start:router_imports]
# app/routers/chat.py — 아래 v1~v3 이 공통으로 쓰는 것들
import asyncio
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.dependencies import get_llm
from app.schemas.chat import ChatRequest
from app.utils.sse import sse_event

logger = logging.getLogger(__name__)
router = APIRouter()

prompt_template = ChatPromptTemplate.from_messages([
    ("system", "유용한 AI 어시스턴트입니다."),
    ("human", "{message}"),
])
# --8<-- [end:router_imports]

# --8<-- [start:v1]
# v1 — 서버가 토큰만 그대로 던짐
@router.post("/stream-v1")
async def chat_stream_v1(request: ChatRequest, llm: ChatOpenAI = Depends(get_llm)):
    chain = prompt_template | llm | StrOutputParser()

    async def generate():
        async for token in chain.astream({"message": request.message}):
            yield token

    return StreamingResponse(generate(), media_type="text/event-stream")
    #(1)> 화면에 글자는 나옴. 근데 클라이언트가 "언제 끝났는지" 를 알 방법이 없음
# --8<-- [end:v1]

# --8<-- [start:v2]
# v2 — 서버가 SSE 형식으로 감싸고 종료 신호도 보냄
@router.post("/stream-v2")
async def chat_stream_v2(request: ChatRequest, llm: ChatOpenAI = Depends(get_llm)):
    chain = prompt_template | llm | StrOutputParser()

    async def generate():
        async for token in chain.astream({"message": request.message}):
            yield sse_event(token)
        yield sse_event("[DONE]", event="done")
        #(1)> 서버가 이 신호를 보내야 클라이언트가 "다 받았다" 를 판단할 수 있음

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        #(2)> Starlette 이 이 값을 응답 헤더의 Content-Type 으로 넣어 줌
        headers={"Cache-Control": "no-cache"},
        #(3)> 중간 프록시가 이 응답을 캐싱해서 다음 사람에게 재사용하는 걸 막음
    )
# --8<-- [end:v2]

# --8<-- [start:v3]
# v3 — v2 + 에러 처리 + 프록시 버퍼링 방지
@router.post("/stream")
async def chat_stream(request: ChatRequest, llm: ChatOpenAI = Depends(get_llm)):
    chain = prompt_template | llm | StrOutputParser()

    async def token_generator():
        try:
            async for token in chain.astream({"message": request.message}):
                yield sse_event(token)
            yield sse_event("[DONE]", event="done")

        except Exception:
            logger.exception("스트리밍 중 에러")
            yield sse_event("응답 생성 중 오류가 발생했습니다.", event="error")
            #(1)> 서버가 str(e) 를 그대로 보내면 안 됨. 내부 정보가 클라이언트에 노출됨
            #(1)> 상세 내용은 서버 로그에만, 클라이언트에는 안전한 문구만

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            #(2)> nginx 에게 "응답을 모아뒀다 보내지 말고 오는 대로 흘려보내" 라고 지시
            #(2)> 이 헤더가 없으면 로컬에선 되던 게 배포 후에 갑자기 안 됨
        },
    )
# --8<-- [end:v3]

#! `v1 → v2 차이`: 서버가 SSE 형식으로 감싸고 [DONE] 신호를 추가
#! `v2 → v3 차이` : 서버가 try/except 로 에러를 잡고, 버퍼링 방지 헤더를 추가


#! `media_type` 은 FastAPI(Starlette) 쪽 파라미터 이름, `Content-Type` 은 HTTP 헤더 이름.
#!  media_type="text/event-stream" → content-type: text/event-stream; charset=utf-8
#! text/ 로 시작하면 Starlette 이 charset=utf-8 을 자동으로 덧붙임.



#== 에러는 반드시 generator "안에서" 잡아야 함
#> 스트리밍에서 제일 중요한 함정. 앞의 "헤더는 한 번만 나간다" 와 이어지는 얘기.

# --8<-- [start:error_trap]
일반 엔드포인트 — 서버가 상태 코드를 정할 기회가 남아 있음
[서버가 처리 다 함] → [에러 발생] → [500 으로 응답 생성] → [전송]
                                       ↑ 여기서 바꿀 수 있음

 스트리밍 — 서버가 이미 200 을 보낸 뒤에 에러가 남
[200 OK + 헤더 전송] → [토큰...] → [토큰...] → [여기서 터짐]
    ↑ 이미 클라이언트에 도착했음. 되돌릴 방법이 없음

# --8<-- [end:error_trap]

#! 서버가 StreamingResponse 를 return 하는 순간 상태 코드 200 과 헤더가 이미 나감.
#! 그 뒤에 무슨 일이 나도 서버는 500 으로 못 바꿈.

#! 전역 예외 핸들러는 어떻게 되냐 → 실행은 됨. 근데 결과가 버려짐.
#! Starlette 이 "응답이 이미 시작됐나?" 를 확인하고, 시작됐으면 핸들러가 만든 500 응답을 안 보내고 그냥 예외를 다시 던짐.
#! → 로그는 남지만 클라이언트는 500 을 못 받음. 그래서 소용이 없는 것.

#! 그래서 유일한 방법이 "generator 안에서 서버가 직접 잡아서
#! event: error 라는 이벤트를 바디에 실어 보내기".

#! 클라이언트 입장에서는 상태 코드 200 을 받았는데 실패한 상황이 됨.
#! → 프론트가 status_code 만 보면 전부 성공으로 착각함. 이걸 알려줘야 함.


#== asyncio.sleep(0) 은 뭐하는 건가

# --8<-- [start:sleep_zero]
async def token_generator():
    async for token in chain.astream({"message": request.message}):
        yield sse_event(token)
        await asyncio.sleep(0)
        #(1)> 0초를 기다리라는 게 아님. "이벤트 루프야 제어권 잠깐 가져가" 라는 뜻
        #(1)> 대기 중인 다른 요청이 끼어들 기회를 주는 것
# --8<-- [end:sleep_zero]

#! 사실 `async for` 로 astream 을 돌리면 그 안에서 이미 await 이 걸림
#! → 제어권이 자동으로 넘어감. 그래서 없어도 대부분 잘 돌아감.
#! 안전장치로 넣어두는 관례에 가까움. 


#== 클라이언트가 SSE 를 받는 코드

# --8<-- [start:client]
import asyncio
import json

import httpx

BASE_URL = "http://localhost:8000"


async def stream_chat(message: str, session_id: str = "test"):
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60) as client:
        async with client.stream(
            "POST", "/chat/stream",
            json={"message": message, "session_id": session_id},
        ) as resp:
            print(f"상태 코드: {resp.status_code}")

            async for line in resp.aiter_lines():
                #(1)> 응답 바디를 한 줄씩 읽음. 다 받을 때까지 안 기다림
                if not line.startswith("data:"):
                    continue
                    #(2)> event: 줄과 빈 줄은 건너뜀. data: 줄만 처리하면 됨

                data = json.loads(line.removeprefix("data:").strip())
                #(3)> removeprefix + strip 이면 공백이 있든 없든 똑같이 동작
                content = data.get("content", "")

                if content == "[DONE]":
                    print("\n완료")
                    break

                print(content, end="", flush=True)
                #(4)> flush=True — 파이썬은 출력을 모아뒀다 한꺼번에 내보내는 습관이 있음
                #(4)> 그걸 끄고 즉시 화면에 찍어야 실시간으로 보임


asyncio.run(stream_chat("파이썬이 뭐야?"))
# --8<-- [end:client]

#! `timeout=60` 을 꼭 줘야 함. httpx 기본 타임아웃이 5초라 긴 답변에서 끊김.

#! 여기 "버퍼링" 이 세 군데나 나옴. 헷갈리지 말 것.
#! `nginx 버퍼링`   → X-Accel-Buffering: no 로 끔 (서버 앞단)
#! `httpx 버퍼링`  → client.stream() 을 쓰면 안 모음 (일반 client.post() 는 모음)
#! `print 버퍼링`  → flush=True 로 끔 (내 터미널)
#! 셋 중 하나만 켜져 있어도 실시간으로 안 보임.

#! curl 로 확인할 때는 `-N` 옵션 필수. 없으면 curl 이 모아뒀다 한 번에 보여줌.
#! `curl -N -X POST localhost:8000/chat/stream -H "Content-Type: application/json" -d '{"message":"안녕"}'`




#==  클라이언트가 중간에 끊으면
#> 사용자가 탭을 닫거나 "정지" 를 누르는 경우.

# --8<-- [end:client]
- 연결이 끊기면 Starlette 이 우리 generator 를 취소함.
- 이때 generator 안으로 asyncio.CancelledError 나 GeneratorExit 가 던져짐.
- 둘 다 Exception 이 아니라 BaseException 밑에 있음 → `except Exception` 이 못 잡음.
- 예외 핸들러 정리할 때 나온 BaseException 구조랑 똑같은 이유임.

- 취소가 제대로 전파되면 astream 도 같이 멈춤 → OpenAI 생성도 중단됨.
- 즉 "끊으면 무조건 돈이 계속 나간다" 는 아님. 정상 동작하면 멈춤.

# --8<-- [end:client]

#! 다만 취소가 전파 안 되는 구성이 있음. BaseHTTPMiddleware(@app.middleware) 를
#! 끼우면 끊김 감지가 제대로 안 돼서 서버가 계속 도는 경우가 알려져 있음.
#! → 아무도 안 보는 답변을 계속 만들면서 돈만 씀.
#! 그래서 "된다고 가정" 하지 말고 실제로 끊어보고 로그로 확인해야 함.


#== 미들웨어가 스트리밍에 영향을 줌

#! 앞서 만든 `@app.middleware("http")` 요청 로깅 미들웨어를 주의할 것.
#! 이 방식은 응답을 통째로 모아뒀다 보내는 건 아님 — 조각 단위로 넘겨주긴 함.
#! 대신 중간에 한 겹이 더 끼는 구조라 두 가지가 걸림.
#!  · 조각마다 거쳐 가느라 오버헤드가 붙음
#!  · 위에서 말한 끊김 감지가 제대로 안 될 수 있음

#! 스트리밍이 안 흐를 때 의심 순서
#! ① 클라이언트 쪽 — curl 이면 -N, python 이면 flush=True, httpx 면 client.stream()
#! ② X-Accel-Buffering 헤더가 있는지 (nginx 뒤에 있을 때)
#! ③ 미들웨어를 잠깐 빼보기


#== 정리

#! SSE              — 서버가 응답 바디에 정해진 텍스트 형식을 계속 써 보내는 방식
#! Content-Type     — 서버가 응답 헤더에 넣어 "바디를 SSE 로 읽어라" 고 알리는 것
#! async generator  — 기다릴 수도 있고 값을 하나씩 줄 수도 있는 함수. 스트리밍의 핵심
#! sse_event        — 토큰을 SSE 형식 문자열로 바꾸는 우리 유틸 함수
#! StreamingResponse — generator 를 받아 HTTP 바디로 흘려보내는 FastAPI 클래스

#! 제일 중요한 것 하나만 고르면 → "에러는 generator 안에서 잡아야 한다".
#! 헤더와 상태 코드가 이미 나간 뒤라 바깥에서는 손쓸 방법이 없음.

