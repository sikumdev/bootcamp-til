"""
title: 구조화 출력 — Parser · with_structured_output · Fixing
tags: [langchain]
"""


#== 방법 ① PydanticOutputParser
#> 모델한테 "이 형식으로 내놔" 라고 프롬프트에 적어서 부탁하는 방식.

# --8<-- [start:parser]
class EmailSummaryParser(BaseModel):
    person:  str = Field(description="메일을 보낸 사람의 이름")
    subject: str = Field(description="메일 제목")
    summary: str = Field(description="본문을 3문장 이내로 요약")
    date:    str = Field(description="본문에 언급된 미팅 날짜와 시간")

# 1단계 — 파서 생성, 형식 지시문 자동 생성
parser = PydanticOutputParser(pydantic_object=EmailSummaryParser)
format_instructions = parser.get_format_instructions()
#(1:3)> 내가 만든 클래스를 보고 "JSON 으로 이렇게 출력해라" 지시문을 알아서 만들어 줌
#(1)> print(format_instructions) 해보면 필드 이름·타입·description 이 다 들어간 긴 문자열임

email_raw = "안녕하세요, 홍길동 팀장님. 8/12 오전 10시 킥오프 미팅 참석 부탁드립니다."

# 2단계 — 프롬프트에 {format} 자리를 만들고 지시문을 미리 고정
prompt = ChatPromptTemplate.from_messages([
    ("system", "이메일에서 핵심 정보를 추출해. 모르면 빈 문자열로 두고 추측하지 마."),
    ("human", "아래 형식만 지켜 JSON으로 출력해.\n{format}\n\n이메일:\n{email_raw}"),
]).partial(format=format_instructions)
#  partial 은 빈칸 하나를 미리 채워두는 것 (고정해 두는 것)

# 3단계 — 체인. parser 가 JSON 문자열을 Pydantic 객체로 바꿔 줌
chain  = prompt | llm | parser
result = chain.invoke({"email_raw": email_raw})

print(type(result))    # <class 'EmailSummaryParser'>
print(result.person)   # 홍길동
print(result.date)     # 8월 12일 오전 10시
#(3:4)> 결과가 str 이 아니라 객체라서 점(.)으로 꺼냄
# --8<-- [end:parser]

#! 여기서 파서가 하는 일이 두 개임.
#! 앞에서는 형식 지시문을 만들어 프롬프트에 넣고 (get_format_instructions)
#! 뒤에서는 돌아온 JSON 문자열을 객체로 바꿈 (parse).
#! 체인 그림상 맨 뒤에만 있는 것 같지만 실제로는 앞뒤 양쪽에 관여함.


#== partial — 빈칸을 미리 채워 고정
#> 틀 하나로 전용 프롬프트 여러 개를 찍어내는 기능.
 
# --8<-- [start:partial]
translate_prompt = ChatPromptTemplate.from_template(
    "다음 회의록 요약을 {language}로 번역하세요. 번역문만 출력하세요.\n\n{summary}"
)
 
# 빈칸 2개 → 매번 둘 다 넘겨야 함
translate_prompt.invoke({"language": "영어", "summary": "..."})
 
# partial 로 language 고정
#(1)> 원본을 고치는 게 아니라 새 프롬프트를 만들어서 돌려줌
#(1)> 그래서 영어·일본어·중국어… 계속 찍어낼 수 있음
to_english  = translate_prompt.partial(language="영어")
to_japanese = translate_prompt.partial(language="일본어")
 
# 빈칸 1개로 줄어듦 → summary 만 넘기면 됨
to_english.invoke({"summary": "..."})
 
en_chain = to_english  | llm | parser
ja_chain = to_japanese | llm | parser
# --8<-- [end:partial]


#== 방법 ② with_structured_output (가장 기본)
#> 프롬프트로 부탁하는 대신, 모델한테 스키마를 직접 등록하는 방식.

