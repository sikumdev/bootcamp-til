"""
title: 실전 툴 — 웹 검색 · 날짜 · 워크플로 함수
tags: [langchain]
"""

#== Tavily 응답 구조 뜯어보기
#> 툴로 감싸기 전에 뭐가 나오는지 먼저 봄.

# --8<-- [start:tavily]
tavily = TavilySearch(max_results=3)
raw = tavily.invoke("LangChain 최신 버전")

print(raw) 
# 결과 값 -> dict
#(4)> {
#(4)>   'query': 'LangChain 최신 버전',
#(4)>   'follow_up_questions': None,
#(4)>   'answer': None,
#(4)>   'images': [],
#(4)>   'results': [
#(4)>     {'url': 'https://m.blog.naver.com/beyond-zero/224171603930',
#(4)>      'title': '2026년, 여전히 LangChain인가? AI 엔지니어가 랭체인 도입을 반대하는 3가지 이유',
#(4)>      'content': 'LangChain은 2026년 현재도 가장 널리 쓰이는 프레임워크지만...',
#(4)>     'score': 0.98},
#(4)>     {'url': '...', 'title': '...', 'content': '...', 'score': 0.87},
#(4)>     {'url': '...', 'title': '...', 'content': '...', 'score': 0.81}
#(4)>   ],
#(4)>   'response_time': 1.42
#(4)> }

print(raw.keys())
# dict_keys(['query', 'follow_up_questions', 'answer', 'images', 'results'])
#(1)> 반환값은 dict. 쓸 건 사실상 results 하나뿐임

results = raw.get("results", [])
print(f"총 결과 수: {len(results)}개")
#(2)> dict.get(키, 기본값) → 키가 없어도 에러 안 나고 기본값을 줌

if results:
    r0 = results[0]
    print(r0.get('title', 'N/A'))
    # 2026년, 여전히 LangChain인가? AI 엔지니어가 랭체인 도입을...
    print(r0.get('url', 'N/A'))
    # https://m.blog.naver.com/beyond-zero/224171603930
    print(r0.get('content', '')[:50])
    # 본문 앞 50자만. 원본은 수백~수천 자라 그대로 찍으면 화면이 덮임
    print(r0.get('score', 'N/A'))
    # 0.98
    #(3)> score 는 검색어와 얼마나 관련 있는지 점수 (0~1). 높을수록 상위
    #(3)> 문서끼리의 유사도가 아니라 '질문 ↔ 문서' 관련도
# --8<-- [end:tavily]


#== web_search — 툴로 감싸기

# --8<-- [start:websearch]
@tool
def web_search(query: str, max_results: int = 5) -> str:
    """
    웹을 실시간으로 검색해 최신 정보를 가져옵니다.

    사용 시점: LLM 학습 데이터 이후 최신 정보(신제품 출시·가격·인물 근황 등)가 필요할 때.
    사용하지 말 것: 역사적 사실, 일반 상식 등 이미 알고 있는 정보.

    Args:
        query: 검색어 (한국어/영어 모두 가능)
        max_results: 반환할 결과 수 (기본 5, 최대 20)
    """
    results = TavilySearch(max_results=max_results).invoke(query)["results"]
    return "\n---\n".join(
        f"제목: {r.get('title','N/A')}\nURL: {r.get('url','')}\n내용: {r.get('content','')}"
        for r in results
    )

print(web_search.invoke({"query": "LangChain 최신 버전", "max_results": 2}))
# 제목: 2026년, 여전히 LangChain인가?
# URL: https://m.blog.naver.com/beyond-zero/224171603930
# 내용: LangChain은 2026년 현재...
# ---
# 제목: LangChain 공식 릴리스 노트
# URL: https://python.langchain.com/...
# 내용: v1.0 부터는...
# --8<-- [end:websearch]

#! docstring 에 "사용하지 말 것" 을 넣은 게 좋았음.
#! 안 쓸 때를 알려주면 아무 질문에나 검색을 돌리는 걸 줄일 수 있음.

#! max_results: int = 5 처럼 기본값을 주면 LLM 이 안 넘겨도 됨.
#! 필수 인자가 적을수록 툴 호출이 덜 틀림.


#== current_date — LLM 이 모르는 것 채워주기

