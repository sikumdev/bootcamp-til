"""
title: Tool 호출 
tags: [langchain]
"""

#== @tool — 함수를 툴로 만들기
#> 데코레이터를 붙이면 평범한 함수가 Tool 객체가 됨.

# --8<-- [start:tool]

@tool
def get_employee_info(employee_id: str) -> dict:
    # docstring 이 LLM 이 읽는 설명서. "사용 시점" 을 적어주면 호출 판단이 정확해짐
    """
    직원 정보를 DB에서 조회합니다.

    사용 시점: 특정 직원의 이름, 부서, 직급 정보가 필요할 때.
    주의: 직원 ID는 반드시 'EMP' + 3자리 숫자 형식 (예: EMP001)

    Args:
        employee_id: 직원 고유 ID (형식: EMP + 3자리 숫자)

    Returns:
        직원 정보 dict: name, dept, level 키 포함
    """
    db = {
        "EMP001": {"name": "김철수", "dept": "AI개발팀", "level": "팀장"},
        "EMP002": {"name": "이영희", "dept": "기획팀",   "level": "PM"},
        "EMP003": {"name": "박민준", "dept": "데이터팀", "level": "시니어"},
    }
    return db.get(employee_id, {"error": f"직원 없음:{employee_id}"})


# @tool 이 만들어낸 게 뭔지 확인
print(type(get_employee_info))
# <class 'langchain_core.tools.structured.StructuredTool'>

print(get_employee_info)
# StructuredTool( name='', description='', args_schema='', func=<>)
#(1)> StructuredTool(
#(1)>   name='get_employee_info',
#(1)>   description="직원 정보를 DB에서 조회합니다.\n\n사용 시점: ...",
#(1)>   args_schema=<class 'langchain_core.utils.`pydantic`.get_employee_info'>, 
#(1)>   func=<function get_employee_info at 0x78babc511bc0> )

#(1)> 칸이 4개인데 앞의 3개는 LLM 에게 보여줄 설명서, func 는 실제로 실행할 원본 함수
#(1)> name → 함수 이름에서 / description → docstring 에서 / args_schema → 타입 힌트에서
#(1)> 원본 함수는 사라진 게 아니라 func 자리에 들어가 있음
#(1)> .invoke() 하면 랭체인이 args 를 검사한 뒤 이 func 를 부르는 것

# LLM 이 실제로 뭘 보는지 확인
print(get_employee_info.name)         # get_employee_info
print(get_employee_info.description)  # docstring 그대로
print(get_employee_info.args)         # {'employee_id': {'type': 'string', ...}}
# print 에는 args_schema 만 나오는데 .args 는 어디서 나오는 건지 
#(2)> class 이름:
#(2)>    def __init__(self):
#(2)>       self.args_schema = {...}      # 진짜 저장된 값
#(2)>
#(2)>    @property
#(2)>    def args(self):                   # 저장 안 하고 그때그때 계산
#(2)>        return self.args_schema["properties"]

#(2)> get_employee_info.args
#(2)> {'employee_id': {'title': 'Employee Id', 'type': 'string'}}
#(2)> get_employee_info.args_schema.model_json_schema()["properties"]
#(2)> # {'employee_id': {'title': 'Employee Id', 'type': 'string'}}   ← 같은 값


# 전체 스키마 — 타입 힌트가 Pydantic 모델로 변환된 결과
import json as json
schema = get_employee_info.args_schema.model_json_schema()

print(schema)
# {'description': '직원 정보를...', 'properties': {'employee_id': {'title': 'Employee Id', 'type': 'string'}}, 'required': ['employee_id'], ...}
#(4)> 그냥 찍으면 한 줄로 쭉 이어져서 중첩 구조가 안 보임

print(json.dumps(schema, ensure_ascii=False, indent=2))
# {
#   "description": "직원 정보를 DB에서 조회합니다. ...",
#   "properties": {
#     "employee_id": {"title": "Employee Id", "type": "string"}
#   },
#   "required": ["employee_id"],
#   "title": "get_employee_info",
#   "type": "object"
# }
#(3:9)> args_schema 가 Pydantic 모델임. 
#(3)> json.dumps(dict) → dict 를 JSON '문자열' 로 바꿈 (dump + s = string)
#(3)> ensure_ascii=False 를 줘야 한글이 \uXXXX 로 안 깨짐
#(3)> indent=2 는 보기 좋게 들여쓰기
#(3)> required 에 있는 게 필수 인자. 기본값을 준 인자는 여기서 빠짐

