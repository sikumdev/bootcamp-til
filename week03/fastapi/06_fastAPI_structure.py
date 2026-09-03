"""
title: FastAPI 프로젝트 구조 — 라우터 · 서비스 분리
tags: [fastapi]
"""

#== HTTP 요청은 뭘로 이루어지나

#! 메서드(Method)  — 무엇을 하려는가. 동사 역할          GET, POST
#! URL(경로)      — 어디에 요청하는가                 /health, /chat/
#! 헤더(Headers)  — 부가 정보. 메타데이터              Content-Type: application/json
#! 바디(Body)     — 전달할 데이터. 주로 POST 에서 씀   {"message": "안녕"}

#! 조회는 GET, 데이터 보내면서 요청하면 POST.
#! GET 은 바디를 거의 안 씀 → 값을 넘기려면 URL 뒤에 ?key=value 로 붙임.


#== 폴더 구조
#> 한 파일에 다 넣으면 금방 못 찾음. 역할별로 쪼개는 것.

# --8<-- [start:tree]
 my_llm_service/               ← 프로젝트 루트 (uvicorn 실행 위치)
 │
 ├── app/                      ← Python 패키지 (__init__.py 필요)
 │   ├── __init__.py           ← "app 폴더를 Python 패키지로 인식" 선언
 │   │
 │   ├── main.py               ← ① 앱 초기화 + 라우터 등록 (안내 데스크)
 │   ├── dependencies.py       ← ② Depends 주입 대상 (LLM 싱글턴 등)
 │   │
 │   ├── routers/              ← ③ HTTP 엔드포인트 정의 (URL·메서드·파라미터)
 │   │   ├── __init__.py
 │   │   ├── health.py         ←    GET /health
 │   │   └── chat.py           ←    POST /chat/, POST /chat/stream
 │   │
 │   ├── services/             ← ④ 비즈니스 로직 (LLM 호출, 프롬프트, 후처리)
 │   │   ├── __init__.py
 │   │   └── llm_service.py    ←    get_chat_response()
 │   │
 │   └── schemas/              ← ⑤ Pydantic 데이터 모델 (요청·응답 타입 계약서)
 │       ├── __init__.py
 │       └── chat.py           ←    ChatRequest, ChatResponse
 │
 ├── .env                      ← API 키 보관. 절대 Git 에 올리지 않음
 ├── .gitignore                ← .env, .venv/ 포함 필수
 └── requirements.txt          ← pip install -r requirements.txt

# uvicorn app.main:app 로 실행 → 루트에서 실행해야 app 을 찾음
# __init__.py 는 빈 파일이어도 됨. "이 폴더는 패키지다" 라는 표시일 뿐
#(1)> 이게 없으면 from app.routers import chat 이 실패함
# --8<-- [end:tree]

#! 핵심 규칙 → routers 는 services 를 부르지만, services 는 routers 를 몰라야 함.
#! 화살표가 한쪽으로만 흐르는 것(단방향 의존성).
#! 서로 부르기 시작하면 나중에 순환 임포트로 터짐.


#== main.py — 안내 데스크

# --8<-- [start:main]
# app/main.py
#(1)> 역할: 앱 초기화 + 라우터 등록 (안내 데스크)
#(1)> 이 파일은 "어떤 URL을 어느 라우터가 처리하는가"만 담당

from fastapi import FastAPI, Request         # Request: 핸들러에 요청 정보 전달
from fastapi.responses import JSONResponse   # 에러 응답을 JSON 형식으로 반환

from app.routers import chat, health, items
#(1)> from app.routers import chat  →  app/routers/chat.py 를 모듈로 임포트
#(1)> → 이 임포트가 성공하려면 app/__init__.py, app/routers/__init__.py 가 존재해야 함

app = FastAPI(
    title="LG CNS AI 서비스",                     # /docs 상단 서비스명
    description="MCP 기반 Agentic AI 서비스 개발자 과정 미니프로젝트",  # /docs 설명
    version="0.1.0",                              # /docs 버전 표시
)

