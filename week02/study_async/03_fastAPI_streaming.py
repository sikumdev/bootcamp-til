"""
title: 스트리밍 
tags: [fastapi, langchain]
"""

#== 목적
#> 총 시간은 같아도 체감이 완전히 다름.
#> 20초 침묵 후 완성된 답 vs 0.5초 후 글자가 흐르기 시작.

#== yield — 되는 대로 하나씩
 
# --8<-- [start:return_vs_yield]

# return = 값 하나 주고 함수 끝
def f():
    return 1
    return 2      # 여기까지 안 옴. return 은 함수를 끝냄
 
# yield  = 값 하나 주고 그 자리에서 멈춰 있음. 또 달라고 하면 이어서 실행
def g():
    yield 1
    yield 2       # 여기도 실행됨. yield 는 잠깐 멈출 뿐

# --8<-- [end:return_vs_yield]
 
# --8<-- [start:yield]
def count():
    for i in range(3):
        print("만드는 중", i)
        yield i
 
for x in count():
    print("받음", x)

# 만드는 중 0
# 받음 0
# 만드는 중 1
# 받음 1
# 만드는 중 2
# 받음 2
# --8<-- [end:yield]
 
#! yield i 의 i 가 그대로 for 문의 x 로 들어감.
#! for x in [0, 1, 2] 랑 결과는 같음.
#! 다른 건 리스트는 세 개가 '이미' 다 있고, 제너레이터는 필요할 때 하나씩 만든다는 것.
 

#== 함수를 불러도 실행이 안 됨
 
# --8<-- [start:gen_object]
def count():
    for i in range(3):
        print("만드는 중", i)
        yield i

gen = count()
print(gen)
# <generator object count at 0x7f...>
#(1)> for 를 돌려야 그때부터 움직임 (혹은 next() 사용해서 하나씩 꺼낼 수 있음)

# next() 제너레이터에서 값을 하나만 꺼내는 함수
print(next(gen))
# 만드는 중 0
# 0

print(next(gen))
# 만드는 중 1
# 1

print(next(gen))
# 만드는 중 2
# 2

next(gen, "끝")     # 더 없으면 "끝" 을 돌려줌


# --8<-- [end:gen_object]
 
#! async def 를 그냥 부르면 코루틴 객체만 나왔던 거랑 같은 원리.
#! yield 가 있으면 코루틴 대신 제너레이터 객체가 나옴.
 
 
#== async 버전
 
# --8<-- [start:ayield]
async def acount():
    for i in range(3):
        print("  만드는 중", i)
        await asyncio.sleep(0.5)
        yield i
 
async def main():
    async for x in acount():
        print("받음", x)
 
asyncio.run(main())
#   만드는 중 0
# 받음 0          ← 0.5초 뒤
#   만드는 중 1
# 받음 1          ← 다시 0.5초 뒤
#   만드는 중 2
# 받음 2
#(1:17)> for 가 아니라 async for. 하나씩 '도착하는' 걸 받을 때 씀
#(1)> 안에 await 가 있어서 async 가 붙은 것. 기다리는 동안 다른 일을 할 수 있음
#(1)> acount() 를 부르면 async_generator 객체가 나옴. 역시 바로 실행 안 됨
# --8<-- [end:ayield]
 
#! for       → 리스트가 다 준비돼 있을 때
#! async for → 하나씩 도착하는 걸 받을 때
 
#! llm.astream() 이 내부적으로 하는 일이 정확히 이것.
#! 토큰이 도착할 때마다 yield chunk 를 하는 함수임. 그래서 async for 로 받는 것.

#== SSE — 브라우저에 글자 흘려보내는 약속된 형식

#! data: 안녕\n\n
#! data: 하세요\n\n
#! "data: " 로 시작하고, 빈 줄 두 개(\n\n)가 "한 조각 끝" 신호.
#! 서버 → 클라이언트 한 방향임. 양방향은 WebSocket 인데 LLM 응답엔 SSE 로 충분.


#== 엔드포인트와 token_stream 의 관계
#> 요청을 받는 건 엔드포인트고, token_stream 은 내보낼 조각을 만드는 함수임.
 
# --8<-- [start:pair]

@app.post("/chat")
async def chat(req: ChatRequest):
    reply = await chain.ainvoke({"message": req.message})
    return {"reply": reply}


# ① 요청을 받는 자리 — 브라우저가 POST /stream 을 부르면 여기가 실행됨
#(1)> 웹브라우저에서 endpoint로 요청이 오는 경우 실행
@app.post("/stream")
async def stream(req: ChatRequest):
    return StreamingResponse(
        # req.message 만 뽑아서 아래 함수에 넘겨줌
        #(2)> token_stream(...) 은 여기서 실행되는 게 아님. 제너레이터 객체만 만들어짐
        #(2)> StreamingResponse 가 그걸 쥐고 하나씩 뽑아 보냄
        token_stream(req.message),        
        media_type="text/event-stream",
    )

