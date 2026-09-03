"""
title: Rate Limit 대응 
tags: [async]
"""

#== Rate Limit 이 뭐냐
#> API 제공사가 걸어둔 사용량 상한. 넘으면 429 Too Many Requests 가 옴.

#! RPM (requests per minute) — 1분에 요청 몇 번까지
#! TPM (tokens per minute)   — 1분에 토큰 몇 개까지
#! 긴 문서를 여러 개 던질 땐 요청 수보다 토큰 한도에 먼저 걸리는 경우가 많음.

#! gather 는 "전부 한꺼번에" 던지는 거라 개수가 많아지면 반드시 걸림.
#! 100개를 gather 하면 100개 요청이 동시에 나감 → 절반쯤 429 로 실패.


#== 문제 재현

# --8<-- [start:problem]
async def get_summary(text: str) -> str:
    result = await llm.ainvoke(f"한 문장으로 요약: {text}")
    return result.content

async def process_bulk(texts: list) -> list:
    results = await asyncio.gather(
        *[get_summary(t) for t in texts],
        return_exceptions=True
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    failures  = [r for r in results if isinstance(r, Exception)]
    print(f"성공: {len(successes)}개 / 실패: {len(failures)}개")

    for f in failures[:3]:
        print(f"  오류: {type(f).__name__}: {str(f)[:80]}")
    return results

# 10개는 보통 안전
asyncio.run(process_bulk([f"텍스트 {i}입니다." for i in range(10)]))
# 성공: 10개 / 실패: 0개


# asyncio.run(process_bulk([f"텍스트 {i}입니다." for i in range(100)]))
# 성공: 47개 / 실패: 53개
#   오류: RateLimitError: Error code: 429 - Rate limit reached...
# return_exceptions=True 덕분에 성공한 47개는 건짐
#(1)> 이거 없었으면 47개까지 다 버려짐
# --8<-- [end:problem]


#== 해결 ① 청크 — 10개씩 나눠서

# --8<-- [start:chunk]
async def process_in_chunks(texts: list, chunk_size: int = 10) -> list:
    """chunk_size 개씩 나눠 처리, 청크 사이 1초 대기"""
    all_results = []

    for i in range(0, len(texts), chunk_size):
        chunk = texts[i : i + chunk_size]
        #(1)> range(0, 25, 10) → 0, 10, 20 세 번 돎
        #(1)> texts[0:10], texts[10:20], texts[20:30] → 마지막은 5개만 남아도 알아서 잘림

        print(f"청크 {i//chunk_size + 1} 처리 중... ({len(chunk)}개)")

        chunk_results = await asyncio.gather(
            *[get_summary(t) for t in chunk],
            return_exceptions=True
        )
        all_results.extend(chunk_results)
        #(2)> append 는 통째로 1개 추가, extend 는 풀어서 여러 개 추가

        if i + chunk_size < len(texts):
            print("  1초 대기 중...")
            await asyncio.sleep(1)
            #(3)> 마지막 청크면 대기할 필요 없으니 조건을 검
            #(3)> 반드시 await asyncio.sleep. time.sleep 은 이벤트 루프를 얼림

    return all_results

results = asyncio.run(process_in_chunks([f"텍스트 {i}입니다." for i in range(25)],
                                        chunk_size=10))
# 청크 1 처리 중... (10개)
#   1초 대기 중...
# 청크 2 처리 중... (10개)
#   1초 대기 중...
# 청크 3 처리 중... (5개)
# --8<-- [end:chunk]

#! 단점이 있음. 청크 안에서 하나만 느리면 나머지 9개가 다 끝나도 기다려야 함.
#! 그동안 슬롯이 놀고 있는 셈. 그리고 1초 대기도 그냥 버리는 시간임.


#== 해결 ② 세마포어 — 슬롯 5개 돌려쓰기
#> 동시에 실행될 수 있는 코루틴 수를 제한하는 도구.

# --8<-- [start:semaphore]
semaphore = asyncio.Semaphore(5)
#(1:1)> "지금 이 순간 최대 5개만 실행 허용" 이라는 뜻

async def safe_llm_call(text: str, idx: int) -> str:
    async with semaphore:
        #(2)> 여기서 슬롯을 하나 가져감. 이미 5개가 쓰고 있으면 이 줄에서 대기

        print(f"  [{idx:02d}] 시작")
        try:
            result = await llm.ainvoke(f"한 문장으로 요약: {text}")
            print(f"  [{idx:02d}] 완료")
            return result.content
        except Exception as e:
            return f"오류: {e}"
        # ← async with 블록이 끝나면 슬롯 자동 반납

async def process_safely(texts: list) -> list:
    return await asyncio.gather(
        *[safe_llm_call(t, i) for i, t in enumerate(texts)],
        return_exceptions=True
    )
    # 20개 코루틴을 전부 만들어 던지는 건 똑같음 / 다만 각자 async with 앞에서 줄을 서게 됨

results = asyncio.run(process_safely([f"텍스트 {i}" for i in range(20)]))
#   [00] 시작
#   [01] 시작
#   [02] 시작
#   [03] 시작
#   [04] 시작       ← 여기까지만 동시 실행, 나머지 15개는 대기
#   [02] 완료
#   [05] 시작       ← 슬롯 하나 반납되자마자 다음이 들어감
#   [00] 완료
#   [06] 시작
# --8<-- [end:semaphore]

#! 슬롯이 뭐냐 → 그냥 '자리 개수' 임. Semaphore(5) 는 자리가 5개라는 뜻.
#! 들어갈 때 하나 가져가고 나올 때 반납함. 자리가 없으면 날 때까지 기다림.
#! 화장실 칸이 5개인 것과 같음. 6번째 사람은 문 앞에서 기다리다 한 명 나오면 들어감.

#! async with 를 쓰는 이유 → 블록을 나갈 때 자동으로 반납해 주기 때문.
#! 에러가 나서 튕겨 나가도 반납됨. 


#== 청크 vs 세마포어 — 뭐가 다르냐

#! 청크   : 10개 던지고 → 전부 끝날 때까지 기다림 → 1초 쉬고 → 다음 10개
#! 세마포어: 5개 던지고 → 하나 끝나는 즉시 다음 하나 투입 → 계속 5개 유지

#! 청크는 '묶음' 단위라 빈자리가 생겨도 안 채움.
#! 청크 안에서 9개가 끝나고 1개가 느리면 슬롯 9개가 놀면서 기다림.
#! 세마포어는 '자리' 단위라 하나 나가면 바로 다음이 들어감 → 노는 시간이 없음.

#! 그래서 보통 세마포어가 더 빠르고 안정적임.
#! 청크는 코드가 단순해서 이해하기 쉽다는 게 장점.
#! 앞에서 본 batch(config={"max_concurrency": 5}) 가 사실 세마포어랑 같은 개념임.


#== 해결 ③ 지수 백오프 재시도
#> 429 가 나도 포기하지 말고 잠깐 쉬었다 다시 시도. 쉬는 시간을 2배씩 늘림.

# --8<-- [start:retry]

import asyncio
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

'''
Rate Limit 오류가 발생했을 때 단순히 포기하는 대신, 잠시 기다렸다가 재시도하는 전략이 지수 백오프(Exponential Backoff) 입니다. 
1초 기다렸다 재시도, 그래도 실패하면 2초, 그래도 실패하면 4초 — 대기 시간이 2배씩 늘어납니다.
'''

semaphore = asyncio.Semaphore(5)


async def safe_call_with_retry(text: str, idx: int, max_retries: int = 3) -> str:
    async with semaphore:
        for attempt in range(max_retries):
            try:
                result = await llm.ainvoke(f"한 문장으로 요약: {text}")
                return result.content
                #(1:1)> 성공하면 바로 return → 아래 재시도 코드는 안 감

            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"  [{idx:02d}] 최종 실패 ({max_retries}회 시도)")
                    return f"실패: {e}"
                    #(2)> 마지막 시도였으면 포기하고 실패 메시지를 돌려줌
                    #(2)> 여기서 raise 하지 않고 문자열로 넘기는 게 포인트

                wait_time = 2 ** attempt
                #(3:1)> 2**0=1, 2**1=2, 2**2=4 → 1초 → 2초 → 4초

                print(f"  [{idx:02d}] {type(e).__name__} → {wait_time}초 후 재시도")
                await asyncio.sleep(wait_time)

