"""
title: Runnable 4종 — Parallel · Passthrough · Lambda · Sequence
tags: [langchain]
"""

#== RunnableParallel — 같은 입력을 여러 체인에 동시에
#> RunnableParallel은 입력 하나를 그대로 복사해서 각 가지에 나눠주고, 결과를 dict로 모으는 것
#(1)>
#(1)>                  ┌─→ summary_chain  ─→ "요약 결과"
#(1)>{"text": "..."} ──┤                              → {"summary": ..., "category": ...}
#(1)>                  └─→ classify_chain ─→ "기술"


# --8<-- [start:parallel]
llm    = ChatOpenAI(model="gpt-4o-mini", temperature=0)
parser = StrOutputParser()


prompt_summary = ChatPromptTemplate.from_messages([
    ("system", "요약 전문가입니다."),
    ("human", "다음 텍스트를 2줄로 요약:\n{text}"),
])
prompt_classify = ChatPromptTemplate.from_messages([
    ("system", "분류 전문가입니다."),
    ("human", "다음 텍스트의 주제를 [업무/개인/기술/기타] 중 하나로 분류:\n{text}"),
])

summary_chain  = prompt_summary  | llm | parser
classify_chain = prompt_classify | llm | parser

# 키 이름은 내가 정하는 것. 결과 dict 의 키가 그대로 이 이름이 됨
parallel = RunnableParallel(
    summary  = summary_chain,
    category = classify_chain,
)

# {'summary': 'AI 프로젝트 킥오프 회의에서 팀 구성과 일정을 결정했습니다. 프로젝트 진행을 위한 첫 단계를 확립했습니다.', 'category': '주제: 업무'}
result = parallel.invoke({"text": "AI 프로젝트 킥오프 회의에서 팀 구성과 일정을 확정했습니다."})

# 입력은 하나인데 두 체인이 각자 그 입력을 받아 감
print(result["summary"])
print(result["category"])

# --8<-- [end:parallel]

#! LLM 은 2번 호출되는 게 맞음. 요약용 1번, 분류용 1번.
#! 동시에 던지는 거라 기다리는 시간은 둘 중 느린 쪽 기준 (순차로 하면 둘을 더한 시간).
#! 대신 토큰이랑 돈은 2배로 나감. 빨라지는 거지 싸지는 게 아님.

#== batch랑 RunnableParallel
#! batch            = 입력 여러 개 → 체인 하나 (같은 일을 여러 데이터에)
#! RunnableParallel = 입력 하나 → 체인 여러 개 (다른 일을 같은 데이터에)
#! parallel.batch([...]) 도 됨 → 입력 N개 × 가지 M개 = LLM 호출 N×M 번

#== RunnablePassthrough() - 값을 입력 받으면 값을 그대로 출력
# --8<-- [start]
RunnablePassthrough().invoke("파이썬이 뭐야?")
#  '파이썬이 뭐야?'   (똑같음)

# 쓰는 이유 — prompt 는 dict 만 받는데 체인 쓸 땐 문자열만 던지고 싶어서
step = RunnableParallel(question=RunnablePassthrough())
step.invoke("파이썬이 뭐야?")
# {'question': '파이썬이 뭐야?'}     ← 문자열 넣었더니 dict 가 나옴
#(2)> 결국 [문자열 → dict] 변환 어댑터임. 필수가 아니라 편의 장치
#(2)> Parallel 의 역할(결과를 dict 로 모음)은 그대로!
# --8<-- [start]

#== RunnableLambda — 파이썬 함수를 체인에 끼우기

# --8<-- [start:lambda]
preprocess = RunnableLambda(lambda x: x.strip().upper())
greeting   = RunnableLambda(lambda name: f"안녕하세요, {name}님!")

#  LLM 없이도 체인이 됨. 앞 결과가 뒤 함수의 입력으로 들어감
chain_rl = preprocess | greeting
print(chain_rl.invoke("  alice  "))   # 안녕하세요, ALICE님!
# --8<-- [end:lambda]


#== RunnableSequence — `|` 랑 같은 것

# --8<-- [start:sequence]
double    = RunnableLambda(lambda x: x + x)
say_hello = RunnableLambda(lambda name: f"Hello, {name}!")

seq = RunnableSequence(first=double, last=say_hello)
print(seq.invoke("Jintae"))                    # Hello, JintaeJintae!
print((double | say_hello).invoke("Jintae"))   # 같은 결과
# --8<-- [end:sequence]