# ② 내보낼 조각을 만드는 자리 
#(4)> 웹브라우저에 응답을 보내기 위해서 원래는 Fastapi가 Json으로 변환해줬지만 
#(4)> StreamingResponse만 예외임(자동 변환 기능이 없음) → 직접 변환 해줘야함
async def token_stream(message: str):
    async for chunk in chain.astream({"message": message}):
        yield f"data: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# 데이터 변환 과정
#(3)> chunk 는 토큰 조각 문자열 (파서를 붙였으니 str)
#(3)> 그걸 dict 로 감싸고 → json.dumps 로 글자로 만들고 → SSE 형식으로 포장
#(3)> /chat 앤드포인트 에서는 FastAPI 가 자동으로 해주던 JSON 변환을 여기선 직접 하는 것
# --8<-- [end:pair]
 
#! /chat 은 return {"reply": ...} 로 끝났는데 /stream 은 왜 이렇게 복잡하냐 →
#! /chat  : 답이 다 나온 뒤 dict 한 개를 return → FastAPI 가 JSON 으로 바꿔서 보냄
#! /stream: 답이 나오는 중에 조각을 계속 내보내야 함 → return 을 한 번밖에 못 씀
#!          그래서 yield 로 여러 번 내보내는 함수를 따로 만들어 통째로 넘기는 것
 
#! 역할 분담
#! stream()          → 요청 받고 검증 (ChatRequest)
#! token_stream()    → 뭘 보낼지 만듦 (내용물)
#! StreamingResponse → 어떻게 보낼지 처리 (배송 방식)
 
 
#== token_stream — yield 가 2개인 이유
 
# --8<-- [start:token_stream]
async def token_stream(message: str):
    async for chunk in chain.astream({"message": message}):
        yield f"data: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# yield 해석
#(1)> 첫 번째 yield → for 문 '안'(8칸). 토큰 개수만큼 반복 실행
#(1)> 두 번째 yield → for 문 '밖'(4칸). 딱 1번. "끝났다" 신호
 
# 실제로 흐르는 모습
#(2)> data: {"token": "파"}      ┐
#(2)> data: {"token": "이"}      │ 첫 번째 yield 가
#(2)> data: {"token": "썬"}      │ 반복 실행
#(2)> data: {"token": "은"}      ┘
#(2)> data: [DONE]               ← 두 번째 yield, 1번
# --8<-- [end:token_stream]
 
#! [DONE] 이 왜 필요하냐 → 받는 쪽에서 ①,②을 구분할 수 없음.
#! ① 답변이 정상적으로 완료됨
#! ② 네트워크가 끊김 / 서버가 죽음
#! 둘 다 "더 이상 안 옴" 으로 보임. [DONE] 은 "끝까지 다 보냈다" 는 확인임.
#! OpenAI API 도 똑같이 data: [DONE] 을 보냄. 업계 관례.
 
 
#== 딕셔너리 vs JSON
#> 딕셔너리는 파이썬 메모리 안의 '물건', JSON 은 밖으로 보내기 위한 '글자'.
 
# --8<-- [start:json]
import json
 
d = {"token": "안녕"}          # 딕셔너리 — 파이썬 객체
s = json.dumps(d)              # JSON — 그냥 문자열
 
print(type(d))     # <class 'dict'>
print(type(s))     # <class 'str'>   ← 문자열!
 
print(d["token"])  # 안녕      (꺼낼 수 있음)
print(s["token"])  # 에러!     문자열이라 못 꺼냄
# 네트워크는 글자(바이트)만 보낼 수 있어서 변환이 필요함
#(1)> 상대가 자바스크립트일 수도 있는데 파이썬 dict 를 알 리가 없음
 
print(s)
# {"token": "안녕"}
#(2)> 작은따옴표가 큰따옴표로 바뀜. JSON 은 큰따옴표만 허용
#(2)> True→true, None→null 로도 바뀜. 함수·클래스는 못 담음
# --8<-- [end:json]
 
#! json.dumps → 포장 (dump = 쏟아내다, 밖으로)
#! json.loads → 풀기 (load = 실어들이다)
#! 파이썬 dict → dumps → 문자열 → 네트워크 → JSON.parse → JS 객체
 
#! /chat 에서는 return {"reply": reply} 만 했는데 JSON 이 도착했음.
#! FastAPI 가 뒤에서 json.dumps 를 대신 해준 것이었음.
#! StreamingResponse 는 "이 글자 그대로 내보내" 하는 도구라 자동 변환이 없음 → 직접 해야 함.
 
 
#== json.dumps 를 꼭 써야 하는 이유 2개

