"""
title: 비동기 — async · await · gather
tags: [async]
"""

#== 비동기가 뭐냐
#> 코드를 빠르게 하는 게 아니라, 기다리는 시간을 겹치게 하는 것.

#! 효과 있는 것 → 남을 기다리는 작업 (LLM 응답, DB, 파일, API)
#! 효과 없는 것 → 내가 계산하는 작업 (이미지 처리, 큰 반복문)
#! 우리가 하는 건 전부 앞쪽임. LLM 답 기다리는 게 시간의 95%.

#! 직원을 늘리는 게 아님. 파이썬은 기본 1명(싱글 스레드).
#! 그 1명이 노는 시간 없이 움직이게 만드는 것.


#== 용어 3개

#! 이벤트 루프 = 알바생 본인. 전체를 돌리는 관리자. asyncio.run() 이 켬
#! 코루틴     = 주문 쪽지. async def 로 만든 함수를 부르면 나오는 것
#! await      = 커피머신 돌려놓고 손 떼기. "여기서 손 떼고 다른 일 해도 돼"

#! await 를 "여기서 멈춰 기다려" 로 이해하면 계속 헷갈림.
#! 반대임. 제어권을 반납하고 다른 일 하러 가는 것.


#== 실습 ① 순차 vs 동시

# --8<-- [start:seq]
import asyncio, time

async def coffee(name, sec):
    print(f"  {name} 시작")
    await asyncio.sleep(sec)
    print(f"  {name} 완성")
    return name

async def main():
    t = time.time()
    #(2)> 현재 시각
    await coffee("아메리카노", 2)
    await coffee("라떼", 3)
    print(f"{time.time()-t:.1f}초")

asyncio.run(main())
#(3)>  main() <- 코루틴 객체만 만들어지고 이벤트 루프 키지 않은 상태임
#(3)>  asyncio.run() <- 이벤트 루프를 킴 (프로그램 전체에서 딱 한번, 맨 바깥에서만 끔)
#   아메리카노 시작
#   아메리카노 완성
#   라떼 시작
#   라떼 완성
# 5.0초
#(1)> await 를 두 줄 나열하면 줄서기임. 앞이 끝나야 뒤가 시작

# --8<-- [end:seq]

# --8<-- [start:gather]
async def main():
    t = time.time()
    await asyncio.gather(
        coffee("아메리카노", 2),
        coffee("라떼", 3),
    )
    print(f"{time.time()-t:.1f}초")

asyncio.run(main())
#   아메리카노 시작
#   라떼 시작
#   아메리카노 완성
#   라떼 완성
# 3.0초
#(1)> 둘 다 먼저 시작하고, 끝나는 대로 완성됨
#(1)> 5초가 3초로 줄어듦. 긴 쪽 하나의 시간만 걸림
# --8<-- [end:gather]

#! await 를 나열하는 건 동시 실행이 아님.
#! await coffee(2); await coffee(3)           → 5초 (줄서기)
#! await asyncio.gather(coffee(2), coffee(3)) → 3초 (동시)



#== 실습 ② 블로킹 함정 
#> asyncio.sleep 을 time.sleep 으로 바꾸면 gather 를 써도 다시 5초.


#! 쓰면 안 되는 것 → 대신 쓸 것
#! time.sleep   → asyncio.sleep
#! requests     → httpx.AsyncClient
#! invoke       → ainvoke  (async 함수 안에서)


#== async def 는 그냥 부르면 실행 안 됨

# --8<-- [start:run]
main()               # 실행 안 됨. 코루틴 객체(쪽지)만 만들어짐
# <coroutine object main at 0x7f...>
#(1)> RuntimeWarning: coroutine was never awaited
#(1)> = "쪽지만 만들고 시키지는 않았다" 는 경고

asyncio.run(main())  # 이벤트 루프를 켜고 실제로 돌림

# --8<-- [end:run]

#! asyncio.run 은 프로그램 전체에서 딱 한 번, 맨 바깥에서만 씀.
#! async 함수 안에서는 await 를 쓰는 것.
#! `(FastAPI 서버에서는 uvicorn 이 대신 켜줘서 이걸 안 씀)`


#== LangChain — 아는 것에 a 만 붙음

#! invoke → ainvoke · stream → astream · batch → abatch

# --8<-- [start:llm]
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")

# 먼저 풀어쓴 버전 — 이걸로 시작할 것
async def main():
    t = time.time()

    msgs = []
    # await 를 안 붙였으니 아직 실행 안 됨. 쪽지만 쌓는 중
    for topic in ["고양이", "강아지", "햄스터"]:
        msg = llm.ainvoke(f"{topic}에 대해 한 문장으로 설명해줘")
        msgs.append(msg)

    results = await asyncio.gather(*msgs)
    #(2)> 여기서 한 번에 던지고 다 올 때까지 기다림

    for r in results:
        print(r.content)
        #(3)> ainvoke 는 AIMessage 객체를 돌려줌 → .content 로 꺼냄

    print(f"{time.time()-t:.1f}초")

asyncio.run(main())
# --8<-- [end:llm]

#! 가장 느린 하나의 시간만 걸림. 세 개를 동시에 던졌으니까.


#== 압축 버전에 쓰인 문법 2개

# --8<-- [start:syntax]

results = await asyncio.gather(*[
    llm.ainvoke(f"{topic}에 대해 한 문장으로 설명해줘")
    for topic in ["고양이", "강아지", "햄스터"]
])
# --8<-- [end:syntax]



#== gather 랑 abatch 차이

#! 같은 체인에 입력만 여러 개 → abatch 가 간단함
#! 서로 다른 작업을 섞을 때 → gather (요약 체인 + 번역 체인 + 웹검색 동시에)
#! 나중에 에이전트가 툴 여러 개를 병렬 호출할 때 gather 형태를 만남

