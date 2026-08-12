"""
title: Depends — 의존성 주입과 싱글턴
tags: [fastapi]
"""

#== 문제 — 요청마다 새로 만들어짐
#> 지금까지 llm_service.py 는 함수 안에서 ChatOpenAI() 를 만들었음.

#! 동시 요청 100개면 인스턴스 100개가 생김.
#! 불필요한 연결 생성 · 메모리 낭비 · 미묘한 설정 불일치.
#! 해결책이 "인스턴스를 한 번만 만들어서 공유하며 계속 돌려쓰기" 임.


#== 용어 정리 — 헷갈렸던 것들

#! 싱글턴(Singleton) = 인스턴스를 딱 1개만 만들어 계속 돌려쓰는 방식.
#! 이름 그대로 single. LLM 클라이언트처럼 만드는 비용이 비싼 걸 이렇게 씀.

#! 캐시(Cache) = 한 번 계산한 결과를 저장해뒀다가 다음엔 그대로 꺼내 쓰는 것.
#! 싱글턴을 만드는 수단이 캐시임 → 함수 결과를 캐시하면 항상 같은 객체가 나옴.

#! 팩토리(Factory) = 객체를 만들어 돌려주는 함수. 공장이라는 뜻.
#! get_chain() 처럼 "부르면 객체를 만들어서 준다" 는 함수가 팩토리라는 의미임.
#! 직접 ChatOpenAI() 를 쓰지 않고 함수를 거치는 이유 → 나중에 바꿔치기하기 쉬워서.




#== lru_cache — 캐시로 싱글턴 만들기
#> LRU(Least Recently Used, 가장 오래 안 쓴 것부터 버리는) 캐시 데코레이터
#> LRU 캐시는 파이썬 프로세스 안 (RAM)에 저장됨
 
# --8<-- [start:lru]
from functools import lru_cache
 
@lru_cache()
def get_chain() -> Runnable[dict, str]:
    #(2)> Runnable[들어갈때 타입, 나올때 타입]
    #(2)> dict → prompt 가 맨 앞이라서
    #(2)> str  → parser 가 맨 뒤라서

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "유용한 AI 어시스턴트입니다."),
        ("human", "{message}"),
    ])
    parser = StrOutputParser()
    return prompt | llm | parser

# @lru_cache 가 붙으면 결과를 저장해뒀다가 다음엔 그대로 돌려줌
#(1)> 호출 1: 실제로 만들고 → 캐시 저장 → 반환
#(1)> 호출 2: 캐시 확인 → HIT → 저장된 것 반환 (생성 없음)
#(1)> 호출 3: 캐시 확인 → HIT → 저장된 것 반환 (생성 없음)
#(1)> 결과: 요청이 몇 개 오든 ChatOpenAI() 는 딱 한 번만 만들어짐
# --8<-- [end:lru]
 
#! lru 는 Least Recently Used 의 약자. 원래는 "오래 안 쓴 것부터 버리는 캐시" 라는 뜻.
#! 인수가 없는(전달하는 입력값이 없는) 함수에 붙이면 저장할 게 하나뿐이라 결과적으로 싱글턴이 됨.
 
#! 인수가 있으면 인수별로 따로 캐시함.
#! get_encoder("gpt-4o-mini") 와 get_encoder("gpt-4") 는 각각 저장됨.
 
 
#== lru_cache 옵션과 메서드
 
# --8<-- [start:lru_detail]
@lru_cache(maxsize=128, typed=False)
#(1)>  maxsize — 캐시 최대 저장 개수. 꽉 차면 가장 오래 안 쓴 것부터 버림
#(1)> 기본값 128. None 이면 LRU 기능 해제 → 캐시가 무한정 커짐
#(1)> typed — True 면 인자 타입까지 구분. f(3) 과 f(3.0) 을 별개로 캐싱
def f(x):
    ...