#! LLM 은 목록·코드를 뱉을 때 줄바꿈을 자주 냄.
#! 언젠가 반드시 터지는 버그이고, 재현이 어려운 형태로 터짐.
 
#! ② 나중에 확장이 안 됨. 에이전트가 되면 보낼 게 늘어남.
#! {'type': 'tool_start', 'tool': '웹검색'}
#! {'type': 'token', 'content': '검'}
#! {'type': 'error', 'message': '타임아웃'}
#! "지금 웹 검색 중..." 을 보여주려면 종류를 구분할 라벨이 필요하고 그게 dict 구조임.
 
#! ensure_ascii=False 는 한글을 깨지지 않게 바꿔주는 옵션.
#! 둘 다 JSON.parse 하면 똑같이 복원되지만 터미널에서 눈으로 볼 때 False 가 나음.
 
#! 따옴표가 섞인 이유 → f"data: {json.dumps({'token': chunk})}\n\n"
#! 바깥이 큰따옴표라 안쪽은 작은따옴표. 같은 걸 쓰면 문자열이 거기서 끊김.
 
# --8<-- [start:why_json]
# ① 줄바꿈이 오면 프로토콜이 깨짐
chunk = "안녕\n\n반가워"          # LLM 이 문단을 나눔
 
print(f"data: {chunk}\n\n")
# data: 안녕
#
# 반가워
#(1:3)> 받는 쪽에선 "안녕" 이 끝나고 정체불명의 "반가워" 가 붙은 걸로 보임
 
print(json.dumps({"token": chunk}, ensure_ascii=False))
# {"token": "안녕\n\n반가워"}
#(2)> 진짜 줄바꿈이 \n 이라는 두 글자로 바뀜 (이스케이프)
#(2)> 한 줄로 안전하게 실려가고, 받는 쪽 JSON.parse 에서 원래 줄바꿈으로 복원됨
# --8<-- [end:why_json]
 

 
#== StreamingResponse
 
# --8<-- [start:response]
from fastapi.responses import StreamingResponse
 
@app.post("/stream")
async def stream(req: ChatRequest):
    # await 가 없음. 실행해서 결과를 받는 게 아니라 '발전기 통째로' 를 넘기는 것
    #(1)> StreamingResponse 가 그걸 쥐고 하나씩 돌려서 뽑아 보냄
    #(1)> headers 는 중간 서버가 버퍼에 모아두지 말라는 지시
    return StreamingResponse(
        token_stream(req.message),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )

async def token_stream(message: str):
    async for chunk in chain.astream({"message": message}):
        yield f"data: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# --8<-- [end:response]
 
#! 원래 HTTP 응답 시에는 Content-Length 로 "42바이트 보낼게" 를 미리 선언함.
#! 즉 답을 다 만들어놓고 세어봐야 함. 근데 LLM 응답은 끝나기 전엔 몇 글자일지 모름.
#! → StreamingResponse 는 Transfer-Encoding: chunked 로 바꿈.
#!   "길이는 나도 몰라, 조각으로 보낼 거고 다 보내면 알려줄게"
 
#! 하는 일 3가지
#! ① 헤더를 Content-Length 대신 chunked 로 바꿈
#! ② 헤더를 먼저 즉시 보냄 (본문 안 기다리고)
#! ③ 제너레이터에서 값이 나올 때마다 즉시 네트워크로 밀어냄
 
#! SSE 전용이 아님. "조금씩 흘려보내기" 라는 일반 기능임.
#! 대용량 CSV, 동영상에도 씀.
 
 
#== 스트리밍 중 에러
#> HTTP 에러 코드를 줄 수 없음. 200 OK 를 이미 보낸 뒤라 되돌릴 수 없음.
 
# --8<-- [start:error]
async def token_stream(message: str):
    try:
        async for chunk in chain.astream({"message": message}):
            yield f"data: {json.dumps({'token': chunk}, ensure_ascii=False)}\n\n"
    # 에러도 데이터로 실어 보냄
    #(1)> 이거 없으면 연결이 뚝 끊기고 사용자 화면은 설명 없이 멈춰 있음
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    yield "data: [DONE]\n\n"

# --8<-- [end:error]
 
 
#== 테스트할 때 주의
 
#! curl -N 을 빼면 안 흐름. -N = 버퍼링 끄기
#! curl -N -X POST http://127.0.0.1:8000/stream -H "Content-Type: application/json" -d '{"message":"5문장으로 설명해줘"}'
 
#! /docs 에서는 스트리밍이 제대로 안 보임 (다 모아서 표시).ㅍ반드시 curl -N 이나 브라우저로 확인할 것.
 
#! 헤더 비교해보기 → curl -i 는 /chat, curl -iN 은 /stream
#! Content-Length 랑 Transfer-Encoding: chunked 가 다른 게 보임

 