# --8<-- [end:tool]

#! 흐름이 이렇게 이어짐 → 먼저 툴에 들어가는 타입 힌트를 pydantic모델로 만듦
#! 타입 힌트(employee_id: str) → Pydantic 클래스 자동 생성(args_schema) → JSON 스키마 → API 요청.
#         ^^^^^^^^^^^  ^^^
#      title: 이름     type: 타입 힌트
#! 툴을 등록한다는 게 결국 이 JSON 을 llm한테 보내는 것이었음 + func(원본 함수)는 안 감. LLM 은 실행 안 하니까 필요 없음
#  (@tool → 타입 힌트 보고 자동 생성 / 구조화 출력 → class EmailSummary(BaseModel) 을 직접 작성)
#! Pydantic 클래스를 내가 선언 → with_structured_output(pydantic 클래스) →  JSON 스키마 → API 요청.
#! func(원본 함수)는 안 감. LLM 은 실행 안 하니까 필요 없음.


#! @tool 을 붙이면 더 이상 평범한 함수가 아님.
#! get_employee_info("EMP001")           (x) 그냥 못 부름
#! get_employee_info.invoke({"employee_id": "EMP001"})  (o) Runnable 이라 invoke


#== LLM 은 스키마의 어디를 보는가
#> 툴을 고를 때와 인자를 채울 때 보는 자리가 다름

# --8<-- [start:argdesc]
툴을 '고를 때'  → 위쪽 description
인자를 '채울 때' → properties 안쪽
# --8<-- [start:argdesc]
#! 인자 쪽이 {"type": "string"} 뿐이면 형식 힌트가 없어서 "EMP1" 같은 걸 넣을 수 있음.


#== 인자마다 설명 붙이기 — 두 가지 방법
 
# --8<-- [start:argdesc]
# ① docstring 을 파싱하게 시키기
#(1)> "Args:" 머리말 + 그 아래 "이름: 설명" 형태여야 인식함 (Google 스타일)
#(1)> 형식이 안 맞으면 조용히 넘어가는 게 아니라 에러가 남
#(1)> Args 부분이 인자로 빠져나가서 위쪽 description 은 요약·사용 시점만 남음


@tool(parse_docstring=True)
def get_employee_info(employee_id: str) -> dict:
    """
    직원 정보를 DB에서 조회합니다.
 
    Args:
        employee_id: 직원 고유 ID (형식: EMP + 3자리 숫자)
    """
    ...

# 붙었는지 확인
print(json.dumps(get_employee_info.args_schema.model_json_schema(), ensure_ascii=False, indent=2))
# {
#   "description": "직원 정보를 DB에서 조회합니다.",
#   "properties": {
#     "employee_id": {
#       "description": "직원 고유 ID (형식: EMP + 3자리 숫자)",
#       "title": "Employee Id",
#       "type": "string"
#     }
#   },
#   "required": ["employee_id"],
#   "title": "get_employee_info",
#   "type": "object"
# }


 
# ② Pydantic 클래스를 직접 넘기기
#(2)> 자동 생성 대신 내가 만든 클래스를 args_schema 자리에 넣는 것
#(2)> docstring 형식 제약이 없어서 확실함. 대신 클래스를 하나 더 써야 함
class EmployeeInput(BaseModel):
    employee_id: str = Field(description="직원 고유 ID (형식: EMP + 3자리 숫자)")
 
@tool(args_schema=EmployeeInput)
def get_employee_info(employee_id: str) -> dict:
    """직원 정보를 DB에서 조회합니다. 사용 시점: 이름·부서·직급이 필요할 때."""
    ...
 
# 붙었는지 확인
print(json.dumps(get_employee_info.args_schema.model_json_schema(), ensure_ascii=False, indent=2))
# "properties": {
#   "employee_id": {
#     "description": "직원 고유 ID (형식: EMP + 3자리 숫자)",   ← 생김
#     "title": "Employee Id",
#     "type": "string"
#   }
# }
# --8<-- [end:argdesc]



#== bind_tools — llm 에 툴 목록을 붙이기

# --8<-- [start:bind]
llm_with_tools = llm.bind_tools([get_employee_info])

print(type(llm_with_tools))
# <class 'langchain_core.runnables.base.RunnableBinding'>

# --8<-- [end:bind]


#== 2단계 — AI 는 JSON 만 만들고 실행은 안 함

# --8<-- [start:call]
messages = [HumanMessage(content="EMP001 직원 정보 알려줘")]
ai_msg = llm_with_tools.invoke(messages)

