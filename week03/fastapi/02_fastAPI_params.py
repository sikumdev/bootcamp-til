"""
title: FastAPI 파라미터 — 경로 · 쿼리 · 바디
tags: [fastapi]
"""

#== 파라미터 3규칙
#> 함수 인자를 보고 FastAPI 가 어디서 값을 찾을지 스스로 정함. 규칙은 위에서부터 순서대로.

#! 규칙 1. 경로 파라미터 : 데코레이터 URL 에 {변수명} 이 있으면 → 경로에서 읽음
#! 규칙 2. 바디 파라미터 : 함수 인자 타입이 Pydantic BaseModel 이면 → 요청 본문에서 읽음
#! 규칙 3. 쿼리 파라미터 : 위 두 개가 아닌 나머지 전부 → ?key=value 에서 읽음

#! 순서대로 검사한다는 게 포인트. 이름이 URL 에 있으면 무조건 경로가 먼저임.


#== items.py — 경로 파라미터

# --8<-- [start:items]
# app/routers/items.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/items/{item_id}")
# {item_id} : 중괄호로 감싼 부분이 경로 파라미터 자리표시자
#(1)>  URL /items/42 → item_id = 42 으로 함수에 전달됨

async def get_item(item_id: int):
# item_id: int : 타입 힌트 int → FastAPI가 문자열→정수 자동 변환 + 실패 시 422
    return {"item_id": item_id}
    #(2)> GET /items/42  → {"item_id": 42}     
    #(2)> GET /items/abc → 422 자동 반환       
    #(2)> GET /items/3.5 → 422 자동 반환       

# 경로 파라미터 여러 개 사용
@router.get("/users/{user_id}/posts/{post_id}")
async def get_user_post(user_id: int, post_id: int):

    return {"user_id": user_id, "post_id": post_id}
# URL 로 오는 건 전부 문자열임. "42" 를 42 로 바꾸는 건 타입 힌트를 보고 하는 것
#(3)> 타입 힌트가 장식이 아니라 진짜로 동작하는 자리 (Pydantic 이랑 같은 얘기)
# --8<-- [end:items]

#! /items/3.5 가 422 인 게 의외였음. float 은 int 로 자동 변환 안 해줌.
#! "42" 는 정수로 딱 떨어지니까 되고, 3.5 는 정보가 손실되니까 막는 것.


#== 세 가지가 한 함수에 다 들어간 예

# --8<-- [start:three]

class UserCreate(BaseModel):
    name: str
    email: str

class UserOut(BaseModel):
    id: int
    name: str

@app.post("/users/{team_id}", response_model=UserOut)
async def create_user(
    team_id: int,        # 규칙 1 → URL의 {team_id}와 이름이 같음 → 경로
    user: UserCreate,    # 규칙 2 → BaseModel이니까 → 요청 본문(JSON)
    notify: bool = True, # 규칙 3 → 나머지 → 쿼리 (?notify=false)
):
    return UserOut(id=1, name=user.name)   # ← 이건 규칙과 무관

# 호출 예 → POST /users/7?notify=false + 본문 {"name":"철수","email":"a@b.c"}
# 마지막 return 은 규칙과 상관없음. 규칙은 '들어오는' 쪽 얘기임
# --8<-- [end:three]

#! 인자의 BaseModel 과 response_model= 은 방향이 반대임.
#!
#!            인자의 BaseModel          response_model=
#! 방향       들어옴 (요청 본문)            나감 (응답 본문)
#! 하는 일    JSON → 파이썬 객체 + 검증     파이썬 객체 → JSON + 필드 필터링
#! 위치       함수 괄호 안                데코레이터 안

#! response_model 의 '필드 필터링' 이 중요함.
#! UserOut 에 email 이 없으니 응답에서 빠짐 → 실수로 민감정보를 내보내는 걸 막아줌.


#== chat.py 는 지금 쿼리 파라미터

# --8<-- [start:chat_param]
@router.post("/")
async def chat_endpoint(message: str, session_id: str = "default"):
    response = await get_chat_response(message, session_id)
    return {"message": response, "session_id": session_id}
# message 도 session_id 도 BaseModel 이 아니고 URL 에도 없음 → 규칙 3, 쿼리
#(1)> 호출은 POST /chat/?message=안녕&session_id=s1
#(1)> session_id 는 기본값이 있으니 안 넘겨도 됨
# --8<-- [end:chat_param]

#! POST 인데 쿼리로 받는 게 어색함. 긴 문장을 URL 에 넣는 것도 이상하고. 한글이나 특수문자가 들어가면 URL 인코딩 문제도 생김.
#! Pydantic 모델을 만들어 바디로 받는 게 맞는 방향 (규칙 2).

# --8<-- [start:better]
# app/schemas/chat.py 에 만들어두고
class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

# 라우터에서는 이렇게
@router.post("/")
async def chat_endpoint(req: ChatRequest):
    response = await get_chat_response(req.message, req.session_id)
    return {"message": response, "session_id": req.session_id}
# 인자가 BaseModel 이 되는 순간 규칙 2(바디파라미터) → 본문에서 읽음
#(1)> 호출은 POST /chat/ + 본문 {"message": "안녕", "session_id": "s1"}
# --8<-- [end:better]

#! schemas/ 폴더를 따로 두는 이유가 이거인 듯.
#! 요청·응답 모델은 라우터랑 서비스 양쪽에서 쓰게 되니까 한 군데 모아두는 것.