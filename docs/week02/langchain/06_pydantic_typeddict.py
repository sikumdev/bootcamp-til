"""
title: Pydantic 모델
tags: [langchain]
"""

#== 왜 Pydantic 인가
#> 프롬프트로 "이 형식으로 답해줘" 부탁하는 대신, 답의 모양을 클래스로 못 박는 방식.
#> 필드 설명이 그대로 LLM 에게 전달되고, 돌아온 값은 자동으로 검증됨.

#! 툴 만들 때 docstring 이 LLM 이 읽는 설명서였던 것과 같은 원리임.
#! 여기선 Field(description=...) 가 그 역할을 함.


#== 필드 정의

# --8<-- [start:basic]
from pydantic import BaseModel, Field
from typing import Literal, Optional

class TaskClassification(BaseModel):
    """업무 분류 모델 — AI 가 이 필드들을 채움"""

    category: Literal["기술지원", "구매요청", "일정조율", "기타"] = Field(
        description="업무 유형 4가지 중 하나. 반드시 이 4가지 중에서 선택."
    )
    #(1:3)> Literal 로 선택지를 박아두면 다른 값이 오는 순간 에러
    #(1)> 프롬프트에 "넷 중 하나로" 라고 쓰는 것보다 확실함

    priority: int = Field(
        description="우선순위 1(낮음)~5(높음)",
        ge=1,   # greater than or equal
        le=5,   # less than or equal
    )
  
    # max_length 는 글자 수 제한
    summary: str = Field(description="핵심 요약 20자 이내", max_length=20)


    urgent: bool = Field(description="24시간 이내 처리가 필요하면 True")

    assignee: Optional[str] = Field(
        default=None,
        description="담당 부서명. 불명확하면 None"
    )
    #(4:4)> Optional = 없어도 됨. default 를 주면 안 넣었을 때 그 값이 들어감
    #(4)> default 가 없는 필드는 전부 필수임
# --8<-- [end:basic]

#! description 은 주석이 아님. LLM 이 실제로 읽는 지시문임.
#! "반드시 이 4가지 중에서" 처럼 프롬프트 쓰듯 적어야 정확도가 올라감.
#! 타입 힌트가 장식이 아니라 진짜로 검사됨. priority 에 "3" (문자열) 을 넣으면
#! 파이썬은 그냥 넘어가지만 Pydantic 은 int 로 바꾸거나 에러를 냄.

#== 타입별로 뭐가 강제되는가
 
#! Literal["개발","기획"]  → 둘 중 하나.        Pydantic 이 강제
#! list[str]              → 문자열 여러 개.     검증 없음 (description 으로 부탁만)
#! list[Literal[...]]     → 정해진 목록에서 여러 개. Pydantic 이 강제
#! str | None + default   → 없어도 됨.          생략 가능
 
#! list[Literal] 은 목록 밖 값이 오면 에러가 남 → description 으로 부탁하는 것보다 훨씬 안정적.
#! 대신 "기타" 같은 탈출구를 꼭 만들어둘 것. 없으면 LLM 이 억지로 고르거나 빈 리스트를 냄.


#== 검증은 언제 도는가

# --8<-- [start:when]
# 객체를 만드는 그 순간 전부 검사함. 통과 못 하면 아예 안 만들어짐
t = TaskClassification(
    category="기술지원", priority=3, summary="프린터 고장", urgent=False
)

t2 = TaskClassification(category="기술지원", priority=9, summary="...", urgent=True)
# ValidationError: Input should be less than or equal to 5
#(2)> le=5 를 어겨서 터짐

# dict 가 필요하면 변환해서 씀
print(t.summary)        # 속성 접근 (o)
print(t["summary"])     # dict 접근 (x)
print(t.model_dump())   # dict 로 변환. 중첩 모델까지 전부 dict 가 됨
# 객체  → dict 변환 원할 시 model_dump() 사용
#(3)> RunnableBranch 조건함수처럼 dict 를 원하는 곳에 넘길 땐 model_dump() 필요
# --8<-- [end:when]