print(ai_msg.content)                    # '' ← 비어있음

print(ai_msg.tool_calls)
# [{'name': 'get_employee_info',
#   'args': {'employee_id': 'EMP001'},
#   'id': 'call_r8IRo2QnwZGMB6hVekzqFkxa',
#   'type': 'tool_call'}]
#(1:4)> 리스트 안에 dict. 키는 name·args·id·type 네 개
#(1)> args 는 또 dict 라서 한 겹 더 들어가야 값이 나옴

print(ai_msg.tool_calls[0]['name'])      # get_employee_info
print(ai_msg.tool_calls[0]['args'])      # {'employee_id': 'EMP001'}
print(ai_msg.tool_calls[0]['id'])        # call_r8IRo2Qn...
# AIMessage 자체는 객체(.tool_calls)인데 안쪽은 dict. 겉과 속이 다름
#(2)> 그래서 .tool_calls 는 점으로, ['name'] 은 대괄호로 꺼냄
#(2)> content 가 빈 건 아직 할 말이 없어서임. "이 툴을 이 값으로 불러줘" 만 한 상태
# --8<-- [end:call]

#! AI 는 함수를 실행할 수 없음. 실행은 내 코드가 함.
#! AI 가 하는 건 "어떤 툴을, 어떤 인자로 부를지" 정해서 JSON 으로 내놓는 것까지.
#! 그 JSON 이 곧 위의 tool_calls 임. (모델은 문자열로 뱉고 랭체인이 dict 로 파싱해 줌)
#! response_metadata 의 finish_reason 이 'stop' 이 아니라 'tool_calls' 로 나옴.
#! → 답을 마친 게 아니라 툴 결과를 기다리며 멈춘 상태라는 뜻.


#== 3단계 — 내 코드가 실행하고 결과를 이력에 넣기

# --8<-- [start:run]
messages.append(ai_msg)

for tc in ai_msg.tool_calls:
    result = get_employee_info.invoke(tc["args"])
    print(result)
    # {'name': '김철수', 'dept': 'AI개발팀', 'level': '팀장'}
    #(2)> tc["args"] 는 {'employee_id': 'EMP001'} 딕셔너리
    #(2)> 툴이 내부에서 원본함수(**args) 로 풀어서 넘김 → 함수는 str 을 받음
    #(2)> 나오는 건 원본 함수의 return 값 그대로 

    tool_msg = ToolMessage(
        content=str(result),
        tool_call_id=tc["id"],
    )
    print(tool_msg)
    # content="{'name': '김철수', 'dept': 'AI개발팀', 'level': '팀장'}"
    # tool_call_id='call_r8IRo2QnwZGMB6hVekzqFkxa'

    messages.append(tool_msg)
# --8<-- [end:run]

#! for 로 도는 이유 → tool_calls 가 리스트라서. AI 가 툴을 여러 개 한 번에 부를 수 있음.
#! 툴이 3개 호출되면 ToolMessage 도 3개를 각각 id 짝 맞춰 넣어야 함.

#! 이 시점의 messages
#! [HumanMessage("EMP001 직원 정보 알려줘"),AIMessage(content='', tool_calls=[...]),ToolMessage(content="{'name': '김철수', ...}", tool_call_id='call_...')]


#== 4단계 — 결과를 다시 넣어 자연어 답변 받기

# --8<-- [start:final]
final = llm_with_tools.invoke(messages)
print(final.content)
# EMP001 김철수는 AI개발팀 팀장입니다.

# --8<-- [end:final]

#! 모델에 메모리가 없어서 매번 messages 전체를 다시 보내야 하는 것.
#! 그래서 3단계에서 ai_msg 랑 ToolMessage 를 append 해둔 게 필수였음.

#! 정리하면 이 4단계가 한 왕복임.
#! ① bind_tools 로 툴 등록
#! ② llm 호출 → tool_calls (content 비어있음)
#! ③ 내 코드가 실행 → ToolMessage 로 결과 넣기
#! ④ 다시 llm 호출 → 최종 답변
#!
#! create_agent 는 이 ②③④ 를 알아서 반복해 주는 것.



#== 툴 여러 개 등록하기

# --8<-- [start:multi]
@tool
def calculate(expression: str) -> str:
    """
    수학 계산을 수행합니다.
    사용 시점: 사칙연산 등 숫자 계산이 필요할 때.
    expression: 계산 가능한 수식 (예: '1234 * 567', '100 / 4')
    """
    try:
        return str(eval(expression))
    except Exception as e:
        return f"계산 오류: {str(e)}"
   

