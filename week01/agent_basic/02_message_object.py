"""
title: LangChain — Message 객체 
tags: [langchain]
"""

#== 상속 구조
#> 아래 Message객체들은 모두 BaseMessage 를 물려받아서 .content 와 .type 을 갖는다.

# --8<-- [start:tree]
 BaseModel (pydantic)
   └─ BaseMessage           ← content, type, id, name
        ├─ SystemMessage    ← 설정(instruction)
        ├─ HumanMessage     ← 사람(query)
        ├─ AIMessage        ← + tool_calls, usage_metadata
        └─ ToolMessage      ← + tool_call_id, status, artifact
# --8<-- [end:tree]


#== 각 객체의 정의

# --8<-- [start:class]
 class BaseMessage(Serializable):
     content: str | list
     type: str
     name: str | None = None
     id: str | None = None

#Literal 이라 바꿀 수 없는 이름표. 딕셔너리만 봐도 뭐였는지 알 수 있다
 class HumanMessage(BaseMessage):
     type: Literal["human"] = "human" 

 class AIMessage(BaseMessage):
     tool_calls: list[ToolCall] = Field(default_factory=list)
     #(1)> default_factory=list → 툴을 안 쓰면 자동으로 [] 빈리스트 반환
     usage_metadata: UsageMetadata | None = None
     type: Literal["ai"] = "ai"


 class ToolMessage(BaseMessage):
     tool_call_id: str
     #(2)> tool_call_id 만 기본값이 없다 = 필수 항목
     status: Literal["success", "error"] = "success"
     type: Literal["tool"] = "tool"
# --8<-- [end:class]


#== AIMessage 는 두 얼굴
#> 같은 클래스인데 상황에 따라 채워지는 칸이 다르다.

#! `툴 호출용` → .content 는 비어있음 / .tool_calls 채워짐
#! `최종 답변용` → .content 채워짐 / .tool_calls 는 []
#! 중간 AIMessage 의 .content 를 찍으면 빈 문자열이 나온다.



#== 에이전트 실행 후 쌓이는 것

# --8<-- [start:list]
result = {"messages":
              [
                HumanMessage,   # [0] 내 질문
                AIMessage,      # [1] "툴 쓸게"  (content 비어있음)
                ToolMessage,    # [2] 툴 실행 결과
                AIMessage,      # [3] 최종 답변  ← [-1]
              ]
           }


result["messages"] = [
    HumanMessage,   # [0] 내 질문
    AIMessage,      # [1] "툴 쓸게"  (content 비어있음)
    ToolMessage,    # [2] 툴 실행 결과
    AIMessage,      # [3] 최종 답변  ← [-1]
]
# --8<-- [end:list]


#== 딕셔너리로 본 실제 모습

# --8<-- [start:dict]
# HumanMessage 객체
 {"content": "서울 날씨 어때?", "type": "human"}

# AIMessage 객체
 {"content": "",                              # 비어있음
  "type": "ai",
  "tool_calls": [{"name": "get_weather",      # 어떤 툴을
                  "args": {"city": "서울"},    # 어떤 값으로
                  "id": "call_abc123"}]}      # tool 고유 id

# ToolMessage 객체
 {"content": "서울은 맑음, 25도",              # 함수의 return 값
  "type": "tool",
  "tool_call_id": "call_abc123",              # tool 고유 id
  "status": "success"}

# AIMessage 객체
 {"content": "서울은 맑고 25도입니다.",
  "type": "ai",
  "tool_calls": []}                           # tool_calls가 비었으니 끝

# 위 딕셔너리는 보기 좋게 변환한 모습이고, 실제 리스트 안에는 객체가 들어있다.
#(1)> result["messages"][-1].content      (o)
#(1)> result["messages"][-1].model_dump() 로 객체 → dict 변환
# --8<-- [end:dict]

#! type 이 신분증. human → ai → tool → ai 순서로 흐른다.
#! call_abc123 이 [1]과 [2]를 잇는다. 툴을 여러 개 동시에 호출하면
#! 결과가 뒤죽박죽 오는데 이 번호(call_abc123)로 짝을 맞춘다. 


#== messages 에 넣는 5가지 방법 — 전부 같다

# --8<-- [start:input]
 {"messages": "안녕"}
 {"messages": ["안녕"]}
 {"messages": [("user", "안녕")]}
 {"messages": [{"role": "user", "content": "안녕"}]}
 {"messages": [HumanMessage("안녕")]}
# 내부에서 convert_to_messages() 가 돌아 전부 HumanMessage 로 변환된다
#(1)> 문서마다 표기가 달랐던 게 아니라, 같은 곳으로 수렴하는 여러 표기법이었다
#(1)> {"role": ...} 은 OpenAI API 형식. 코드를 옮길 때 안 고쳐도 되게 지원한다
# --8<-- [end:input]

#! `role 이 어떤 클래스가 되는지`
#! role: system·developer → SystemMessage
#! role: user·human → HumanMessage
#! role: assistant·ai → AIMessage
#! role: tool → ToolMessage


#== 함정 — 넣을 땐 role, 나올 땐 type

#! 넣을 때 "role", 나올 때 "type"
#! `Human`: 넣을 때 "user" → 나올 때 "human"
#! `AI`:   넣을 때 "assistant" → 나올 때 "ai"


# --8<-- [start:history]
history = result["messages"]

# 객체와 dict 를 한 리스트에 섞어도 다 변환된다
agent.invoke({"messages": history + [{"role": "user", "content": "또 질문"}]})
# --8<-- [end:history]


#== 디버깅

# --8<-- [start:debug]
# 객체가 어떤 순서로 쌓였는지 한눈에 보기

for m in result["messages"]:
    m.pretty_print()
# --8<-- [end:debug]


