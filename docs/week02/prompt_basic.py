"""
title: 프롬프트 작성법 — RCIF · shot
tags: [langchain]
"""

#== RCIF — 프롬프트에 넣을 4가지
#> R 역할 · C 배경 · I 지시 · F 형식. 이 중 빠진 게 있으면 AI 가 알아서 채워버림.

# --8<-- [start:rcif]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

meeting_text =  """
                박팀장: 신제품 출시를 8월 15일로 확정하자고 제안합니다.
                김팀장: 동의합니다. 마케팅은 SNS 먼저 시작하고요.
                이팀장: AI 추천 기능은 9월 적용하겠습니다. 개발 일정 필요해요.
                """

# 지시만 있고 형식이 없음 → 정리 방식을 AI 가 알아서 고름 (결과 구조도 매번 달라져서 다음 단계에서 쓰기 어려움)
bad = llm.invoke(f"회의록 정리해줘:\n{meeting_text}")

# R 은 SystemMessage 에, C·I·F 는 HumanMessage 에 넣음
good = llm.invoke([
                    SystemMessage(content="[R] 당신은 비즈니스 커뮤니케이션 전문가입니다."),
                    HumanMessage(content=f"""[C] 킥오프 회의 기록입니다.
                                            {meeting_text}

                                            [I] 아래 형식으로 정리해주세요.
                                            [F]
                                            1. 핵심 결정 사항 (번호 목록)
                                            2. 액션 아이템 표: 담당자 | 내용 | 기한
                                            3. 다음 회의 안건"""),
                  ])
# --8<-- [end:rcif]

#! R = 어떤 전문가로서 답할지, C = 판단에 필요한 자료 I = 무엇을 할지, F = 어떤 모양으로 내놓을지
#! 넷 중 제일 자주 빠뜨리는 게 F(형식). 형식 안 주면 결과가 매번 달라짐.


#== Zero-shot vs Few-shot
#> 예시를 주느냐 마느냐의 차이. 주는 쪽이 few-shot.

# --8<-- [start:shot]
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

few = llm.invoke(
                    f"고객 문의를 분류해. 분류: [배송문의, 환불, 제품불량, 기타]\n\n"
                    f"예시:\n"
                    f"'주문 2주 됐는데 배송 안 됐어요.' → 배송문의\n"
                    f"'화면에 금이 가 있어요.' → 제품불량\n"
                    f"'환불하고 싶어요.' → 환불\n\n"
                    f"분류할 문의: '{inquiry}'\n"
                    f"분류 결과만 출력:"
                )
# --8<-- [end:shot]

#! 쉬운 문제는 zero-shot 으로도 같은 답이 나옴.
#! 차이가 벌어지는 건 경계가 애매한 케이스랑, 출력 형식을 정확히 맞춰야 할 때임.


#== 한 번에 완성하지 않는다
#> 프롬프트는 짧게 시작해서 부족한 걸 하나씩 더하면 됨.

# --8<-- [start:iter]
# v1 — 일단 되는지 확인
"이메일 요약:\n{email}"

# v2 — 형식(F) 추가
"아래 형식으로 요약:\n- 발신자:\n- 핵심 요청:\n- 시급성:\n\n{email}"

# v3 — 역할·독자·제약 추가
"바쁜 임원 보고 관점으로 요약해.\n"
"- 이름:\n- 핵심 요청 (20자 이내):\n- 필요 조치 (즉시처리/검토필요/참고):\n- 기한:\n\n{email}"

# --8<-- [end:iter]

#! v1 → v3 에서 늘어난 건 결국 R(임원 보고 관점) · F(필드와 글자 수) · 선택지임.
#! 반복 개선이란 곧 RCIF 의 빈칸을 하나씩 메우는 과정인 듯.