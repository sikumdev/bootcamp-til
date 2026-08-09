"""
title: 대화 기억 
tags: [langchain]
"""


#== v1 — 손으로 관리하기
#> 모델에 메모리가 없으니 리스트에 쌓아뒀다가 통째로 다시 보내는 것.

# --8<-- [start:manual]
# 사용자를 구분하려고 dict 로 감쌈. 세션마다 리스트가 따로 있음
#(1)> 질문을 append → llm 호출 → 답도 append. 이 append 두 번이 전부임
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables import RunnableWithMessageHistory


conversation_history = {}   # session_id → list[Message]


def chat_with_history(session_id: str, user_msg: str) -> str:
    if session_id not in conversation_history:
        conversation_history[session_id] = []

    conversation_history[session_id].append(HumanMessage(content=user_msg))
    response = llm.invoke(conversation_history[session_id])
    conversation_history[session_id].append(response)
    return response.content
# --8<-- [end:manual]

#! 이 함수는 동기(sync)임. FastAPI 엔드포인트에서는 ainvoke() 로 바꿔야 함.


#== MessagesPlaceholder — 메시지 리스트가 들어갈 자리
#> {변수} 는 문자열 하나를 받는 자리, MessagesPlaceholder 는 메시지 리스트를 통째로 받는 자리.

# --8<-- [start:placeholder]
prompt_with_history = ChatPromptTemplate.from_messages([
    ("system", "너는 한국의 예의바른 교사야. 짧고 구조적으로 대답해줘."),
    MessagesPlaceholder("chat_history"),
    # 튜플이 아니라 객체를 끼워 넣음. 
    #(1)> 리스트를 넣으면 그 자리에 메시지들이 '풀어헤쳐져서' 들어감
    #(1)> 빈 리스트면 자리 자체가 사라짐 (빈 메시지가 생기는 게 아님)
    ("human", "{input}"),
])

chain = prompt_with_history | llm | StrOutputParser()
# --8<-- [end:placeholder]
#! {chat_history} 로 쓰면 안 되는 이유 → 그건 문자열 자리라 리스트를 넣으면
#! 통째로 문자열이 돼버림. 메시지 개수가 미리 안 정해지니까 전용 자리가 필요한 것.

#== MessagesPlaceholder 객체 구조
 
# --8<-- [start:ph_object]

chain = prompt_with_history | llm | StrOutputParser()

ph = MessagesPlaceholder("chat_history")
print(ph)
# MessagesPlaceholder(variable_name='chat_history', optional=False)
#  variable_name → 입력 dict 에서 어느 키를 꺼내 쓸지. 위치 인자로 준 게 여기 들어감
#(1)> optional → 기본 False. 그 키가 없으면 에러. True 면 없어도 자리를 비움
#(1)> n_messages → 최근 몇 개만 넣을지. 안 주면 전부
 
print(prompt_with_history.messages)
# [SystemMessagePromptTemplate(prompt=PromptTemplate(template='너는 한국의...')),
#  MessagesPlaceholder(variable_name='chat_history'),
#  HumanMessagePromptTemplate(prompt=PromptTemplate(template='{input}'))]
#(2)> 튜플로 쓴 건 ...PromptTemplate 으로 변환됐는데 MessagesPlaceholder는 그대로 있음
#(2)> 이미 그 계열의 객체라서 변환할 게 없음 → 그래서 튜플이 아니라 객체로 넣는 것
 
print(prompt_with_history.input_variables)
# ['chat_history', 'input']
#(3)> 빈칸 목록에 chat_history 도 잡힘 → invoke 때 이 키를 채워야 함
 
# 실제로 펼쳐지는지 확인
prompt_with_history.format_messages(
    chat_history=[HumanMessage("내 이름은 민재야."), AIMessage("반가워요, 민재님!")],
    input="내 이름이 뭐야?",
)
# [SystemMessage(content='너는 한국의 예의바른 교사야...'),
#  HumanMessage(content='내 이름은 민재야.'),      ← 여기 2개가
#  AIMessage(content='반가워요, 민재님!'),          ← 펼쳐짐
#  HumanMessage(content='내 이름이 뭐야?')]
#(4:4)> 템플릿은 3줄인데 결과는 4개. 자리 하나가 2개로 늘어난 것
# --8<-- [end:ph_object]