# 통계 조회
f.cache_info()
# CacheInfo(hits=5, misses=2, maxsize=128, currsize=2)
#(2)> hits     — 캐시에 있어서 함수 실행을 건너뛴 횟수
#(2)> misses   — 캐시에 없어서 실제로 실행한 횟수
#(2)> currsize — 지금 저장돼 있는 항목 수
 
f.cache_clear()      # 캐시와 통계 초기화
f.__wrapped__        # 캐시가 안 걸린 원본 함수
#(3)> __wrapped__ 로 부르면 캐시를 건너뛰고 매번 새로 실행됨
# --8<-- [end:lru_detail]
 
 
#== 캐시가 도는 걸 눈으로 보기 — 피보나치
 
# --8<-- [start:fib]
from functools import lru_cache
 
@lru_cache(maxsize=128)
def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)
 
fib(30)
print(fib.cache_info())
# CacheInfo(hits=28, misses=31, maxsize=128, currsize=31)
#(1)> misses=31 → fib(0)~fib(30) 까지 31개를 실제로 계산함
#(1)> hits=28   → 이미 계산해둔 걸 28번 그냥 꺼내 씀
#(1)> currsize=31 → 지금 31개가 저장돼 있음
# --8<-- [end:fib]
 
#! 캐시가 없으면 fib(30) 은 함수를 269만 번쯤 부름.
#! fib(28) 을 fib(30) 도 부르고 fib(29) 도 부르고… 같은 계산이 계속 반복되니까.
#! 캐시를 붙이면 59번으로 끝남(실제 계산은 31번). 한 번 계산한 건 다시 안 하니까.
 
#! 우리가 get_chain 에 쓰는 건 이 성능 얘기가 아니라 "같은 객체를 돌려받기" 쪽임.
#! 원래 목적은 반복 계산 줄이기인데, 부수 효과인 싱글턴을 이용하는 것.
 
 
#== hashable 이 뭐냐
#> "값이 안 변하고, 그 값으로 고유한 숫자를 뽑을 수 있는 것".
 
# --8<-- [start:hashable]
hash("안녕")        # 됨  — 문자열
hash(42)           # 됨  — 숫자
hash((1, 2))       # 됨  — 튜플
hash(True)         # 됨  — bool
 
hash([1, 2])       # TypeError: unhashable type: 'list'
hash({"a": 1})     # TypeError: unhashable type: 'dict'
hash({1, 2})       # TypeError: unhashable type: 'set'

# hashable은 바뀔 수 있는 것(list·dict·set)은 안 됨
#(1)> 바뀌면 같은 물건인데 숫자가 달라져서 캐시를 못 찾게 됨
# --8<-- [end:hashable]
 
#! 딕셔너리 키에 쓸 수 있는 것 = hashable 한 것.
#! lru_cache 는 { 인자: 결과 } 형태로 저장함. 인자가 키 자리에 들어감.
#! 그래서 인자(입력값)만 hashable 이면 됨. 결과값은 아무거나 상관없음.

#! 궁금했던건 위의 get_chain()은 인자가 없는데 어떻게 키값으로 저장이 될까 했는데 빈 튜플로 키값이 들어감
#! { (): <RunnableSequence 객체> }
 
# --8<-- [start:hashable_fix]
@lru_cache
def f(items):
    return sum(items)
 
f([1, 2, 3])       # TypeError: unhashable type: 'list'
f((1, 2, 3))       # 6  — 튜플로 바꾸면 됨

# 리스트를 넘겨야 하면 tuple() 로 감싸서 넘기는 게 흔한 우회법!
# --8<-- [end:hashable_fix]
 
#! 불변(immutable)이면 대체로 hashable 함. 
#! 튜플은 불변이라 되고 리스트는 가변이라 안 되는 게 딱 그 차이임.
 
#! 예외 하나 → 튜플 안에 리스트가 들어있으면 안 됨.
#! hash((1, [2, 3])) 은 에러. 속까지 전부 불변이어야 함.

# --8<-- [start]
 제약 두 가지