async def robust_batch(texts: list) -> list:
    """재시도 포함 안전 배치 처리 — 프로덕션 수준"""
    results = await asyncio.gather(
        *[safe_call_with_retry(text, i) for i, text in enumerate(texts)],
        return_exceptions=True
    )

    successes = sum(1 for r in results if not isinstance(r, Exception) and not str(r).startswith("실패"))
    print(f"\n배치 완료: 성공 {successes}개 / 전체 {len(results)}개")
    return results

texts = [f"텍스트 {i}입니다." for i in range(30)]
results = asyncio.run(robust_batch(texts))

#   [07] RateLimitError → 1초 후 재시도 (1/3)
#   [07] RateLimitError → 2초 후 재시도 (2/3)
# 배치 완료: 성공 30개 / 전체 30개    ← 재시도로 결국 성공
# --8<-- [end:retry]

#! 왜 시간을 2배씩 늘리냐 → 서버가 밀려 있는데 같은 간격으로 계속 두드리면
#! 더 밀리기만 함. 점점 물러나면서 서버가 회복할 시간을 주는 것.

#! await asyncio.sleep 이어야 함.


#== 최종 정리 — 넷 중 뭘 쓰나

#! gather      : 여러 개를 동시에 던지는 기본. 개수가 적을 때(10개 이하)
#! create_task : 걸어두고 그 사이에 다른 일을 할 때
#! 청크        : 코드가 단순함. 대량인데 세마포어가 부담스러울 때
#! 세마포어     : 대량 처리의 정답. 슬롯을 계속 채워서 노는 시간이 없음
#!
#! 실전 조합 → gather + 세마포어 + return_exceptions=True + 백오프 재시도
#! 이 네 개를 다 쓴 게 마지막 코드임.