#! optional=True 는 첫 대화에 쓸모 있음.
#! RunnableWithMessageHistory 는 알아서 빈 리스트를 채워주지만,
#! chain.invoke 를 직접 부를 땐 키를 빠뜨리면 터짐.
#! 메시지 객체 말고 [("user", "안녕")] 이나 [{"role": "user", "content": "안녕"}] 도 됨.
#! 안에서 convert_to_messages 가 돌아서 객체로 바꿔 줌 



#== RunnableWithMessageHistory — 자동으로 넣고 빼주기
#> [히스토리 꺼내서 입력에 끼우기] → 원래 체인 → [이번 대화를 히스토리에 넣기]

# --8<-- [start:rwmh]
store = {}   # 실무에서는 dict 대신 DB (Redis, PostgreSQL)
 
def get_history(session_id: str):
    return store.setdefault(session_id, InMemoryChatMessageHistory())
    #(1)> setdefault → 키가 없으면 만들어 넣고 반환, 있으면 기존 걸 반환
 
def clear_history(session_id: str):
    store.setdefault(session_id, InMemoryChatMessageHistory()).clear()
 
chat = RunnableWithMessageHistory(
    chain,
    get_history,
    input_messages_key="input",  # ("human", "{input}") 의 그 이름
    #(2)> get_history 는 '함수 자체' 를 넘김. 괄호 붙여서 부르는 게 아님         
    history_messages_key="chat_history",  # MessagesPlaceholder 의 그 이름
)

 
cfg = {"configurable": {"session_id": "user1"}}
 
print(chat.invoke({"input": "내 이름은 민재야."}, cfg))
# 반가워요, 민재님!
print(chat.invoke({"input": "내 이름이 뭐야?"}, cfg))
# 민재님이라고 하셨습니다!

clear_history("user1")
print(chat.invoke({"input": "내 이름이 뭐야?"}, cfg))
# 이름을 알려주시지 않으셨습니다
# --8<-- [end:rwmh]


#== RunnableWithMessageHistory 인자
#> 체인 앞뒤에 히스토리 로드·저장을 붙여주는 래퍼. 체인 자체는 안 건드림.
 
#! runnable              (필수·위치) 감쌀 체인
#! get_session_history   (필수·위치) session_id → 히스토리 객체를 돌려주는 함수
#! input_messages_key    입력 dict 에서 어떤 키가 사용자 메시지인지
#! history_messages_key  히스토리를 어떤 키로 넣을지 = MessagesPlaceholder 이름
#! output_messages_key   출력이 dict 일 때 어느 키가 답변인지
#! history_factory_config  session_id 말고 다른 키를 쓸 때
 
#! 뒤의 세 개는 상황에 따라 필요함.
#! input_messages_key  → 입력이 dict 면 필요. 여러 키 중 뭘 저장할지 알아야 하니까
#! history_messages_key → 안 주면 동작이 달라짐. 주면 그 키에 리스트로 넣고,
#!                        안 주면 히스토리를 입력 메시지 앞에 그냥 이어붙임
#!                        (ChatPromptTemplate 없이 llm 만 감쌀 때가 후자)
#! output_messages_key → StrOutputParser 로 끝나면 필요 없음
 

#! 반환값은 BaseChatMessageHistory 를 상속한 객체여야 함.
#! InMemoryChatMessageHistory 가 그중 하나. Redis·PostgreSQL 버전으로 바꿔도
#! 나머지 코드는 그대로 → 저장소만 갈아끼우면 됨.

#== 이것도 결국 Runnable
 
# --8<-- [start:rwmh_object]

chat = RunnableWithMessageHistory(
    chain,
    get_history,
    #(3)> get_history 는 '함수 자체' 를 넘김. 괄호 붙여서 부르는 게 아님
    input_messages_key="input",           
    history_messages_key="chat_history",  
)

print(type(chat))
# <class 'langchain_core.runnables.history.RunnableWithMessageHistory'>
 
