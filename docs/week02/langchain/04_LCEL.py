"""
title: LCEL 
tags: [langchain]
"""

#== LCEL 개념
#> Runnable들을 파이프 `|` 연산자로 연결할 수 있는 문법

# --8<-- [start:flow]
Runnable  (부모 — invoke/batch/stream 규격을 정의)
   ├── RunnableSequence      ← prompt | llm | parser 의 정체
   ├── RunnableParallel      ← {} 가 변환되는 것
   ├── RunnableLambda        ← 함수가 변환되는 것
   ├── RunnablePassthrough   ← 조건 분기
   ├── ChatOpenAI
   ├── ChatPromptTemplate
   └── StrOutputParser
# --8<-- [start:flow]

#! Runnable 이면 아래가 공짜로 따라옴.
#! .invoke()  입력 1개 → 출력 1개
#! .batch()   입력 여러 개를 병렬로
#! .stream()  결과를 조금씩 흘려보내기
#! .ainvoke() .abatch()  async 버전


#== 타입이 어떻게 바뀌는가
#> dict → PromptValue → AIMessage → str. 부품을 하나 지날 때마다 타입이 바뀜.

# --8<-- [start:flow]
llm    = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = StrOutputParser()

template = ChatPromptTemplate.from_messages([
    ("system", "요약 전문가입니다."),
    ("human", "다음을 {length}줄로 요약:\n{text}"),
])

news = "삼성전자가 차세대 3D 메모리 zHBM 을 공개했다. ..."

# 부품마다 invoke 가 따로 있음. 체인은 이걸 순서대로 이어준 것뿐임
input_dict = {"length": "3", "text": news}
messages   = template.invoke(input_dict)  
#(1)>  messages=[SystemMessage(...), HumanMessage(...)]
ai_msg     = llm.invoke(messages)          
text_out   = parser.invoke(ai_msg)        

# <class 'dict'> → <class 'langchain_core.prompt_values.ChatPromptValue'>  → <class 'langchain_core.messages.ai.AIMessage'> → <class 'str'>
print(type(input_dict), "→", type(messages), "→", type(ai_msg), "→", type(text_out))

# --8<-- [end:flow]

#! 체인의 최종 결과 타입 = 맨 마지막 부품의 출력 타입.
#! parser 로 끝나면 str, llm 으로 끝나면 AIMessage, structured_llm 이면 객체.

#== ChatPromptValue — 리스트가 아니라 리스트를 담은 객체
 
# --8<-- [start:promptvalue]
result = template.invoke({"length": "2", "text": "안녕하세요"})
 
print(type(result))          # ChatPromptValue -> 객체
print(result.to_messages())  # [SystemMessage(...), HumanMessage(...)]
print(result.to_string())    # 'System: ...\nHuman: ...'

# --8<-- [end:promptvalue]
 
#! 프롬프트가 실제로 어떻게 나가는지 볼 때 to_string() 이 제일 편함.
#! print(template.invoke({"length": "2", "text": "테스트"}).to_string())


#== .from_messages vs .format_messages
#> 이름이 비슷한데 단계가 다름. 하나는 만들기, 하나는 채우기.

# --8<-- [start:methods]
# 만들 때 — 재료는 ("역할", "템플릿 문자열") 
template = ChatPromptTemplate.from_messages([
    ("system", "요약 전문가입니다."),
    ("human", "다음을 {length}줄로 요약:\n{text}"),
])

# 채울 때 — 결과는 메시지 객체 리스트
#(1)> [SystemMessage(content='요약 전문가입니다.'),HumanMessage(content='다음을 3줄로 요약:\n삼성전자가 차세대 3D 메모리...')]
filled = template.format_messages(length="3", text=news)
print(filled)

# --8<-- [end:methods]

#! 들어갈 땐 튜플, 나올 땐 객체. 이 대비로 기억하면 될 듯.
#! from_messages([("system", ...), ("human", ...)])  ← 튜플로 만들고
#! format_messages(length="3", text=news)  → [SystemMessage(...), HumanMessage(...)]  ← 객체로 나옴


#== 파이프로 잇기

# --8<-- [start:chain]
chain = template | llm | parser

# <class 'langchain_core.runnables.base.RunnableSequence'>
#(1)> | 로 묶으면 RunnableSequence 라는 객체가 만들어짐 (LangSmith 에 RunnableSequence 로 찍힘)
#(1)> 부품 목록을 순서대로 들고 있다가 invoke 하면 차례로 실행해 줌
print(type(chain))

# [ChatPromptTemplate(...), ChatOpenAI(...), StrOutputParser()]
print(chain.steps)
# --8<-- [end:chain]

#! Runnable = invoke·stream·batch 를 가진 것들의 공통 규격.
#! template 도 llm 도 parser 도 전부 Runnable 이라서 | 로 이어붙일 수 있는 것임.
#! 이어붙인 결과(RunnableSequence)도 또 Runnable 이라 체인끼리도 이어붙일 수 있음.

#== 중간에서 값 확인하기
#> 체인이 길어지면 어디서 모양이 틀어졌는지 안 보임. 확인용 함수를 끼워 넣으면 됨.
 
