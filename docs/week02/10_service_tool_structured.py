"""
title: 서비스로 묶기 — 툴 + 구조화 출력
tags: [langchain]
"""



# --8<-- [start:setup]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

@tool
def get_related_policy(keyword: str) -> dict:
    """
    키워드와 관련된 사내 정책을 조회합니다.

    사용 시점: 사용자가 특정 업무 프로세스나 규정에 대해 질문할 때.
    예시: "재택근무 신청", "연차 사용", "출장 규정"

    Args:
        keyword: 검색할 정책 키워드 (한국어 2~10자)

    Returns:
        {'policy_name': str, 'summary': str, 'link': str}
        또는 {'error': str} (해당 정책 없을 때)
    """
    policies = {
        "재택근무": {
            "policy_name": "재택근무 운영 규정 v2.1",
            "summary": "월 최대 8일, 팀장 사전 승인 필요",
            "link": "https://hr-portal.lgcns.com/policy/remote-work",
        },
        "연차": {
            "policy_name": "연차 휴가 관리 규정",
            "summary": "입사 1년차 15일, 매년 1일씩 추가",
            "link": "https://hr-portal.lgcns.com/policy/annual-leave",
        },
    }
    for key, policy in policies.items():
        if key in keyword:
            return policy
    return {"error": f"'{keyword}' 관련 정책을 찾을 수 없습니다."}

llm_with_tools = llm.bind_tools([get_related_policy])
# --8<-- [end:setup]


#== 서비스 함수의 뼈대
#> 툴 호출 4단계를 함수로 감싼 것. 원리는 앞 노트에 정리했고, 여기선 서비스로 쓸 때의 차이만.

#! SystemMessage 를 맨 앞에 두는 게 포인트. 역할·말투가 여기서 정해짐.
#! 앞에서 RCIF 의 R 은 매번 안 바뀌니까 SystemMessage 라고 정리했던 그것.

#! while 이 아니라 if 로 짜면 왕복 1번만 처리함. 툴 → 툴 연쇄는 못 함.
#! 정책 조회 하나로 끝나는 서비스면 이걸로 충분함. 무한 루프 걱정도 없고.


#== parser 를 붙이려면

# --8<-- [start:parser]
# 1) 선언하고 바로 쓰기
parser = StrOutputParser()
final_answer = parser.invoke(ai_msg)
print(final_answer)
# 재택근무는 월 최대 8일 가능하며, 팀장의 사전 승인이 필요합니다.
#(1)> 이미 받아둔 AIMessage 를 문자열로 바꿈. .content 랑 결과 같음


# 2) 체인으로 묶기
chain  = llm_with_tools | StrOutputParser()
answer = chain.invoke(messages)
#(2:2)> 호출부터 변환까지 한 번에
# --8<-- [end:parser]

#! 툴이 있는 흐름에서는 2)가 애매함. 중간에 tool_calls 를 꺼내 봐야 하는데
#! 파서가 앞서 .content 만 남겨버리면 tool_calls 를 잃음.
#! → 툴 단계는 파서 없이 AIMessage 로 받고, 최종 문장 단계에서만 파서를 붙이는 게 맞음.


#== 툴이랑 with_structured_output 을 같이 못 쓰는 이유

#! 한 번의 호출에서 "툴을 부를지" 와 "정해진 형식으로 답할지" 를 동시에 못 시킴.
#! 둘 다 같은 function calling 자리를 쓰기 때문임.
#! → 그래서 호출을 2단계로 쪼갬. 1단계는 툴, 2단계는 형식.

#! 2단계의 structured_llm 에는 툴이 안 붙어 있음(bind_tools 안 함).
#! 그러니 1단계에서 필요한 정보를 messages 에 다 모아둬야 함.


#== v3 — 2단계로 나누기

# --8<-- [start:v3]
class PolicyAnswer(BaseModel):
    policy_name: str  = Field(description="정책 공식 명칭. 없으면 '해당 없음'")
    answer:      str  = Field(description="사용자 질문에 대한 친절한 안내 문장")
    link:        str  = Field(default="", description="정책 원문 링크. 없으면 빈 문자열")
    found:       bool = Field(description="관련 정책을 찾았는지 여부")
    #(1)> found 로 성공·실패를 표시하면 뒤에서 if 로 분기하기 좋음