print(type(chat).__mro__[:4])
# (RunnableWithMessageHistory, RunnableBindingBase, RunnableSerializable, Runnable)
#(1:3)> __mro__ = 이 클래스가 뭘 상속받았는지 순서대로
#(1)> Runnable 이니까 invoke·stream·batch 다 되고 파이프로 더 이을 수도 있음
 
print(chat.bound)
# RunnableLambda(_enter_history) | chain | ...
#(2)> 안에 조립된 실제 실행 순서 (체인을 하나 더 만든 것뿐임)
# --8<-- [end:rwmh_object]
 
#! cfg 를 안 주면 에러남. session_id 를 못 찾으면 히스토리를 못 꺼내니까.
#! chat.invoke({"input": "안녕"})        (x)
#! chat.invoke({"input": "안녕"}, cfg)   (o)
 
#! 키 이름을 session_id 말고 다른 걸로 쓰려면 history_factory_config 를 씀.
#! 한 사용자가 대화방을 여러 개 갖는 구조면 user_id + conversation_id 로 나눔.
 
 
#== 1회차 실행 흐름
#> chat.invoke({"input": "내 이름은 민재야."}, cfg) 를 한 줄씩 따라간 것.
#> ①②⑥ 은 래퍼가 하는 일이고 ③④⑤ 만 실제 체인임.
 
# --8<-- [start:flow1_load]
# ① 히스토리 꺼내기 — _merge_configs (아직 체인 실행 전)
 
# 입력: cfg = {"configurable": {"session_id": "user1"}}
session_id = cfg["configurable"]["session_id"]     # → "user1"
hist = get_history("user1")
 
# get_history 내부에서 일어나는 일
#   store.setdefault("user1", InMemoryChatMessageHistory())
#   → "user1" 키가 없음 → 새 객체를 만들어 넣고 그걸 반환
 
# 실행 후 상태
store = {"user1": InMemoryChatMessageHistory(messages=[])}   # 텅 빔
hist  = store["user1"]  
# hist = InMemoryChatMessageHistory(messages=[])                                     # 같은 객체 (사본 아님)
#(1)> 여기서 hist 가 store 안의 객체와 '같은 것'!!
# --8<-- [end:flow1_load]
 
# --8<-- [start:flow1_key]
# ② 입력 dict 에 키 추가 — _enter_history (아직 체인 실행 전)
 
# 이전
{"input": "내 이름은 민재야."}                      # 키 1개

hist.messages.copy()                               # → []  (비어 있음)
 
# 이후 — history_messages_key 이름으로 키를 하나 만들어 넣음
{"input": "내 이름은 민재야.",
 "chat_history": []}                               # 키 2개가 됨
# 내가 넘긴 건 input 하나뿐인데 래퍼가 chat_history 를 끼워 넣어 줌
#(1)> 키 이름은 history_messages_key="chat_history" 로 정해둔 그것
#(1)> 값은 hist.messages 를 복사한 리스트. 지금은 첫 대화라 []
#(1)> 이 dict 가 그대로 체인 입력이 됨
# --8<-- [end:flow1_key]
 
# --8<-- [start:flow1_chain]
# ③ ChatPromptTemplate — 여기서 체인 실행 시작
 
# 템플릿 3줄                             받은 값                  결과
# ("system", "너는 ... 교사야")       →  (고정)              →  SystemMessage("너는 ... 교사야")
# MessagesPlaceholder("chat_history") →  []                 →  (아무것도 없음)  자리가 사라짐
# ("human", "{input}")                →  "내 이름은 민재야."  →  HumanMessage("내 이름은 민재야.")
 
# 최종 결과: 메시지 2개
[SystemMessage("너는 한국의 예의바른 교사야. 짧고 구조적으로 대답해줘."),
 HumanMessage("내 이름은 민재야.")]
 
# ④ ChatOpenAI — API 전송
{"model": "gpt-4o-mini", "temperature": 0, "messages": [
    {"role": "system", "content": "너는 한국의 예의바른 교사야. 짧고 구조적으로 대답해줘."},
    {"role": "user",   "content": "내 이름은 민재야."}
]}
# 응답
AIMessage(content="반가워요, 민재님!", response_metadata={...}, usage_metadata={...})

 
# ⑤ StrOutputParser
AIMessage(content="반가워요, 민재님!")  →  "반가워요, 민재님!"   # str
# --8<-- [end:flow1_chain]
 