#== 핵심 — 파이프(|)에 넣으면 자동으로 Runnable 로 바뀌는 것들
#>  LCEL 부품은 전부 Runnable 이어야 연결됨.
#>  근데 dict·함수는 Runnable 이 아님. → 랭체인이 | 를 만나는 순간 알아서 감싸 줌.

# --8<-- [start:coerce]
prompt_q = ChatPromptTemplate.from_template("이 질문에 간단히 답해줘: {question}")

# 1) dict → RunnableParallel 로 자동 변환
chain_rpt = {"question": RunnablePassthrough()} | prompt_q | llm | parser
#(1)> chain_rpt.invoke() 시 내부적으로 RunnablePassthrough().invoke()가 가장 먼저 실행된다고 생각 하면 편함
#(1)> 즉, 코드 상으로 볼때 RunnablePassthrough()에 invoke('문자열')에 있는 문자열이 대체 된다고 보면 댐
#(1)> 파이썬 `dict{}` 와 `|(파이프)` 가 만나는 순간 랭체인이 RunnableParallel 로 바꿔 줌. 아래 둘은 완전히 같음
#(1)> RunnableParallel(question=RunnablePassthrough()) | prompt_q
#(1)> {"question": RunnablePassthrough()} | prompt_q
chain_rpt.invoke('파이썬이 뭐야?')

# 2) 함수·callable → RunnableLambda
prompt_ig = ChatPromptTemplate.from_template("{고객번호} 고객님, {창구번호}번 창구로 오십시오.")

# () 로 묵은건 여러줄 잇기 위해 썼고 itemgetter(키)는 딕셔너리의 키에 매칭되는 값을 가져옴
#(2)> 입력 {"customer_number": 132, "counter_number": 4}
#(2)> 출력 {"고객번호": 132, "창구번호": 4}   ← prompt 빈칸 이름에 맞춤
chain_ig = (
    {
        "고객번호": itemgetter("customer_number"),
        "창구번호": itemgetter("counter_number"),
    }
    | prompt_ig | llm | parser
)

chain_ig.invoke({"customer_number": "132", "counter_number": "4"})

 
# 일꾼을 여러 개 놓고 확인해보기
step = RunnableParallel(
    원본   = RunnablePassthrough(),
    대문자 = RunnableLambda(str.upper),
    글자수 = RunnableLambda(len),
)
print(step.invoke("hello"))
# {'원본': 'hello', '대문자': 'HELLO', '글자수': 5}
#(3)> 입력 하나가 세 일꾼에게 각각 복사돼서 들어가고, 각자 처리한 결과가 자기 키에 담김
# --8<-- [end:passthrough]
#! chain_rpt.invoke("파이썬이 뭐야?") 시 순서
#!
#! ① RunnableParallel(question=RunnablePassthrough()) .invoke("파이썬이 뭐야?") 
#!  -> {"question": "파이썬이 뭐야?"}   (dict)
#!
#! ② prompt_q.invoke({"question": ...}) -> ChatPromptValue 객체
#!    (안에 [HumanMessage(...)] 를 담고 있음. .to_messages() 로 꺼냄)
#!
#! ③ llm.invoke(ChatPromptValue)        -> AIMessage 객체
#!    (llm 이 알아서 to_messages() 해서 받음)
#!
#! ④ parser.invoke(AIMessage)           -> AIMessage.content  (str)

#== RunnableBranch — 조건에 따라 다른 체인으로
#> 체인 안에서 하는 if / elif / else. invoke() 한 번으로 분기까지 타고 끝까지 흘러감.
 
# --8<-- [start:branch_form]
# (조건, 체인) 튜플을 순서대로 나열. 위에서부터 검사해서 처음 True 인 것만 실행
#(1)> 나머지 조건은 아예 검사 안 함 (if/elif 와 동일)
#(1)> 마지막은 튜플이 아니라 체인 하나만. 다 False 면 여기로 감
branch = RunnableBranch(
    (조건함수1, 체인1),      # if
    (조건함수2, 체인2),      # elif
    기본체인,               # else ← 조건 없이. 필수. 빠지면 에러
)
# --8<-- [end:branch_form]

