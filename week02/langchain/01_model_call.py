"""
title: 첫 LLM 호출과 LangSmith 추적
tags: [langchain]
"""

#== .env파일에 키 넣기
#> API 키를 코드에 직접 쓰지 않고 .env 파일에 적어둔다.

# --8<-- [start:env]
# .env  (프로젝트 최상단)
OPENAI_API_KEY=sk-...
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_PROJECT=day1
# --8<-- [end:env]


#== 환경 변수란?
#> macOS 같은 운영체제가 메모리에 `이름 = 값` 형태로 저장하고 있는 정보로 os가 실행 중일때 
#> 메모리에 존재하는 값

# --8<-- [start:load]
from dotenv import load_dotenv
import os

# .env 파일을 읽어서 → os 환경변수에 등록해주는 함수
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
#(2)> (전체 흐름)`.env` 파일에 작성 → `load_dotenv()`가 읽어서 OS 메모리에 등록  → `os.getenv()`로 꺼내 씀
llm = ChatOpenAI()
# --8<-- [end:load]

#! ChatOpenAI() 객체에 파라미터로 api_key 를 안 넘겼는데 연결되는 이유?
#! - ChatOpenAI() 가 내부에서 os.getenv("OPENAI_API_KEY") 를 자동으로 찾아 쓴다.
#! - 흐름: .env → load_dotenv() → 환경변수 등록 → ChatOpenAI() 내부에서 자동 참조


#== LangSmith 자동 추적
# --8<-- [start]
# LANGSMITH_TRACING=true 만 등록돼 있으면 이후 모든 랭체인 호출이 자동으로 기록된다.
# 코드에 LangSmith 관련 import 나 설정을 추가할 필요가 없다.
# --8<-- [end]



#== LLM 객체 만들기

# --8<-- [start:llm]
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# --8<-- [end:llm]
#!  temperature — 답변의 확률 다양성 (0 에 가까울수록 매번 비슷하고 안정적, 1 에 가까울수록 다양하고 창의적)

#== 호출 ① 문자열로

# --8<-- [start:call1]
response = llm.invoke("LG CNS의 주요 사업을 3줄로 요약해줘")
print(response.content) # response는 AIMessage 객체
# --8<-- [end:call1]
#! invoke 메서드에 문자열을 넣으면 내부에서 HumanMessage 하나로 변환된다


#== 호출 ② 메시지 리스트로
#> 역할을 지정하려면 메시지 객체를 직접 넘긴다.

# --8<-- [start:call2]
from langchain_core.messages import SystemMessage, HumanMessage

response = llm.invoke([
    # SystemMessage 는 모델의 역할·말투·규칙을 정하는 자리
    SystemMessage(content="당신은 IT 기업 분석 전문가입니다. 한국어로 간결하게 답하세요."),
    HumanMessage(content="LG CNS의 주요 사업을 3줄로 요약해줘"),
])

print(response.content) # response는 AIMessage 객체
# --8<-- [end:call2]
#!문자열 호출로는 역할을 지정할 수 없다. 그게 위의 문자열로 호출하는 방식과의 유일한 차이!


#== 응답 객체에서 꺼낼 수 있는 것
#> invoke 의 결과는 AIMessage 객체다. 

# --8<-- [start:attrs]
# 결과  →  <class 'langchain_core.messages.ai.AIMessage'>
print(type(response))         

# 결과  →  응답 텍스트
print(response.content)        

# 결과  → {'input_tokens': 21, 'output_tokens': 112, 'total_tokens': 133, ...}
print(response.usage_metadata)
#(1)> 토큰 사용량. 어느 모델이든 같은 형태로 정리해서 준다 → 비용 계산에 쓴다

# 결과  → {'model_name': 'gpt-4o-mini-2024-07-18', 'finish_reason': 'stop', ...}
print(response.response_metadata)
#(2)> 제공사가 준 원본 응답 정보. 모델명·종료 이유·id 등
#(2)> finish_reason 이 'stop' 이면 정상 종료, 'length' 면 길이 제한에 잘린 것

# 결과  → [] 
print(response.tool_calls)     

# --8<-- [end:attrs]

#! usage_metadata 와 response_metadata 는 내용이 겹쳐 보이지만 성격이 다르다.
#! usage_metadata = 랭체인이 표준 형태로 정리한 것 (모델을 바꿔도 키가 같다)
#! response_metadata = 제공사 응답 그대로 (OpenAI 는 token_usage, 다른 모델은 다른 이름)


#== config — 태그와 메타데이터
#> LangSmith 대시보드에서 이 호출만 골라 보려고 붙인다.

# --8<-- [start:config]
# tags 는 필터용 라벨, metadata 는 검색 가능한 부가 정보

config = {
    "tags": ["day1", "테스트"],
    "metadata": {"수강생": "김시연", "목적": "첫 호출 확인"},
}

response = llm.invoke("LG CNS의 주요 사업을 3줄로 요약해줘", config=config)
#(2)> 대시보드에서 Filter by tag: "day1" 로 이 호출만 볼 수 있다
# --8<-- [end:config]

#? 스트리밍할 때도 usage_metadata 가 나오는지 (마지막 chunk 에만 붙는다고 들었음)
#? temperature 말고 top_p, max_tokens 는 각각 뭘 조절하는지