① 인자는 해시 가능(hashable)해야 함 → 아래 섹션 참고
② 같은 입력에 항상 같은 출력인 순수 함수에만 쓸 것
  시간·랜덤·DB 조회처럼 매번 달라지는 건 캐시하면 안 됨
# --8<-- [end]

#! get_chain() 은 인자가 없으니 둘 다 문제없음.
#! maxsize 도 의미가 없음. 저장할 게 하나뿐이니까.
#! 이왕이면 `@lru_cache(maxsize=None)` 이나 3.9+ 의 `@cache` 가 더 맞음.
#! maxsize 가 숫자면 "오래된 것 버리기" 순서를 계속 관리하느라 쓸데없는 일을 함.
#! None 이면 그 관리를 아예 안 해서 조금 더 가벼움.
 
#! cache_info() 로 싱글턴이 실제로 도는지 확인할 수 있음.
#! 요청을 여러 번 보낸 뒤 misses=1 이면 딱 한 번만 만들어졌다는 뜻.
 
#! API 키를 바꾸면 get_chain.cache_clear() 로 캐시를 비워야 새 키가 반영됨.
#! 안 그러면 예전 키로 만든 인스턴스를 계속 씀. 근데 보통은 서버를 재시작함.

#== async 함수에 lru_cache 붙이면 터짐
#> 지금 get_chain 은 동기(def) 라 괜찮음. 나중에 async def 로 바꿀 때 밟는 함정.
 
# --8<-- [start:async_trap]
@lru_cache
async def get_chain():
    return prompt | llm | parser
 
 
chain = await get_chain()
#(1)> 요청 1 — 잘 돌아감
 
chain = await get_chain()
#(2)> 요청 2 — RuntimeError: cannot reuse already awaited coroutine
# --8<-- [end:async_trap]
 
#! `async def` 함수를 부르면 결과가 바로 안 나옴. `코루틴 객체` 라는 게 나옴.
#! 실행 예약표 같은 것. `await` 를 해야 그때 실제로 돌아가고 결과가 나옴.
#! 그리고 이 예약표는 일회용임. 한 번 await 하면 다 쓴 상태가 됨.
 
#! lru_cache 는 "함수가 돌려준 것" 을 저장하는데,
#! async 함수가 돌려준 건 결과가 아니라 그 일회용 예약표임.
#! → 두 번째 호출부터는 이미 다 쓴 예약표를 꺼내서 줌 → 에러.
 
#! 해결은 그냥 동기 함수로 두는 것. Depends 는 `def` 도 받아줌.
#! ChatOpenAI() 만드는 건 await 할 게 없어서 async 일 이유가 없음.
#! async 는 "네트워크·DB 응답을 기다려야 할 때" 쓰는 것. 습관적으로 붙이면 이걸 밟음.
#! 진짜 async 팩토리가 필요하면 lifespan 이나 `async-lru` 라이브러리를 씀.
 
#== 캐시는 어디에 저장되나
#> RAM. lru_cache 는 그냥 파이썬 dict 하나를 만들어 결과를 담아두는 것.
#(1)> 변수를 만들면 RAM 에 올라가는 것과 똑같음.
#(1)>  → 프로세스가 죽으면 사라짐. 서버를 재시작하면 다시 한 번 실제로 실행됨.

# --8<-- [start]
 "캐시" 라는 말이 여러 층에서 쓰여서 헷갈림.
 CPU 캐시     CPU 안 (L1/L2/L3)        하드웨어. 우리가 못 건드림
 lru_cache   RAM (내 파이썬 프로세스)  
 Redis       RAM (별도 프로그램)        여러 서버가 공유할 때
 디스크 캐시    SSD/HDD                  껐다 켜도 남아야 할 때
 # --8<-- [end]

#! lru_cache 는 `'내 프로세스 안'` 에만 있음 → `다른 프로세스와 공유가 안 됨.`
#! uvicorn --workers 4 로 띄우면 프로세스가 4개 → `각자 자기 캐시를 가짐.``
#! `즉 ChatOpenAI 인스턴스가 1개가 아니라 4개 생김.``
 
 
#== lru_cache 를 쓸 때 vs Redis 를 쓸 때
#> 기준은 "공유가 필요한가" 가 아니라 "그게 데이터냐 도구냐" 임.
 
