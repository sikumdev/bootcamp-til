"""
title: ChatPromptTemplate 
tags: [langchain]
"""

#== 템플릿 만들기
#> {중괄호}가 변수 자리. f-string 아니니까 중괄호는 하나만 씀.

# --8<-- [start:make]
chat_template = ChatPromptTemplate.from_messages([
    ("system", "당신은 {industry} 산업 전문 분석가입니다. {tone} 어조로 한국어로 답하세요."),
    ("human", "{task}에 대해 {format}으로 분석해주세요."),
])
#(1:4)> from_messages 에 들어가는 건 리스트임. 딕셔너리 아님
#(1)> 리스트의 원소는 ("역할", "템플릿 문자열") 튜플
#(1)> 역할 자리에 쓰는 값: system · human · ai
#(1)> 딕셔너리는 나중에 invoke 로 값 채울 때 쓰는 것 — 다른 단계임
# --8<-- [end:make]

#! 템플릿 문자열에 공백 빼먹으면 그대로 붙어서 나옴.
#! "당신은{industry}" → "당신은제조업" 이 됨. 변수 앞뒤 공백 확인할 것.


#== 템플릿 안을 들여다보기
#> 템플릿이 어떤 메시지로 변환되는지 눈으로 확인하는 용도.

# --8<-- [start:inspect]
print(chat_template.input_variables)
# ['format', 'industry', 'task', 'tone']
#(1)> 채워야 할 빈칸 이름. invoke 에 넣을 키가 이거임

# format_messages 는 빈칸만 채우고 끝. LLM 호출 안 함
#(2)> 딕셔너리가 아니라 키워드 인자로 넘김 (industry="제조업" 형태)
#(2)> 이미 딕셔너리로 갖고 있으면 format_messages(**d) 로 풀어서 넘기면 됨
filled = chat_template.format_messages(
    industry="제조업",
    tone="전문적이고 간결한",
    task="ERP 도입 리스크",
    format="번호 목록 3가지",
)

for msg in filled:
    print(type(msg).__name__, ":", msg.content[:30])
# SystemMessage : 당신은 제조업 산업 전문 분석가입니다. ...
# HumanMessage : ERP 도입 리스크에 대해 번호 목록 3가지로 ...
#(3:2)> 반환값은 리스트고, 안에는 SystemMessage·HumanMessage 객체가 들어있음
# --8<-- [end:inspect]

#! format_messages 와 invoke 의 차이.
#! format_messages(키워드 인자) → 메시지 리스트 만들고 멈춤. 확인용
#! chain.invoke({딕셔너리}) → 그 메시지를 만들어서 LLM 까지 보냄. 실행용


#== 체인으로 연결해서 호출

# --8<-- [start:chain]
# 템플릿 출력이 llm 입력으로 자동 전달됨
chain = chat_template | llm

result = chain.invoke({
    "industry": "제조업",
    "tone": "전문적이고 간결한",
    "task": "ERP 도입 리스크",
    "format": "번호 목록 3가지",
})

print(result.content)

# --8<-- [end:chain]


#== 같은 템플릿으로 여러 번 — ** 언패킹

# --8<-- [start:reuse]
industries = [
    {"industry": "금융업", "tone": "보수적이고 신중한"},
    {"industry": "유통업", "tone": "실용적인"},
    {"industry": "헬스케어", "tone": "규정 중심적인"},
]

for config in industries:
    result = chain.invoke({
        **config,
        #(1)> **config 는 딕셔너리를 풀어서 바깥 딕셔너리에 합치는 것
        #(1)> 예시)  {**{"a":1}, "b":2} → {"a":1, "b":2}
        "task": "ERP 도입 리스크",
        "format": "번호 목록 3가지",
    })

    print(f"\n=== {config['industry']} ===")
    print(result.content)
# --8<-- [end:reuse]