# --8<-- [start:flow1_save]
# ⑥ 히스토리에 저장 — _exit_history (체인은 이미 끝남)
 
hist.add_messages([
    HumanMessage("내 이름은 민재야."),      # input_messages_key="input" 로 뽑음
    AIMessage("반가워요, 민재님!"),         # 출력 문자열을 AIMessage 로 되돌림
])
 
# 실행 후
store["user1"].messages
# [HumanMessage("내 이름은 민재야."), AIMessage("반가워요, 민재님!")]
# 파서가 str 로 만든 걸 다시 AIMessage 로 감싸는 게 포인트
#(1)> 히스토리에는 메시지 객체로 들어가야 다음 턴에 그대로 쓸 수 있으니까
#(1)> input_messages_key 를 지정한 이유가 여기 있음. 여러 키 중 뭘 저장할지 알아야 함
# --8<-- [end:flow1_save]
 
#! hist 는 store["user1"] 과 '같은 객체' 임. 사본이 아님.
#! 그래서 hist 에 add_messages 하면 store 가 알아서 같이 바뀜.
#! 다시 store 에 넣어주는 코드가 없는 이유가 이거였음.
 
 
#== 2회차 — placeholder 가 풀리는 곳
 
# --8<-- [start:flow2]
# chat.invoke({"input": "내 이름이 뭐야?"}, cfg)
 
# ① 히스토리 꺼내기 — 이번엔 키가 이미 있음
hist = get_history("user1")
#   store.setdefault("user1", ...) → 키가 있으니 새로 안 만들고 기존 것 반환

# hist = InMemoryChatMessageHistory(messages=[HumanMessage("내 이름은 민재야."), AIMessage("반가워요, 민재님!")]) 
hist.messages
# [HumanMessage("내 이름은 민재야."), AIMessage("반가워요, 민재님!")]
 
# ② 입력 dict 에 키 추가 — 이번엔 값이 안 비어있음
{"input": "내 이름이 뭐야?",
 "chat_history": [HumanMessage("내 이름은 민재야."),
                  AIMessage("반가워요, 민재님!")]}     # 리스트 2개짜리
 
# ③ 템플릿 3줄 → 메시지 4개
#   ("system", ...)           → SystemMessage("너는 교사야")
#   MessagesPlaceholder(...)  → HumanMessage("내 이름은 민재야.")   ┐ 리스트가
#                               AIMessage("반가워요, 민재님!")      ┘ 풀어헤쳐짐 ★
#   ("human", "{input}")      → HumanMessage("내 이름이 뭐야?")
 
# ④ GPT 는 이 4개만 보고 답함. 2번째에 "민재" 가 있어서 아는 것
#    → AIMessage("민재님이라고 하셨습니다!")
 
# ⑥ 저장 후
store["user1"].messages   # 4개가 됨

# --8<-- [end:flow2]
 
#! 모델이 기억하는 게 아니라 매번 전부 다시 보내는 것.
#! llm은 stateless 라서 프롬프트에 다 넣어야 한다던 게 이렇게 구현됨.
 
 
#== store 구조
 
# --8<-- [start:store]
store
# {
#   "user1": InMemoryChatMessageHistory(messages=[
#       HumanMessage(content="내 이름은 민재야."),
#       AIMessage(content="반가워요, 민재님!"),
#       HumanMessage(content="내 이름이 뭐야?"),
#       AIMessage(content="민재님이라고 하셨습니다!"),
#   ]),
#   "user2": InMemoryChatMessageHistory(messages=[...]),
# }
# 겉은 dict(session_id → 객체), 안은 InMemoryChatMessageHistory 객체
#(1)> 메시지는 그 객체의 .messages 리스트에 들어있음
#(1)> InMemory 라서 프로그램을 끄면 다 날아감 → 실서비스면 Redis·DB
# --8<-- [end:store]
 
#! 대화가 길어지면 매 호출마다 전체를 다시 보내니까 입력 토큰이 계속 늘어남.
#! context window 한도에 걸리기 전에 오래된 걸 자르거나 요약해야 함.
 