"""
title: gather 심화 
tags: [async]
"""

#== 순차 vs 동시 — 실제로 재보기

# --8<-- [start:bench]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

QUESTIONS = [
    "파이썬 async/await의 장점을 한 문장으로.",
    "LangChain이란 무엇인지 한 문장으로.",
    "FastAPI의 특징을 한 문장으로.",
    "비동기 프로그래밍이 필요한 이유를 한 문장으로.",
    "Pydantic의 역할을 한 문장으로.",
]

def sequential():
    """5개 질문을 하나씩 순서대로"""
    start = time.time()
    for q in QUESTIONS:
        llm.invoke(q)
        #(1)> invoke 는 응답이 올 때까지 이 줄에서 완전히 멈춤
        #(1)> 응답이 와야 다음 반복으로 넘어감 → 5번을 줄줄이 기다림
    return time.time() - start

async def concurrent():
    """5개를 동시에 시작해서 가장 늦는 것까지 기다리기"""
    start = time.time()
    await asyncio.gather(*[llm.ainvoke(q) for q in QUESTIONS])
    #(2)> 5개를 한꺼번에 던져놓고 다 올 때까지 기다림
    #(2)> 걸리는 시간은 가장 느린 하나의 시간
    return time.time() - start

seq  = sequential()
conc = asyncio.run(concurrent())
print(f"순차: {seq:.2f}초 / 동시: {conc:.2f}초 / {seq/conc:.1f}배")
# 순차: 10.83초 / 동시: 2.41초 / 4.5배
# --8<-- [end:bench]



#== await 유무 — 직접 확인하기

# --8<-- [start:await_test]
# 없을 때 — 코루틴 객체만 만들어짐. LLM 호출 자체가 안 일어남
coroutine_obj = llm.ainvoke('안녕?')
print(type(coroutine_obj))
# <class 'coroutine'>
print(coroutine_obj)
# <coroutine object BaseChatModel.ainvoke at 0x7f...>
coroutine_obj.close()
#(1)> close() 는 안 쓰고 버릴 코루틴을 정리하는 것
#(1)> 안 하면 "coroutine was never awaited" 경고가 뜸

# 있을 때 — 실제로 실행돼서 AIMessage 가 옴
actual = await llm.ainvoke('안녕?')
print(type(actual))
# <class 'langchain_core.messages.ai.AIMessage'>
print(actual.content)
# 안녕하세요! 무엇을 도와드릴까요?
# --8<-- [end:await_test]

#! ainvoke 를 부르는 것 = 주문 쪽지를 쓰는 것.
#! await 를 붙이는 것 = 그 쪽지를 실제로 주방에 넣는 것.
#! gather 안에서 await 를 안 붙이는 이유가 이거였음. 쪽지만 모아서 한꺼번에 넘기는 것.


#== 완료 순서 vs 결과 순서
#> 이 둘이 다름. 헷갈리기 쉬운 지점.

# --8<-- [start:order]
TEXTS = [
    "파이썬 async/await의 장점을 한 문장으로.",
    "LangChain이란 무엇인지 한 문장으로.",
    "FastAPI의 특징을 한 문장으로.",
    "비동기 프로그래밍이 필요한 이유를 한 문장으로.",
    "Pydantic의 역할을 한 문장으로.",
]

async def get_summary(text: str, label: str) -> str:
    result = await llm.ainvoke(f'한 문장으로 요약: {text}')
    print(f'  [{label}] 완료')
    return result.content

async def process_all(texts: list) -> list:
    return await asyncio.gather(
        *[get_summary(t, f'텍스트{i+1}') for i, t in enumerate(texts)],
        return_exceptions=True
    )

results = asyncio.run(process_all(texts))
#   [텍스트4] 완료      ← 완료 순서는 뒤죽박죽
#   [텍스트3] 완료
#   [텍스트5] 완료
#   [텍스트2] 완료
#   [텍스트1] 완료

for i, r in enumerate(results):
    print(f'  [{i+1}] {str(r)[:30]}')
#   [1] 파이썬은 배우기 쉬운 다목적...   ← 결과는 항상 입력 순서
#   [2] LangChain은 대규모 언어...

