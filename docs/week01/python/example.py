"""
title: FastAPI 게시글 CRUD
tags: [Fastapi, 1주차]
"""

from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from app.database import engine, Base, get_db
from app.models.post import Post
from app.schemas.post import PostResponse, Postcreate, PostUpdate
from sqlalchemy.orm import Session

app = FastAPI(
    title="FastAPI NCP Mailing Service",
    description="게시판과 NCP 메일 발송 기능을 제공하는 서비스입니다.",
    version="1.0.0",
    docs_url ="/docs",
    redoc_url="/redoc"
)

@app.get("/")
def health_check():
    return {"status": "ok"}


@app.get("/ping")
async def ping_db():
    # 연결 시도
    try:
        with engine.connect() as conn:
            return {"status":"connected"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)


#== 게시글 생성
# --8<-- [start]
@app.post("/posts", response_model=PostResponse, summary="새 게시글 생성", description="새로운 게시글을 생성합니다.")
def create_post(post: Postcreate,db: Session = Depends(get_db)):
    
    created_post = Post(**post.model_dump())
    #(1)> post.model_dump() -> Postcreate 객체(pydantic)를 딕셔너리 형태로 변환
    #(1)>  {"title": "제목입니다", "author": "홍길동", "content": "내용입니다"}
    #(1)> ** 은 키워드 인자로 풀어줌
    #(1)>   Post(title="제목입니다", author="홍길동", content="내용입니다")
    #(1)> 즉, DB 객체를 가져오는거임

    db.add(created_post)
    db.commit()
    db.refresh(created_post)

    return created_post
# --8<-- [end]


#!pydantic 모델이 딕셔너리(JSON)로 알아서 바뀌는 건, 함수가 return 해서 클라이언트에게 응답으로 나갈 때임. 
#!FastAPI가 그 순간 자동으로 pydantic 객체 → JSON으로 직렬화

#!응답(나갈 때): pydantic 객체 → JSON. FastAPI가 자동으로 해줌. 내가 .model_dump() 안 써도 됨.
#!DB 객체 생성(중간 작업): pydantic 객체 → dict → SQLAlchemy 객체. 
#!자동 아님. **를 쓰려면 내가 직접 .model_dump()로 dict를 만들어야 함.


#== 게시글 목록 조회
# --8<-- [start]
@app.get("/posts", response_model=List[PostResponse], 
         summary="게시글 목록 조회", description="게시글 목록을 조회합니다.",
         responses= {404: {
                            "description": "게시글 조회 실패",
                            "content": {"application/json": {"example":{"detail": "게시글을 찾을 수 없습니다."}}}
             
                        }
                    }
        )
def get_posts(db: Session=Depends(get_db)):
    posts = db.execute(select(Post).order_by(Post.created_at.desc())).scalars().all()

    if posts is None:
        raise HTTPException(status_code= 404, detail="게시글을 찾을 수 없습니다.")
    
    return posts
# --8<-- [end]


#== 게시글 상세 조회
# --8<-- [start]
@app.get("/posts/{post_id}",response_model=PostResponse, summary="게시글 상세 조회", description="게시글 ID를 기반으로 특정 게시글을 조회합니다.")
def get_post(post_id: int, db: Session=Depends(get_db)):
    post = db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if post is None:
        raise HTTPException(status_code= 404, detail="게시글을 찾을 수 없습니다.")
    
    return post
# --8<-- [end]

#== 게시글 수정
# --8<-- [start]
@app.put("/posts/{post_id}", response_model=PostResponse, summary="게시글 수정", description="게시글 ID를 기반으로 특정 게시글을 수정합니다.")
def update_post(post_id: int, post_update: PostUpdate, db: Session = Depends(get_db)):
    post = db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if post is None:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")

    update_dict = {                                    
        key: value
        for key, value in post_update.model_dump().items()
        if value is not None
    }
    #(1:5)> 사용자가 실제로 보낸(None이 아닌) 필드만 골라 수정하는 부분
    #(1)> 1) model_dump()로 요청을 dict로 변환 → {"title": "새 제목", "content": None}
    #(1)> 2) .items()로 (key, value) 쌍을 하나씩 꺼냄
    #(1)> 3) if value is not None → 값 있는 것만 추림 → {"title": "새 제목"}
    #(1)> 4) 아래 setattr(post, key, value)는 post.title = "새 제목"과 동일

    for key, value in update_dict.items():
        setattr(post, key, value)

    db.commit()
    db.refresh(post)
    return post


#! 필드가 늘 때마다 if문을 하나씩 추가해야 하는 방식(if post_update.title is not None: ...)의 불편함을, 컴프리헨션 + setattr로 필드 개수와 무관하게 처리하도록 바꾼 것.
# --8<-- [end]


#== 게시글 삭제
# --8<-- [start]
@app.delete("/posts/{post_id}", response_model=dict,summary="게시글 삭제", description="게시글 ID를 기반으로 특정 게시글을 삭제합니다.",
             responses= {200:{"description": "게시글 삭제 성공",
                              "content": {"application/json": {"example": {"message":"게시글이 성공적으로 삭제되었습니다."}}}
                              },
                        404: {
                            "description": "게시글 삭제 실패",
                            "content": {"application/json": {"example":{"detail": "게시글을 찾을 수 없습니다."}}}
             
                            }
                        }
            )
def delete_post(post_id: int, db: Session=Depends(get_db)):
    post = db.execute(select(Post).where(Post.id == post_id)).scalar_one_or_none()

    if post is None:
        raise HTTPException (status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    db.delete(post)
    db.commit()
    return {"message": "게시글이 삭제되었습니다."} 
# --8<-- [end]
    


