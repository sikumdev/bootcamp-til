"""
title: dependencies.py — 버전별 정리
tags: [fastapi]
"""


#== v1 — 체인 하나로 뭉치기
#> 제일 단순함. 체인만 필요할 때.

# --8<-- [start:v1]
from dotenv import load_dotenv
load_dotenv()

#  싱글턴 패턴을 위한 표준 라이브러리 데코레이터
#(1)> 함수 결과를 캐시 → 같은 인수면 재계산 없이 반환
from functools import lru_cache   
from langchain_openai import ChatOpenAI  

from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


@lru_cache()      
def get_chain() -> Runnable[dict, str]:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0,)
    prompt =  ChatPromptTemplate.from_messages([
                                                ("system", "유용한 AI 어시스턴트입니다."),
                                                ("human", "{message}"), ])
    parser = StrOutputParser()
    return prompt|llm|parser

# --8<-- [end:v1]

#! 한계 → 프롬프트를 따로 꺼내 쓸 수가 없음.
#! 토큰 수를 세려면 프롬프트가 완성된 메시지를 봐야 하는데 체인 안에 갇혀 있음.
#! 그래서 v2 가 나옴.


#== v2 — 프롬프트를 따로 빼기
#> 프롬프트를 라우터에서도 써야 할 때. 토큰 계산이 그런 경우.

# --8<-- [start:v2]
from dotenv import load_dotenv
load_dotenv()

#  싱글턴 패턴을 위한 표준 라이브러리 데코레이터
#(1)> 함수 결과를 캐시 → 같은 인수면 재계산 없이 반환
from functools import lru_cache   
from langchain_openai import ChatOpenAI  

from langchain_core.runnables import Runnable
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

import tiktoken

MODEL_NAME = "gpt-4o-mini"

@lru_cache
def get_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", "유용한 AI 어시스턴트입니다."),
        ("human", "{message}"),
    ])

# 프롬프트를 별도 함수로 빼고, 체인은 그걸 갖다 씀
#(2)> get_prompt() 도 캐시되니까 체인 안의 것과 같은 객체임
#(2)> MODEL_NAME 을 상수로 뺀 것도 포인트. 응답에 모델명을 넣을 때 재사용
@lru_cache
def get_chain() -> Runnable[dict, str]:
    llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
    return get_prompt() | llm | StrOutputParser()

# 토큰 계산기도 만드는 비용이 있어서 캐시함
#(3)> 인수가 있으니 모델별로 따로 저장됨
#(3)> 모르는 모델명이면 KeyError → 기본 인코딩으로 넘어감
@lru_cache
def get_encoder(model: str = MODEL_NAME):
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        return tiktoken.get_encoding("o200k_base")  # gpt-4o 계열 기본 인코딩

# --8<-- [end:v2]

#! @lru_cache 와 @lru_cache() — 괄호가 있든 없든 동작은 같음.



#== v3 — Annotated 로 타입 별칭 만들기
#> 라우터에서 Depends(...) 를 매번 쓰기 귀찮을 때.

# --8<-- [start:v3]
from typing import Annotated
from fastapi import Depends

# Annotated[타입, 메타정보] → "이 타입인데 이런 사정이 있다" 를 한 덩어리로
#(1)> 앞은 진짜 타입, 뒤는 FastAPI 에게 주는 지시
ChainDep = Annotated[Runnable[dict, str], Depends(get_chain)]
PromptDep = Annotated[ChatPromptTemplate, Depends(get_prompt)]


# 라우터에서 이렇게 쓰게 됨
async def chat_endpoint(request: ChatRequest, chain: ChainDep, prompt: PromptDep):
    ...

# --8<-- [end:v3]

#! 두 방식 비교
#! chain: Runnable[dict, str] = Depends(get_chain)   ← 기본. 길지만 직관적
#! chain: ChainDep                                    ← Annotated. 짧고 재사용 편함

#! Annotated 쪽이 나은 점 하나 더 → 기본값 자리가 비어 있음.
#! = Depends(...) 는 문법상 '기본값' 자리에 들어가는 거라,
#! 기본값 있는 인자 뒤에 기본값 없는 인자를 못 두는 파이썬 규칙에 걸릴 수 있음.


#== 세 버전 언제 쓰나

#! v1 — 체인만 있으면 될 때. 처음 배울 때 이걸로 시작
#! v2 — 프롬프트나 인코더를 따로 꺼내 써야 할 때
#! v3 — v1/v2 위에 얹는 것. 라우터 코드를 짧게 만드는 용도

#! v3 는 v1·v2 와 배타적이지 않음. 어느 버전이든 Annotated 를 얹을 수 있음.
#! 실제로는 v2 + v3 조합이 제일 많이 쓰일 듯.