# 전역 예외 핸들러 — Exception을 잡으면 모든 예상치 못한 에러를 처리
#(2)>   @app.exception_handler는 include_router() 전후 어디에 놓아도 동일하게 동작합니다
#(2)>   (미들웨어(@app.middleware)는 등록 순서가 중요하지만, 예외 핸들러는 무관합니다)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """LLM 타임아웃·API 키 만료·연결 오류 등 모든 예외를 500으로 통일.

    클라이언트에는 안전한 메시지만, 상세 오류는 서버 로그에만 기록합니다.
    """
    # 실제 서비스에서는 여기에 로깅 추가 (Sentry, CloudWatch 등)
    #(2)> import logging
    #(2)> logging.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(status_code=500, content={"detail": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."},
        #(3)> 절대 금지: content={"detail": str(exc)}  ← 내부 구조·스택 트레이스 노출
        #(3)> 사용자에게는 안전한 메시지, 로그에만 상세 기록
    )

# include_router: "이 라우터를 앱에 연결해라" — 부서를 안내 데스크에 등록하는 것
app.include_router(health.router)
#(4)> health.router: health.py 안의 router = APIRouter() 인스턴스
#(4)> prefix 없음 → health.py 안의 @router.get("/health") 가 그대로 /health

# prefix="/chat"
#(5)>  → chat.py 안의:
#(5)>   @router.post("/")       → 실제 등록 URL: POST /chat/
#(5)>   @router.post("/stream") → 실제 등록 URL: POST /chat/stream  
#(5)>  tags=["Chat"] → /docs에서 Chat 그룹으로 묶임
app.include_router(chat.router, prefix="/chat", tags=["Chat"])

app.include_router(items.router, tags=["Items"])

# --8<-- [end:main]

#! prefix 와 tags 차이
#! prefix="/chat" → 실제 URL 앞에 붙음. 기능에 영향을 줌
#! tags=["Chat"]  → /docs 화면에서 그룹으로 묶는 라벨. 동작에는 영향 없음

#! 흔한 실수 → prefix 를 "/chat/" 처럼 슬래시로 끝내고
#! router 안에도 "/" 를 쓰면 "/chat//" 가 됨.
#! prefix 는 슬래시 없이 "/chat", router 경로는 "/" 로 시작하는 게 관례.

#== Exception 이 뭔지부터
#> 파이썬에서 에러는 빨간 글씨가 아니라 "객체" 임. 변수에 담을 수 있는 물건.
#> 그리고 에러 객체끼리 족보(상속 관계)가 있음.

# --8<-- [start:exception_tree]
# BaseException
# └── Exception              ← "보통의 에러" 는 전부 여기 아래
#     ├── ValueError         int("가나다")
#     ├── KeyError           d["없는키"]
#     ├── ZeroDivisionError  1 / 0
#     ├── TimeoutError       LLM 응답이 안 옴
#     └── ... (수백 개)
# --8<-- [end:exception_tree]

#! Exception 은 이 족보의 조상.
#! 그래서 Exception 을 잡는다 = 그 아래 자손을 전부 잡는다는 뜻.

#! BaseException 이 아니라 Exception 을 쓰는 이유가 있음.
#! Ctrl+C(KeyboardInterrupt)와 종료(SystemExit)는 Exception 바깥에 있음.
#! BaseException 을 잡으면 서버 끄려고 Ctrl+C 를 눌러도 안 꺼짐.


#== 전역 예외 핸들러
#> 어디서 터지든 한 곳에서 잡아 같은 모양의 응답을 돌려주는 그물.

# --8<-- [start:handler]
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO)
#(1)> INFO 이상만 출력. 개발 중엔 logging.DEBUG 로 낮춰도 됨
logger = logging.getLogger(__name__)
#(1)> __name__ 을 주면 어느 모듈에서 찍은 로그인지 같이 남음

app = FastAPI()


@app.exception_handler(Exception)
#(2)> "무슨 에러든 상관없이 다 이 함수로 보내라"
async def global_exception_handler(request: Request, exc: Exception):
    #(3)> request — 어느 URL 에서 터졌는지 알려고 받음
    #(3)> exc     — 실제로 던져진 에러 객체. str(exc) 하면 메시지가 나옴

    logger.error("%s %s 처리 실패", request.method, request.url, exc_info=True)
    #(4)> exc_info=True — 스택 트레이스까지 로그에 남김. 이게 없으면 원인 추적 불가

    return JSONResponse(
        status_code=500,
        content={"detail": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요."},
        #(5)> content=str(exc) 는 절대 금지. 파일 경로·쿼리·키 일부가 새어 나감
    )

# --8<-- [end:handler]

#! 핸들러가 없으면 예외가 그대로 밖으로 나감.
#! 클라이언트는 이상한 형식의 500 을 받게 됨.
#! 있으면 언제나 {"detail": "..."} 형식이라 프론트가 처리하기 쉬움.

#! str(exc) 를 절대 응답에 넣지 말 것.
#! 에러 메시지에 파일 경로·DB 쿼리·API 키 일부가 들어있을 수 있음.
#! 상세 내용은 로그로만. 사용자에겐 "서버 오류가 발생했습니다" 정도로.

#! 404·422 는 500 으로 안 바뀜. (내가 잘못 알고 있던 것)
#! FastAPI 가 HTTPException·RequestValidationError 전용 핸들러를 이미 갖고 있고
#! 구체적인 핸들러가 우선임. Exception 핸들러는 "아무도 안 잡은 것" 만 받음.

#! 등록 위치는 상관없음. include_router 앞이든 뒤든 똑같이 동작함.
#! 미들웨어(@app.middleware)는 순서가 중요한데 예외 핸들러는 무관함.

#! 핸들러가 응답을 보낸 뒤에도 Starlette 이 예외를 한 번 더 위로 던짐.
#! → 터미널에 traceback 이 찍히는 게 정상. 버그 아님.
#! → 대신 테스트에서 500 응답을 검증하려면
#!    `TestClient(app, raise_server_exceptions=False)` 로 만들어야 함.


#== JSONResponse — 왜 dict 를 그냥 못 돌려주나
#> 엔드포인트에서는 dict 를 return 하면 FastAPI 가 알아서 포장해 줌.
#> 근데 예외 핸들러는 그 자동 포장이 없음 → 완성된 응답 객체를 직접 만들어야 함.

# --8<-- [start:response]
# 엔드포인트 — 자동 포장됨
async def health_check():
    return {"status": "ok"}
    #(1)> FastAPI 가 내부에서 JSONResponse 로 감싸 줌

# 예외 핸들러 — 직접 만들어야 함
return JSONResponse(status_code=500, content={"detail": "..."})
#(2)> ① dict → JSON 문자열로 변환
#(2)> ② Content-Type: application/json 헤더 붙임
#(2)> ③ 상태 코드 지정
# --8<-- [end:response]


#! PlainTextResponse  — 그냥 텍스트
#! HTMLResponse       — HTML
#! StreamingResponse  — 스트리밍 (/chat/stream 만들 때 씀)
#! FileResponse       — 파일 다운로드


#== logging — print 대신 쓰는 것
#> print 도 화면에 찍히긴 함. 근데 서버에서는 중요도 구분이 없어서 문제.

# --8<-- [start:logging]
# 레벨 — 왼쪽이 낮음
# DEBUG    < INFO    < WARNING   < ERROR   < CRITICAL
# 개발용     정상 흐름   좀 이상함    터짐      서버 죽음

logging.basicConfig(level=logging.INFO)
#(1)> 여기서 정한 레벨 이상만 출력됨
#(1)> 개발은 DEBUG, 운영은 WARNING 이상만 보는 식

# 이 한 줄만 나옴. "뭔가 터졌다" 는 것만 알 수 있음
logger.error("에러 발생")

# + 어느 파일 몇 번째 줄에서 터졌는지 전체 추적이 따라옴
logger.error("에러 발생", exc_info=True)
# --8<-- [end:logging]

#! print 를 안 쓰는 이유 → "요청 들어옴" 도 print, "API 키 만료" 도 print 라서
#! 하루에 수만 줄이 쌓이면 그 안에서 진짜 문제를 못 찾음.

#! 레벨을 붙여두면 나중에 Sentry 같은 걸 붙여서
#! "ERROR 이상이면 슬랙으로 알림" 같은 것도 됨.

#! logging.error() 를 직접 부르지 말고 logger 를 만들어 쓰는 게 관례.
#! logger = logging.getLogger(__name__) → 로그에 모듈 이름이 같이 찍힘.


#== 배포할 때 /docs 끄기

# --8<-- [start:prod]


# 배포
app = FastAPI(docs_url=None, redoc_url=None)

# 개발 — 기본값 그대로
# /docs 는 내 API 의 설계도를 통째로 공개하는 것과 같음
#(1)> 어떤 엔드포인트가 있고 무슨 값을 받는지 다 보임 → 공격 표면이 됨
#(1)> redoc 은 /redoc 에 뜨는 또 다른 문서 화면. 같이 꺼야 함
app = FastAPI()

# --8<-- [end:prod]

#! 환경변수로 켜고 끄면 코드를 안 고쳐도 됨.
#! DEBUG=true 면 문서 켜고, 아니면 끄는 식.


