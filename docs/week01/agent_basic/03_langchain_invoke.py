"""
title: LangChain — invoke, stream
tags: [langchain, ai-agent]
"""

#== 대원칙
#> 문법은 하나, 재료만 바뀐다. 재료 모양은 조립품 맨 앞 부품이 정한다.

# --8<-- [start:principle]
# LangChain 은 부품을 파이프(|)로 조립하는 도구 → `langchain =prompt|model|parser`
# 조립한 모든 것에 invoke() 라는 똑같은 실행 버튼이 달린다

runnable.invoke(입력, config=None)
# --8<-- [end:principle]

#== 패턴 1 — LLM 단독

# --8<-- [start:llm]
llm = ChatOpenAI(model="gpt-4o-mini")
answer = llm.invoke("고양이 설명해줘") # 입력은 그냥 문자열
print(answer.content) # 출력은 AIMessage 객체
#(1)> 출력은 문자열이 아니라 AIMessage 객체 → .content 로 꺼낸다
# --8<-- [end:llm]

#! 단발성 질문이면 여기서 끝. 패턴 2 는 재사용할 때만 쓴다.


#== 패턴 2 — 프롬프트 체인
#> 빈칸 뚫린 양식지를 만들어두고 빈칸만 갈아 끼우는 방식.

# --8<-- [start:chain]
prompt = ChatPromptTemplate.from_template("{topic}를 {style} 스타일로 설명해줘")
chain = prompt | llm

# 빈칸이 여러 개니까 "어느 칸에 뭘 넣을지" 이름표가 필요해서 딕셔너리 사용
answer = chain.invoke({"topic": "고양이", "style": "친근한"}) # 입력은 딕셔너리
print(answer.content) # 출력은 AIMessage 객체
# --8<-- [end:chain]

#! `빈칸이 없으면 invoke({})` — 빈 딕셔너리를 넣어야 한다. None 이나 문자열은 안 된다.
#! `빈칸이 1개`면 문자열도 통하지만, 되다 안 되다 해서 헷갈리니 항상 딕셔너리로 쓰는 습관을 들이자!

# --8<-- [start:parser]
# 파서를 붙이는 경우  → .content 없이 바로 문자열로 받는다

chain = prompt | llm | StrOutputParser()
answer = chain.invoke({"topic": "고양이"})
print(answer)
# --8<-- [end:parser]


#== 패턴 3 — 에이전트
#> 패턴1,패턴2와 종류가 다름. 부품 조립이 아니라 도구를 쥐여준 직원을 고용하는 것에 가깝다.

# --8<-- [start:agent]
agent = create_agent(model=llm, tools=[get_weather])

result = agent.invoke({"messages": "서울 날씨 어때?"})
#(1)> 키 이름 messages 는 에이전트가 정해놓은 것이라 바꿀 수 없다
print(result["messages"][-1].content)
#(2)> 출력은 dict. 마지막 메시지가 최종 답변
# --8<-- [end:agent]

#! 패턴 1·2 는 한 번 묻고 한 번 답하면 끝나지만 에이전트는 "툴 쓸게 → 툴 실행 → 결과 보고 답변" 알아서 반복
#! 대화가 계속 쌓이니 목록 전체를 들고 다녀야 해서, 입력도 출력도 messages 라는 리스트다. 
#! (정확히는 딕셔너리 안 messages라는 키의 매칭되는 리스트 값들)


#== 패턴 비교
#! | 패턴 | 입력 | 출력 형태 | 코드 |
#! |---|---|---|---|
#! | LLM 단독 | `"문자열"` | `AIMessage` (객체) | `.content` |
#! | 프롬프트 체인 | `{"빈칸": "값"}` | `AIMessage` (객체) | `.content` |
#! | 에이전트 | `{"messages": ...}` | `dict` | `["messages"][-1].content` |


#== 꺼내기 규칙
#> ["대괄호"] 는 딕셔너리에, .점 은 객체에.

# --8<-- [start:unwrap]
result                          # dict       {"messages": [...]}
result["messages"]              # list       [HumanMessage, AIMessage]
result["messages"][-1]          # AIMessage  마지막 = 최종 답변
result["messages"][-1].content  # str        "서울은 맑습니다"
# --8<-- [end:unwrap]


#== stream — 입력은 같고 출력만 다르다
 
# --8<-- [start:stream]
# 체인은 invoke 와 입력이 완전히 동일. 결과값이 조각으로 나오는 것만 다르다

for chunk in chain.stream({"topic": "고양이"}):
    print(chunk.content, end="", flush=True)
# --8<-- [end:stream]

#! `(참고)`  chunk란 최종 반환값을 여러 조각으로 쪼갠 덩어리라고 생각하면 됌.
#! 에이전트만 chunk 모양이 invoke 와 다름 (stream_mode로 갈림)

#== 에이전트 stream — 모드별 chunk 형태
#> 셋 다 같은 실행인데 chunk 모양이 다르다. 마지막 chunk 를 놓고 비교하면 이렇다.
 