@tool
def get_weather(city: str) -> str:
    """
    도시 날씨를 조회합니다.
    사용 시점: 특정 도시의 현재 날씨·기온을 물어볼 때.
    예시 질문: '서울 날씨', '오늘 도쿄 기온', '부산 날씨 알려줘'
    """
    return f"{city}: 맑음, 25도"   # Mock 데이터
    

tools     = [get_employee_info, calculate, get_weather]
llm_multi = llm.bind_tools(tools)

tool_map = {t.name: t for t in tools}
# {'get_employee_info': StructuredTool(...), 'calculate': ..., 'get_weather': ...}
#(3)> t.name 은 위에서 본 StructuredTool 의 name 칸

# --8<-- [end:multi]

#! 툴을 3개 붙이면 프롬프트에 설명 3개가 다 실려 감 → 입력 토큰이 늘어남.
#! 안 쓰는 툴을 잔뜩 붙여두면 돈도 더 들고 LLM 이 고르기도 어려워짐.


#== 수동 에이전트 — 루프로 돌리기
#> 앞의 4단계를 while 로 감싸면 그게 에이전트임.

# --8<-- [start:loop]
def agent_run(query: str, max_turns: int = 5):
    messages = [HumanMessage(content=query)]

    for turn in range(max_turns):
        ai_msg = llm_multi.invoke(messages)
        messages.append(ai_msg)

        if not ai_msg.tool_calls:
            print(f"최종 답변: {ai_msg.content}")
            return ai_msg.content, messages
        

        for tc in ai_msg.tool_calls:
            tool = tool_map.get(tc["name"])
            if tool is None:
                result = f"알 수 없는 도구: {tc['name']}"

            else:
                try:
                    result = tool.invoke(tc["args"])
                except Exception as e:
                    result = f"도구 실행 오류: {e}"

            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    return "최대 반복 횟수 초과", messages

# --8<-- [end:loop]

#! for turn in range(max_turns) 로 감싼 게 핵심.
#! 한 바퀴 = LLM 호출 1번 + 툴 실행. 툴이 필요 없어지면 도중에 return 으로 빠져나감.


#== 툴이 연달아 필요한 질문

# --8<-- [start:chained]
agent_run("오늘 날씨는 몇도인지랑 오늘날씨 온도/3 한거는 얼마야?")
# 실행 중 출력
#   get_weather({'city': '서울'}) → 서울: 맑음, 25도
#   calculate({'expression': '25/3'}) → 8.333333333333334
#   최종 답변: 오늘 서울 날씨는 25도이고, 25를 3으로 나누면 약 8.33입니다.
#   반환값 = (answer, messages) 튜플
#   answer  → "오늘 서울 날씨는 25도이고..."  (str)
#   messages → 아래 6개짜리 리스트
#(1:7)> messages 흐름
#(1)> [HumanMessage,
#(1)>  AIMessage      ← get_weather 호출
#(1)>  ToolMessage    ← "서울: 맑음, 25도"
#(1)>  AIMessage      ← calculate("25/3") 호출   ★2바퀴째
#(1)>  ToolMessage    ← "8.333..."
#(1)>  AIMessage]     ← 최종 답변

# --8<-- [end:chained]


#== tool_choice — 도구 선택 강제하기
#> 평소엔 AI 가 알아서 고르는데, 특정 툴만 쓰도록 못 박을 수 있음.

# --8<-- [start:choice]
q_weather = "서울 날씨 알려줘"

# 기본 — AI 가 알아서 고름
normal = llm_multi.invoke([HumanMessage(content=q_weather)])
print(normal.tool_calls[0]['name'] if normal.tool_calls else '직접 답변')
# get_weather

# 강제 — calculate 만 쓰게 함
llm_forced = llm.bind_tools(tools, tool_choice="calculate")

forced = llm_forced.invoke([HumanMessage(content=q_weather)])
print(forced.tool_calls[0]['name'])   # calculate
print(forced.tool_calls[0]['args'])   # {'expression': '...'}  ← 억지로 지어냄

# --8<-- [end:choice]

#! tool_choice 에 넣을 수 있는 값
#! "auto"              기본값. AI 가 알아서 판단 (툴을 안 쓸 수도 있음)
#! "필요한 툴 이름"       그 툴을 무조건 호출
#! "any" / "required" 아무거나 하나는 반드시 호출 (안 쓰는 건 금지)
#! "none"             툴을 아예 안 씀. 그냥 답만 하게 할 때