# --8<-- [start:debug]
def 확인(x):
    print(f"[타입] {type(x)}\n[값] {x}")
    return x
#(1:3)> 받은 걸 찍고 그대로 돌려주는 함수. return 을 빼먹으면 뒤로 None 이 흘러감
 
chain = (
    {"question": RunnablePassthrough()}
    | RunnableLambda(확인)      # dict 가 만들어진 직후
    | prompt_q
    | RunnableLambda(확인)      # prompt 통과 후
    | llm | parser
)
# --8<-- [end:debug]


#== invoke vs stream vs batch
#> 셋 다 같은 체인에 있음. 입력을 몇 개 넣고 결과를 언제 받느냐가 다름.

# --8<-- [start:three]
# invoke —  입력 1건, 다 끝나면 한 번에
result = chain.invoke({"length": "3", "text": news})
print(result)

# stream — 입력 1건, 조각으로 즉시
for chunk in chain.stream({"length": "3", "text": news}):
    print(chunk, end='', flush=True)

# batch — 입력 여러 건, 동시에
#(2)> 안에서 스레드를 여러 개 띄워 동시에 요청함 (for 문 돌리는 것보다 훨씬 빠름)
#(2)> 반환값은 결과 str 들의 리스트

texts = [
    "회의 내용 A: AI 프로젝트 일정 조율 논의",
    "회의 내용 B: 예산 확정 및 팀 구성 완료",
    "회의 내용 C: 다음 달 데모 발표 준비",
]

results = chain.batch([
    {"length": "2", "text": texts[0]},
    {"length": "3", "text": texts[1]},
    {"length": "1", "text": texts[2]},
])

# --8<-- [end:three]


#== batch 결과 순서
#> LangSmith 에는 B → C → A 로 찍혔는데 results 리스트는 A → B → C 순임.

#! langSmith 순서는 '먼저 끝난 순서' 임. 동시에 던져서 빨리 끝난 게 먼저 기록됨.
#! 근데 results 리스트는 넣은 순서대로 돌려줌. 랭체인이 안에서 다시 정렬해 줌.
#! → 실행 순서는 뒤죽박죽이어도 결과 순서는 걱정 안 해도 됨. results[0] 은 항상 첫 입력의 답.


#== max_concurrency

# --8<-- [start:concurrency]

# 한 번에 동시에 처리할 최대 개수 (max_concurrency) 설정 
#(1)> 'max_concurrency': 한 번에 "동시에" 처리할 최대 개수 (창구 개수)
#(1)>   → batch는 입력 전부를 한꺼번에 던지는 게 아니라, 이 개수만큼만 동시에 실행
#(1)>   → 하나가 끝나면 빈 자리에 다음 입력이 들어감
#(1)>   → 입력 12개 / max_concurrency=5 면
#(1)>      시작:      1,2,3,4,5 실행 중
#(1)>      3번 끝나면: 1,2,4,5,6 실행 중   ← 빈 자리에 6번이 들어감
#(1)>  'max_concurrency 올리면 답변을 빠르게 받을 수 있지만 , 짧은 시간에 요청이 몰려 Rate Limit에 걸리기 쉬움 ' 
#(1)>  → Rate Limit = API 제공사가 건 사용량 상한 (1분당 요청 수 RPM / 토큰 수 TPM)
#(1)>  → 초과 시 429 Too Many Requests 에러 → 이 값을 낮추면 됨
results = chain.batch(
    [{"length": "2", "text": texts[0]},
     {"length": "3", "text": texts[1]}],
    config={"max_concurrency": 5},
)
# --8<-- [end:concurrency]
#! max_concurrency 지정하지 않으면 파이썬 스레드풀 기본값을 따라가서
#! 오히려 5보다 커질 수 있음. 대량 처리 시엔 꼭 명시할 것
#! 입력이 2개뿐이면 5든 100이든 결과 동일. 수십~수백 개일 때부터 의미가 생김.
#! 긴 문서를 여러 개 던질 땐 요청 수(RPM)보다 토큰 한도(TPM)에 먼저 걸리는 경우가 많음.
#! RunnableParallel 이랑 같이 쓰면 가지 수만큼 곱해서 요청이 나감 → 429 가 빨리 뜸.


#== batch 랑 stream 같이 되나
#> 안 됨. batch 는 다 끝날 때까지 기다렸다가 리스트로 한 번에 줌.

#! 왜 안 되는지 생각해보면 당연함. 여러 건이 동시에 흘러나오면 어느 건의 조각인지 알 수 없음.
#! stream_mode 같은 게 있는 것도 아니고, 그냥 batch 는 스트리밍을 지원 안 함.

# --8<-- [start:as_completed]
# batch_as_completed → 완성된 건부터 결과값 하나씩 받고 싶으면 이걸 씀
#(1)> (몇 번째 입력이었는지, 결과) 튜플로 나옴 → 순서가 섞이니 idx 로 짝을 맞춰야 함
for idx, output in chain.batch_as_completed([
    {"length": "2", "text": texts[0]},
    {"length": "3", "text": texts[1]},
]):
    print(idx, output)
# --8<-- [end:as_completed]