# --8<-- [start:date]
@tool
def current_date() -> str:
    """
    현재 날짜를 조회합니다.

    사용 시점: 오늘 날짜·현재 시각이 필요할 때.
    예시 질문: '오늘 몇 월이야?', '지금 몇 년도야?', '이번 달이 뭐야?'

    Returns:
        str: YYYY-MM-DD 형식의 현재 날짜
    """
    return datetime.now().strftime("%Y-%m-%d")

print(current_date.invoke({}))
# 2026-08-06
#(1)> 인자가 없는 툴도 됨. 대신 invoke 에 빈 dict {} 를 넘겨야 함
# --8<-- [end:date]

#! LLM 은 오늘이 며칠인지 모름. 학습 시점에서 멈춰 있음.
#! 그래서 "다음 주 금요일" 같은 걸 날짜로 바꾸라 하면 지어냄.
#! → 구조화 출력에서 날짜를 원문 그대로 받아두라고 했던 이유가 이거였음.


#== simple_workflow — 루프를 함수로
#> 루프 원리는 앞 노트(툴 호출 4단계)에 정리했음. 여기선 달라진 것만.

# --8<-- [start:workflow]
def simple_workflow(llm, question: str, tools: list) -> str:
    """질문과 도구 목록을 받아 도구 호출이 끝날 때까지 반복 실행합니다."""
    tool_list = {t.name: t for t in tools}
    llm_wt    = llm.bind_tools(tools)
    messages  = [HumanMessage(content=question)]

    ai_msg = llm_wt.invoke(messages)
    messages.append(ai_msg)

    while ai_msg.tool_calls:
        for tc in ai_msg.tool_calls:
            tool_exec = tool_list[tc["name"]]
            tool_msg  = tool_exec.invoke(tc)
            #(1)> tc 를 통째로 넘기면 ToolMessage 가 바로 나옴 
            messages.append(tool_msg)

        ai_msg = llm_wt.invoke(messages)
        messages.append(ai_msg)

    return ai_msg.content
# --8<-- [end:workflow]

# --8<-- [start:workflow_run]
tools_basic = [get_employee_info, calculate, current_date]

print(simple_workflow(llm, "EMP002 직원 정보 알려줘", tools_basic))
# EMP002 이영희님은 기획팀 PM입니다.

print(simple_workflow(llm, "1234 * 567은?", tools_basic))
# 1234 × 567 = 699,678 입니다.

print(simple_workflow(llm, "오늘 날짜는?", tools_basic))
# 오늘은 2026년 8월 6일입니다.

# --8<-- [end:workflow_run]

#! 달라진 것 두 가지 → ① tool.invoke(tc) 로 바꿈  ② tools 를 인자로 받게 함.
#! tools 를 밖에서 받으니 질문마다 툴 조합을 바꿔 끼울 수 있음.


#== tool.invoke(tc) vs tool.invoke(tc["args"])
#> 앞 노트랑 여기가 다른 지점. 뭘 넘기느냐에 따라 나오는 게 다름.

# --8<-- [start:two_ways]
# ① args 만 넘기기 → 함수의 반환값이 그대로 나옴
result = tool_exec.invoke(tc["args"])      # {'name': '이영희', 'dept': ...}
messages.append(ToolMessage( content=str(result),tool_call_id=tc["id"],))
# 결과를 받아서 ToolMessage 를 내가 만들어야 함
#(1)> content 를 str() 로 감싸고 tool_call_id 도 직접 챙겨야 함

# ② tc 전체 넘기기 → ToolMessage 가 바로 나옴
tool_msg = tool_exec.invoke(tc)            # ToolMessage(content='...', tool_call_id='call_...')
messages.append(tool_msg)
# tc 에 name·args·id·type 이 다 들어있으니 랭체인이 알아서 채워 줌
#(2)> 문자열 변환도 id 연결도 자동. 
# --8<-- [end:two_ways]


#== while vs for(max_turns)

#! 여기선 while ai_msg.tool_calls 로 돌렸는데, 종료 보장이 없음.
#! LLM 이 툴을 계속 부르면 안 멈춤 → API 비용이 계속 나감.
#! 실습이라 괜찮지만, 앞에서 쓴 max_turns 같은 상한을 두는 게 안전함.

#! 정리
#! while  = 끝날 때까지. 코드가 짧고 의도가 분명함
#! for + max_turns = 안전장치 있음. 대신 초과 시 처리도 써야 함