# print 가 찍히는 순서 = 실제로 끝난 순서 (빠른 게 먼저)
#(1)> results 리스트 = 항상 입력 순서. gather 가 안에서 다시 정렬해 줌
# --8<-- [end:order]

#! batch 결과 순서 정리했던 거랑 같은 얘기였음.
#! LangSmith 에 찍히는 순서는 뒤죽박죽인데 results[0] 은 항상 첫 입력의 답이라던 것.


#== 예외가 나면 대입 자체가 안 됨
#> return_exceptions 를 이해하려면 이것부터.

# --8<-- [start:assign]
x = 100
print('실행 전 x =', x)     # 100

# 오른쪽(1/0)을 계산하다 터지면 왼쪽(x)에 넣는 일이 아예 안 일어남
#(1)> x 가 None 이 되는 게 아니라 이전 값 그대로임
#(1)> 변수가 처음부터 없었다면 만들어지지도 않음
try:
    x = 1 / 0              # ← 여기서 터짐
except ZeroDivisionError:
    print('오류 발생!')

print('실행 후 x =', x)     # 100  ← 여전히 100!

# --8<-- [end:assign]


#== return_exceptions — 하나 터지면 어떻게 되나

# --8<-- [start:exceptions]
async def 작업(이름, 초, 실패=False):
    await asyncio.sleep(초)
    if 실패:
        print(f'  {이름} 실패')
        raise ValueError(f'{이름} 터짐')
    print(f'  {이름} 완료 (돈 나감)')
    return f'{이름}의 결과물'

# ① True — 에러도 결과 리스트에 담아서 돌려줌
결과 = await asyncio.gather(
    작업('A', 1),
    작업('B', 2, 실패=True),
    작업('C', 3),
    return_exceptions=True
)
print('받은 것:', 결과)
#   A 완료 (돈 나감)
#   B 실패
#   C 완료 (돈 나감)

# 받은 것: ['A의 결과물', ValueError('B 터짐'), 'C의 결과물']
#(1)> 에러 객체가 리스트의 그 자리에 그대로 들어옴
#(1)> A, C 결과는 멀쩡히 건짐

# ② False (기본값) — 예외가 밖으로 튀어나옴
try:
    결과2 = await asyncio.gather(
        작업('A', 1),
        작업('B', 2, 실패=True),
        작업('C', 3),
        return_exceptions=False
    )
except ValueError as e:
    print(f'  예외가 튀어나옴: {e}')

await asyncio.sleep(2)                      # C 가 끝날 시간 주기
print('결과2 존재?', '결과2' in globals())
#   A 완료 (돈 나감)
#   B 실패
#   예외가 튀어나옴: B 터짐
#   C 완료 (돈 나감)          ← B 가 터진 뒤에도 C 는 계속 돌았음

# 결과2 존재? False
#(2)> gather 가 예외를 던지면 오른쪽 계산이 중단됨 → 왼쪽 결과2 에 넣는 일 자체가 안 일어남
#(2)> 그래서 결과2 라는 변수가 만들어지지도 않음 ('결과2' in globals() → False)
#(2)> 위의 x = 1/0 이랑 같은 구조. A 결과도 받을 방법이 없어짐
# --8<-- [end:exceptions]

#! return_exceptions=False 여도 이미 시작된 작업은 안 멈춤. C 가 끝까지 돌아서 "돈 나감" 이 찍힘.
#! gather 가 취소하는 건 '결과를 모아 돌려주는 일' 이지 진행 중인 요청이 아님.
#! → 즉 API 비용은 그대로 나가는데 결과만 못 받는 것. 제일 손해임.

#! 기본값이 False 라는 게 함정임. 아무것도 안 쓰면 하나 터질 때 다 날아감.
#! 대량 처리할 땐 return_exceptions=True 를 기본으로 켜둘 것.
#! 특히 429(Rate Limit)는 언제든 날 수 있어서 이거 없으면 위험함.

#! globals() 는 지금 살아있는 변수 이름들을 dict 로 주는 함수.
#! '이름' in globals() 로 그 변수가 만들어졌는지 확인할 수 있음.