# --8<-- [start:structured]
class EmailSummary(BaseModel):
    sender:       str           = Field(description="발신자 이름")
    purpose:      str           = Field(description="이메일 목적 한 문장")
    action_items: list[str]     = Field(description="처리 필요 항목 목록")
    deadline:     Optional[str] = Field(default=None, description="기한. 없으면 None")
    priority:     int           = Field(description="중요도 1~5", ge=1, le=5)

structured_llm = llm.with_structured_output(EmailSummary)

result = structured_llm.invoke(email_raw)
print(type(result))       # <class 'EmailSummary'>
print(result.sender)

# --8<-- [end:structured]
#!  스키마가 프롬프트가 아니라 API 요청 자체에 실려 감


#== 모델 안에 모델 — 중첩

# --8<-- [start:nested]
class ActionItem(BaseModel):
    assignee: str = Field(description="담당자 이름")
    task:     str = Field(description="업무 내용")
    deadline: str = Field(description="기한 (YYYY-MM-DD 형식)")

class MeetingMinutes(BaseModel):
    title:        str              = Field(description="회의 제목")
    decisions:    list[str]        = Field(description="결정 사항 목록")
    action_items: list[ActionItem] = Field(description="액션 아이템 목록")
    next_agenda:  list[str]        = Field(description="다음 회의 안건")
    #(1:1)> list[str] 은 문자열 목록, list[ActionItem] 은 객체 목록

structured_llm = llm.with_structured_output(MeetingMinutes)
result = structured_llm.invoke("회의록 원문...")

print(result.action_items[0].assignee)
#(2)> 리스트에서 꺼내고([0]) 그 안에서 또 꺼냄(.assignee)
#(2)> # [ActionItem(assignee='김철수', task='API 문서 작성', deadline='2026-08-14'),
      #  ActionItem(assignee='이영희', task='디자인 시안', deadline='2026-08-20')]
# --8<-- [end:nested]


#== ① 이랑 ② 중에 뭘 쓰나

#! PydanticOutputParser = 프롬프트로 부탁 → 모델이 안 지키면 실패함
#! with_structured_output = 모델 기능으로 강제 → 훨씬 안정적
#!
#! 웬만하면 ②. 지원하는 모델(OpenAI 등)이면 이게 쉽고 정확함.
#! ① 은 그 기능이 없는 모델을 쓰거나, 형식 지시문을 직접 손대야 할 때.
#! ② 는 프롬프트에 형식 설명이 안 들어가니까 입력 토큰도 덜 먹음.


#== OutputFixingParser — 실패하면 고쳐달라고 다시 물어보기

# --8<-- [start:fixing]
fixing_parser = OutputFixingParser.from_llm(llm=llm, parser=parser)
#(1)> 앞에서 만든 PydanticOutputParser 를 감싸는 방식

chain_with_fix = prompt | llm | fixing_parser
result = chain_with_fix.invoke({"email_raw": email_raw})
#(2:2)> 체인에서 마지막 파서만 바꿔 끼우면 됨. 나머지는 그대로

# 동작 순서
#   1) LLM 출력 → parser 로 파싱 시도
#   2) 성공 → 바로 반환
#   3) 실패 → llm 에게 "형식에 맞게 고쳐" 재요청
#   4) 고친 출력 → 다시 파싱 → 반환
#(3:6)> 실패했을 때만 2차 호출이 나감. 성공하면 추가 비용 없음
# --8<-- [end:fixing]

#! 이게 앞 노트의 "검증 실패하면 재시도하는 기능 있는지" 답이었음. 있음.
#! 대신 실패할 때마다 LLM 을 한 번 더 부르는 거라 느려지고 돈도 더 나감.
#! ② with_structured_output 을 쓰면 애초에 잘 안 틀려서 이게 덜 필요함.
#! 순서로 보면 → ② 로 막고, 그래도 새면 ① + Fixing.