#! `lru_cache 에 담는 건 도구.` 체인·LLM 클라이언트·토크나이저 같은 것.
#! 워커마다 하나씩 있어도 아무 문제 없음. 하는 일이 완전히 같으니까.

 
#! `Redis 에 담는 건 데이터.` 대화 이력·세션·장바구니 같은 것.
#! 워커마다 다르면 안 됨. 워커1 에서 "내 이름은 시연이야" 했는데
#! 워커2 에 붙으니 모른다고 하면 서비스가 깨짐.
 
#! 구분하는 질문 → "워커마다 다른 값이면 사용자가 이상하다고 느끼나?"
#! 체인이 워커마다 다른 객체다   → 사용자는 모름. 문제없음
#! 대화 이력이 워커마다 다르다   → 사용자가 바로 알아챔. 문제됨
 
# --8<-- [start]
get_chain() · get_prompt() · get_encoder()  → lru_cache (도구)
대화 이력 store                               → Redis/DB (데이터)
 
이유가 하나 더 있음 → lru_cache 는 개별 삭제가 안 됨.
데이터는 수정·삭제가 필요한데(대화 삭제, 로그아웃) cache_clear() 는 전부 날리는 것뿐임.
Redis 는 키 단위로 지우고 만료 시간(TTL)도 걸 수 있음.
# --8<-- [end]

 
 
#== Depends — "나는 이게 필요해" 라고 선언만
 
# --8<-- [start:depends]
from fastapi import APIRouter, Depends
from app.dependencies import get_chain
 
router = APIRouter()
 
@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    chain: Runnable[dict, str] = Depends(get_chain),
    #(1)> Depends(get_chain) → 함수를 넘기는 것. 부르는 게 아님 (괄호 없음)
    #(1)> FastAPI 가 요청이 올 때마다 알아서 get_chain() 을 호출해서 결과를 넣어 줌
    #(1)> lru_cache 덕분에 실제로는 캐시된 같은 체인이 옴
):
    result = await chain.ainvoke({"message": request.message})
    return ChatResponse(message=result, session_id=request.session_id, model="gpt-4o-mini")

# --8<-- [end:depends]
 
#! 라우터 안에서 get_chain() 을 직접 불러도 되는 거 아님? → 되긴 함.
#! 근데 Depends 를 쓰면 두 가지가 따라옴.
#! ① /docs 에 의존관계가 문서화됨 (쿼리·헤더를 받을 때만)
#!    → get_chain 처럼 객체만 반환하는건 /docs에서 보이지는 않음
#! ② 테스트할 때 통째로 바꿔치기할 수 있음 (아래 참고)


#== Depends 도 캐시를 함 — 근데 범위가 다름
#> lru_cache 만 캐시하는 줄 알았는데 Depends 도 캐시함.
#> 다만 "요청 하나가 끝날 때까지" 만 기억하고 버림.
 
# --8<-- [start:use_cache]
def get_chain():
    print("체인 만듦")
    return prompt | llm | parser
 
 
def get_logger(chain = Depends(get_chain)):
    #(1)> 이 의존성 안에서도 get_chain 을 또 부름
    ...
 
 
@router.post("/")
async def chat_endpoint(
    chain = Depends(get_chain),
    logger = Depends(get_logger),
    #(2)> get_chain 이 등장한 곳은 총 2군데 (여기 직접 + get_logger 안)
    #(2)> 근데 "체인 만듦" 은 요청당 1번만 찍힘 → FastAPI 가 캐시한 것
):
    ...
# --8<-- [end:use_cache]
 
#! FastAPI 는 `Depends(..., use_cache=True)` 가 기본값임.
#! 한 요청 안에서 같은 의존성이 몇 번 나오든 딱 1번만 호출하고 결과를 돌려씀.
#! 끄고 싶으면 `Depends(get_chain, use_cache=False)` 로 명시.
 