#== field_validator — 필드 하나를 직접 검사

# --8<-- [start:field]
from pydantic import field_validator, model_validator

class SmartTaskClassification(BaseModel):
    category: str = Field(description="업무 유형")
    priority: int = Field(description="우선순위 1~5", ge=1, le=5)
    summary:  str = Field(description="20자 이내 요약")

    @field_validator('summary')
    @classmethod
    def summary_must_be_concise(cls, v: str) -> str:
        """요약 앞뒤 공백 제거 후 길이 재확인"""
        v = v.strip()
        if len(v) > 20:
            raise ValueError(f"요약은 20자 이내여야 합니다 (현재:{len(v)}자)")
        return v
    #(1:9)> ('summary') 로 어느 필드를 볼지 지정. v 가 그 필드에 들어온 값
    #(1)> 값을 손보고 나서 반드시 return 해야 함. 안 하면 None 이 저장됨
    #(1)> @classmethod 가 필요한 이유 → 객체가 만들어지기 전에 도는 검사라서
    #(1)> 객체가 없으니 self 를 못 쓰고 클래스(cls) 를 받음
# --8<-- [end:field]

#! max_length=20 이랑 뭐가 다른지 헷갈렸는데, 이건 공백을 먼저 지우고 잰다는 게 다름.
#! "  긴 요약  " 처럼 공백이 붙어 오면 max_length 는 공백까지 세서 억울하게 터짐.
#! 값을 고칠 수 있다는 게 field_validator 의 핵심. 검사만 하는 게 아님.


#== model_validator — 필드끼리의 관계를 검사

# --8<-- [start:model]
    @model_validator(mode='after')
    def urgent_category_check(self):
        """우선순위 5(긴급)는 '기타' 카테고리로 분류 불가"""
        if self.priority == 5 and self.category == "기타":
            raise ValueError("우선순위 5(긴급)는 '기타' 카테고리로 분류할 수 없습니다")
        return self
    #(1:7)> 필드 두 개를 같이 봐야 하는 규칙은 여기서 검사
    #(1)> mode='after' = 각 필드 검증이 끝난 뒤에 돎 → self 로 값을 꺼내 쓸 수 있음
    #(1)> 이것도 return self 를 빼먹으면 안 됨

try:
    t = SmartTaskClassification(category="기타", priority=5, summary="긴급 처리")
except Exception as e:
    print(e)   # 우선순위 5(긴급)는 '기타' 카테고리로 분류할 수 없습니다
# --8<-- [end:model]

#! 정리
#! field_validator = 필드 하나. 값을 다듬거나 그 필드만의 규칙
#! model_validator = 여러 필드 조합. "A 면 B 는 안 됨" 같은 규칙


#== TypedDict — 검증 없는 모양 선언

# --8<-- [start:typeddict]
from typing import TypedDict

class ChatState(TypedDict):
    question:    str
    answer:      str
    tokens_used: int

state: ChatState = {"question": "안녕?", "answer": "", "tokens_used": 0}
state["answer"] = "안녕하세요!"

state["tokens"] = 10
#(2)> 오타인데 실행은 됨. 딕셔너리에 추가됨

print(type(state))   # <class 'dict'>
#(3)> 런타임엔 그냥 dict. TypedDict 라는 타입이 따로 있는 게 아님
# --8<-- [end:typeddict]

#! TypedDict 는 힌트만 주는 것. 진짜로 막아주는 건 없음.
#! Pydantic 은 객체를 만들 때 실제로 검사하고, 틀리면 에러를 냄.
#! 그래서 LLM 이 채우는 값(믿을 수 없는 값)은 Pydantic 으로 받아야 함.
#! 반대로 내가 관리하는 상태(LangGraph State)는 TypedDict 로 충분함.