structured_llm = llm.with_structured_output(PolicyAnswer, include_raw=True)

def run_service_v3(user_question: str) -> dict:
    messages = [
        SystemMessage(content="당신은 LG CNS 사내 HR 정책 안내 도우미입니다. 친절하게 안내해주세요."),
        HumanMessage(content=user_question),
    ]

    # 1단계 — 툴 사용
    ai_msg = llm_with_tools.invoke(messages)
    messages.append(ai_msg)

    if ai_msg.tool_calls:
        for tc in ai_msg.tool_calls:
            result = get_related_policy.invoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # 2단계 — 지금까지의 대화를 구조화
    messages.append(HumanMessage(content="위 내용을 정해진 형식으로 정리해줘."))
    return structured_llm.invoke(messages)
    #(2)> HumanMessage 를 하나 더 끼워 넣는 게 요령
    #(2)> ToolMessage 로 끝나면 "이제 뭐 하라는 거지" 가 없어서, 지시를 한 줄 더 준 것
# --8<-- [end:v3]

#! 이 시점의 messages
#! SystemMessage
#! HumanMessage("재택근무 신청은?")
#! AIMessage(tool_calls=[...])                    ← 1단계, llm_with_tools 가 생성
#! ToolMessage("{'policy_name': ...}")            ← 도구 실행 결과
#! HumanMessage("위 내용을 정해진 형식으로 정리해줘")     ← 우리가 추가
#! AIMessage(구조화된 결과)                          ← 2단계, structured_llm 이 생성


#== include_raw=True

# --8<-- [start:raw]
out = run_service_v3("재택근무 신청은 어떻게 하나요?")

print(out.keys())
# dict_keys(['raw', 'parsed', 'parsing_error'])
#(1)> include_raw=True 면 객체가 아니라 dict 로 나옴

print(out["parsed"])
# PolicyAnswer(policy_name='재택근무 운영 규정 v2.1', answer='재택근무는 월 최대 8일...', found=True)
#(2)> 평소에 쓰는 건 이것. include_raw 를 안 쓰면 이게 바로 반환됨

print(out["raw"])
# AIMessage(content='{"policy_name":"재택근무 운영 규정 v2.1", ...}', tool_calls=[])
#(3)> 모델이 실제로 뱉은 원본. content 에 JSON 문자열이 그대로 들어있음

print(out["parsing_error"])   # None
#(4)> 파싱이 깨지면 여기에 에러가 담김. 예외가 안 터지고 넘어감

# parsed 는 객체라서 점으로 꺼냄
print(out["parsed"].policy_name)   # 재택근무 운영 규정 v2.1
print(out["parsed"].found)         # True
print(out["parsed"].model_dump())
# {'policy_name': '재택근무 운영 규정 v2.1',
#  'answer': '재택근무는 월 최대 8일 가능하며, 팀장의 사전 승인이 필요합니다.',
#  'link': 'https://hr-portal.lgcns.com/policy/remote-work',
#  'found': True}
#(5:4)> 바깥은 dict(대괄호), 안쪽 parsed 는 객체(점). 겹칠 때 헷갈리기 쉬움
#(5)> API 응답으로 내보내려면 model_dump() 로 dict 변환
# --8<-- [end:raw]

#! include_raw 를 안 쓰면(기본값 False) 파싱 실패 시 그냥 예외가 터짐.
#! True 로 두면 parsed=None, parsing_error=에러 로 담겨서 내가 처리할 수 있음.
#! → 실서비스에서는 True 로 두고 parsing_error 를 확인하는 게 안전할 듯.


#! 토큰도 같이 볼 것. 2단계 호출의 prompt_tokens 가 408 인데,
#! 앞의 대화(System·Human·AI·Tool·Human)를 통째로 다시 보내서 그럼.
#! 단계를 나누면 안전한 대신 입력 토큰이 늘어남.