# --8<-- [start:modes]
# stream 모드 : values
#(1)> invoke 반환값과 형태가 같다. 매번 처음부터 전부 들어있는 스냅샷
{'messages': [HumanMessage, AIMessage, ToolMessage, AIMessage]}
 
# stream 모드 : updates  (기본값)
#(2)> 바깥 키가 노드 이름(model·tools)으로 되어 있어서 → chunk["messages"] 는 KeyError
{'model': {'messages': [AIMessage]}}
 
# stream 모드 : messages
#(3)> 애초에 dict 가 아니라 튜플 → chunk, meta 두 개로 받아야 한다
( AIMessageChunk(content=''), {'langgraph_node': 'model', ...} )
# --8<-- [end:modes]
 
#! invoke 와 같은 형태로 끝나는 건 values 하나뿐이고 updates는 한 겹 더 감싸여 있는 딕셔너리 형태, messages는 튜플
#! `values`   → invoke 결과를 원하는데 중간도 보고 싶다 
#! `updates`  → 어느 단계가 돌고 있는지 알고 싶다 
#! `messages` → 글자를 한 자씩 찍고 싶다 


#== 에이전트 stream ① 기본 = updates
 
# --8<-- [start:updates]
for chunk in agent.stream({"messages": "서울 날씨 어때?"}):
    print(chunk)
#(1:2)> # chunk 값 형태
#(1)> {'model': {'messages': [AIMessage(content='', tool_calls=[...])]}}
#(1)> {'tools': {'messages': [ToolMessage(content='서울은 맑음, 25도')]}}
#(1)> {'model': {'messages': [AIMessage(content='서울은 맑고 25도입니다.')]}}

#(1)> # 바깥 키가 messages 가 아니라 노드 이름(model·tools) → chunk["messages"] 는 KeyError
#(1)> # 각 chunk 에는 그 단계에서 새로 추가된 메시지만 들어있다 (누적 아님)

 
for chunk in agent.stream({"messages": "서울 날씨 어때?"}): # 딕셔너리 한개씩 가져오는 for문
    for node, update in chunk.items(): # for k,v in 딕셔너리.items()
        print(node, "→", update["messages"][-1].content) # 키 → 값["messages"][-1].content
# --8<-- [end:updates]
 
 
#== 에이전트 stream ② values = 매 단계의 전체 상태
 
# --8<-- [start:values]
for chunk in agent.stream({"messages": "서울 날씨 어때?"}, stream_mode="values"):
    print(len(chunk["messages"]), chunk["messages"][-1].type)


# 출력형태
#(1)> chunk["messages"] 가 매번 처음부터 지금까지 전부
#(1)> chunk 1 → {'messages': [HumanMessage]}
#(1)> 
#(1)> chunk 2 → {'messages': [HumanMessage, AIMessage]}
#(1)> 
#(1)> chunk 3 → {'messages': [HumanMessage, AIMessage, ToolMessage]}
#(1)> 
#(1)> chunk 4 → {'messages': [HumanMessage, AIMessage, ToolMessage, AIMessage]} 
#(1)> chunk4는 invoke 결과와 동일

# 결과
#(2)> 1 human
#(2)> 2 ai
#(2)> 3 tool
#(2)> 4 ai

# invoke 의 결과값은 values 의 마지막 chunk 결과값과 같음 (출력 형식이 같음)
result = agent.invoke({"messages": "서울 날씨 어때?"})
print(len(result["messages"]), result["messages"][-1].type)
# --8<-- [end:values]

#! values 와 invoke 의 차이는 '중간을 보느냐' 뿐, invoke 는 왕복이 끝날 때까지 기다렸다가 한 번에, values 는 단계마다 미리 보여줌.
#! 그래서 진행 표시나 오래 걸리는 툴의 중간 결과를 띄울 때 values 를 쓴다.
 
 
#== 에이전트 stream ③ messages = 타자 효과
 
# --8<-- [start:msgmode]
for chunk, meta in agent.stream({"messages": "안녕"}, stream_mode="messages"):
    print(chunk.content, end="", flush=True)
#(1:2)> # 결과값  →  (  AIMessageChunk(content=''), {'langgraph_node': 'model', ...}  )
#(1)> 1)  유일하게 토큰 단위 청크로 ChatGPT 처럼 글자가 한 자씩 찍힌다
#(1)> 2) (chunk, meta) 튜플로 오니까 두 개의 변수로 값을 받아야 한다
# --8<-- [end:msgmode]
 
#! 타자 효과는 "messages", 진행 단계 추적은 "values", 디버깅은 기본값(updates).
#! `values 는 완성된 메시지 단위라 글자가 한 자씩 찍히지 않는다.`
 
 
#== 헷갈릴 때 — 추측하지 말고 찍어보기 (디버깅 습관)
 
# --8<-- [start:debug]
# 출력 모양을 모를 때 확인해보기
result = agent.invoke({})
print(result)           

# 청크 조각들 확인해보기
for chunk in agent.stream({}):
    print(chunk)
# --8<-- [end:debug]
 
 