#! 근데 요청이 끝나면 그 캐시는 버려짐. 다음 요청은 처음부터 다시 만듦.
#! 그래서 lru_cache 가 없으면 "요청 100개 → 인스턴스 100개" 가 그대로 남음.
 
#! 정리하면 둘 다 캐시인데 범위가 다름.
#! Depends    → 요청 1개 안에서 1개 (요청 끝나면 사라짐)
#! lru_cache  → 서버(프로세스) 전체에서 1개 (프로세스 죽을 때까지 유지)

 
#== 테스트 용이성 — dependency_overrides
#> 문제 상황 — 이 엔드포인트를 테스트하려면?
#> 실제 OpenAI 를 부르게 됨 → 돈 나가고, 느리고, 답이 매번 달라서 검증도 안 됨
 
# --8<-- [start:override]

# 해결 — 가짜 체인으로 갈아끼우기
# tests/test_chat.py
from fastapi.testclient import TestClient
from app.main import app
from app.dependencies import get_chain

class FakeChain:
    async def ainvoke(self, _):
        return "테스트용 고정 답변"

def get_fake_chain():
    return FakeChain()

app.dependency_overrides[get_chain] = get_fake_chain   # ← 여기서 등록
#(1)>  "get_chain 을 부를 자리에 get_fake_chain 을 대신 써라" 라는 등록
#(1)> 라우터 코드는 한 글자도 안 고침. 밖에서 바꿔치기하는 것
#(1)> 이제 테스트를 돌려도 실제 API 를 안 부름 → 공짜, 빠름, 답이 항상 같음

client = TestClient(app)

def test_chat():
    res = client.post("/chat/", json={"message": "안녕", "session_id": "s1"})

    assert res.status_code == 200
    body = res.json()
    assert body["message"] == "테스트용 고정 답변"
    assert body["session_id"] == "s1"
    assert body["model"] == "gpt-4o-mini"

def test_empty_message():
    res = client.post("/chat/", json={"message": ""})
    #(2)> message 필드 자체를 안 보냄 → 필수 필드 누락이라 422
    assert res.status_code == 422
    
# "get_chain 을 부를 자리에 get_fake_chain 을 대신 써라" 라는 등록
#(1)> 라우터 코드는 한 글자도 안 고침. 밖에서 바꿔치기하는 것
#(1)> 이제 테스트를 돌려도 실제 API 를 안 부름 → 공짜, 빠름, 답이 항상 같음
 
# 테스트 끝나면 원복
app.dependency_overrides.clear()
# --8<-- [end:override]
 
#! 이게 Depends 를 쓰는 진짜 이유인 듯.
#! 라우터가 get_chain() 을 직접 불렀다면 바꿔치기할 방법이 없음.
#! `Depends 로 "밖에서 받아온다" 고 해두면 밖에서 다른 걸 넣어줄 수 있음.`
 
#! 답이 항상 같아야 테스트가 됨. "이 입력이면 이 출력" 을 검증해야 하는데
#! 진짜 LLM 은 매번 다르게 답하니까 검증 자체가 불가능함.
 
 
#== Depends, lru_cache 정리

#! 함수로 객체 반환(팩토리)  → 설정을 한 곳에서 관리. 엔드포인트마다 복붙 안 해도 됨
#! @lru_cache          → 인스턴스를 한 번만 만들어 공유. 인스턴스 100개 생기는 걸 막음
#! Depends             → 밖에서 바꿔치기 가능 (테스트), /docs 연동


#! Depends 없이 get_chain() 을 직접 불러도 싱글턴은 됨 (lru_cache 덕).
#! 거꾸로 lru_cache 없이 Depends 만 쓰면 요청마다 새로 만들어짐.

 
#? lru_cache 대신 lifespan 에 넣는 거랑 뭐가 다른지
#? → 시점 보장(서버 시작 시 vs 첫 호출 시)과 종료 시 정리(yield 뒤 close) 여부가 핵심 차이