#== 실무 패턴 — 성공·실패 갈라내기

# --8<-- [start:split]
results = await asyncio.gather(*작업들, return_exceptions=True)

success= [r for r in 결과 if not isinstance(r, Exception)]
#(1)> isinstance(r, Exception) 으로 가려냄. 에러 객체인지 아닌지
failure = [(i, r) for i, r in enumerate(results) if isinstance(r, Exception)]
#(2)> 실패 쪽은 enumerate 로 인덱스를 같이 담음 → 몇 번째가 실패했는지 알아야 재시도 가능

print(f'성공 {len(success)}건, 실패 {len(failure)}건')
for i, e in failure:
    print(f'  [{i}] {type(e).__name__}: {e}')
# --8<-- [end:split]

#! 실패 목록에 인덱스를 남기는 게 핵심.
#! 인덱스를 알아야 원본 리스트에서 그것만 다시 꺼내 재시도할 수 있음.


#== create_task — gather 랑 뭐가 다르냐
#> 둘 다 동시 실행인데, 시작하는 시점이 다름.

# --8<-- [start:create_task]
async def cook(name, seconds):
    await asyncio.sleep(seconds)
    print(f'  {name} done ({seconds}s)')
    return name

# A. gather — 그 줄에 도달해야 시작
t0 = time.time()
results = await asyncio.gather(cook('A', 2), cook('B', 2))
print(f'  {time.time()-t0:.1f}s')
#   A done (2s)
#   B done (2s)
#   2.0s

# B. create_task — 만드는 순간 이미 시작
t0 = time.time()
tasks = [asyncio.create_task(cook('C', 2)), asyncio.create_task(cook('D', 2))]
#(1)> 이 줄에서 C, D 가 이미 백그라운드로 돌기 시작함

print(' 주문 넣어두고 딴 일 하는 중')
await asyncio.sleep(1)                  # 딴 일 1초
print(' 딴 일 끝 (1초 경과)')

results = await asyncio.gather(*tasks)  # 이제 결과만 회수
print(f'  총 {time.time()-t0:.1f}s')
#   주문 넣어두고 딴 일 하는 중
#   딴 일 끝 (1초 경과)
#   C done (2s)
#   D done (2s)
#   총 2.0s

# 딴 일 1초를 했는데도 총 2초임. 그 1초 동안 요리가 이미 진행 중이었으니까
#(2)> 딴 일을 먼저 하고 그다음 gather 를 불렀다면 1 + 2 = 3초가 걸렸을 것
# --8<-- [end:create_task]

#! gather      = 그 줄에서 시작하고, 끝날 때까지 다음 줄로 못 감
#! create_task = 만든 순간 시작. 그 사이에 다른 코드를 끼워 넣을 수 있음

#! LLM 배치 처리는 대부분 gather 로 충분함.
#! create_task 는 "태스크 만들어두고 나중에 결과 확인" 하는 패턴에 씀.
#! 예를 들면 LLM 호출을 걸어두고 그동안 DB 조회나 파일 읽기를 하는 경우.


#== gather · batch · RunnableParallel 차이
#> 셋 다 "동시에" 인데 뭐가 동시인지가 다름.

#! chain.batch([입력1, 입력2, ...])
#!   → 입력 여러 개 · 체인 하나. 같은 일을 여러 데이터에
#!   → 안에서 스레드를 띄움. async 함수가 아니어도 씀
#!
#! RunnableParallel({"a": 체인1, "b": 체인2})
#!   → 입력 하나 · 체인 여러 개. 다른 일을 같은 데이터에
#!
#! asyncio.gather(코루틴1, 코루틴2, ...)
#!   → 아무거나 다 됨. LLM 호출이든 DB 조회든 파일 읽기든 섞어도 됨
#!   → 대신 async 함수 안에서만 쓸 수 있고 ainvoke 를 써야 함

#! 정리하면 → 같은 체인에 입력만 여러 개면 abatch 가 간단하고,
#! 서로 다른 작업을 섞어야 하면 gather 를 씀.