# --8<-- [start:branch]
urgent_prompt = ChatPromptTemplate.from_template(
    "다음 긴급 회의 결과로 팀 슬랙에 올릴 알림 문구를 작성하세요.\n"
    "3줄 이내, 담당자와 기한을 명시할 것.\n\n요약: {summary}\n액션: {action_items}"
)
normal_prompt = ChatPromptTemplate.from_template(
    "다음 회의의 할 일을 담당자별로 정리해주세요.\n\n요약: {summary}\n액션: {action_items}"
)
low_prompt = ChatPromptTemplate.from_template(
    "다음 회의를 한 문장으로 정리해주세요.\n\n요약: {summary}"
)

# 조건 함수는 '앞 단계의 출력' 을 x 로 받음
#(1)> x["urgency"] 로 접근하려면 앞에서 dict 로 바꿔줘야 함. 객체면 x.urgency
branch = RunnableBranch(
    (lambda x: x["urgency"] == "높음", urgent_prompt | llm | parser),
    (lambda x: x["urgency"] == "보통", normal_prompt | llm | parser),
    low_prompt | llm | parser,
)

full_chain = (
    {"meeting_text": RunnablePassthrough()}
    | chat_prompt
    | structured_llm
    | RunnableLambda(lambda note: note.model_dump())
    | branch
)
#(2:7)> structured_llm 출력은 dict 가 아니라 MeetingNote 객체라서 변환이 필요함
#(2)> 조건 함수도 dict 를 원하고, 뒤의 프롬프트도 {summary} 빈칸을 채우려면 dict 여야 함
#(2)> .model_dump() 는 객체를 딕셔너리로 변환함
 
full_chain.invoke('문자열~~')
# --8<-- [end:branch]

#! 흐름 정리
#! "[8/5 긴급 장애 대응] ..."            str
#!   ↓ {"meeting_text": Passthrough()}
#! {"meeting_text": "[8/5 긴급..."}      dict
#!   ↓ chat_prompt                       ChatPromptValue
#!   ↓ structured_llm                    MeetingNote 객체  
#!   ↓ model_dump()                      dict
#!   ↓ branch → 조건 True 인 가지만 실행
#!   ↓ 선택된 prompt | llm | parser      str
 
#! 같은 dict 가 조건함수랑 프롬프트 양쪽에 다 들어감.
#! 조건함수는 판단만 하고(True/False), dict 를 실제로 쓰는 건 선택된 체인.
#! dict 에 키가 남아도 상관없음. low_prompt 는 {summary} 하나만 쓰는데 dict 는 5개 키.
#! 여기서도 남는 건 OK / 모자란 건 KeyError.



#== ChatPromptTemplate 메서드 세 개 차이
#> 앞의 둘은 '만들기', 마지막은 '쓰기'. 단계가 다름.

# --8<-- [start:methods]
# from_template — 문자열 하나로 만들기. human 메시지 한 개짜리가 됨 [HumanMessage()]
prompt_a = ChatPromptTemplate.from_template("이 질문에 간단히 답해줘: {question}")

# from_messages — 역할별로 여러 개 만들기. [SystemMessage(),HumanMessage()]
prompt_b = ChatPromptTemplate.from_messages([
    ("system", "요약 전문가입니다."),
    ("human", "다음을 요약:\n{text}"),
])

# format_messages — 다 만든 템플릿에 값을 채워서 list[Message] 로 뽑기
print(prompt_b.format_messages(text="긴 텍스트..."))
# [SystemMessage(content='요약 전문가입니다.'), HumanMessage(content='다음을 요약:\n긴 텍스트...')]
#(1)> 만드는 게 아니라 만들어 둔 걸 쓰는 것. 확인용으로 자주 씀
# --8<-- [end:methods]

#! from_template / from_messages 는 클래스에서 바로 부름 (객체 만들기 전).
#! format_messages 는 만들어진 객체에 대고 부름. 여기서 헷갈렸음.



#== RAG 패턴 미리보기

# --8<-- [start:rag]
rag_chain = (
    {
        "context":  retriever,              # 질문으로 관련 문서 검색
        "question": RunnablePassthrough(),  # 질문 원문 그대로 통과
    }
    | prompt | llm | parser
)
#(1:7)> dict 니까 자동으로 RunnableParallel. 검색과 원문 통과가 동시에 일어남
#(1)> 결과 {"context": 문서, "question": 질문} 이 그대로 프롬프트 빈칸에 들어감
#(1)> RunnableParallel + Passthrough 조합이 RAG 의 기본형
# --8<-- [end:rag]
