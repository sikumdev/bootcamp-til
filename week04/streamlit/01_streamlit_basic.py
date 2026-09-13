"""
title: Streamlit — rerun · session_state · 채팅
tags: [streamlit]
"""

#== Streamlit 이 뭐냐
#> 파이썬 파일 하나가 그대로 웹 화면이 되는 도구.

# --8<-- [start:hello]
# apps/hello.py
import streamlit as st

# 다른 st 함수보다 먼저 와야 함. 뒤에 두면 에러
st.set_page_config(page_title="도서관 대시보드", layout="centered")

st.title("우리 도서관 대시보드")
st.write("첫 Streamlit 앱입니다.")

# 터미널에서:  streamlit run apps/hello.py
# 브라우저에서: http://localhost:8501
# --8<-- [end:hello]

#== st.set_page_config — 페이지 전체 설정
#> 브라우저 탭 제목·아이콘·화면 폭처럼 `페이지 자체`에 관한 설정.

# --8<-- [start:page_config]
st.set_page_config(
    page_title="도서관 대시보드", # 브라우저 탭에 뜨는 이름. 안 주면 파일명이 그대로 나옴
    page_icon="📚",     # 탭 아이콘 (파비콘).
    layout="centered",
    #(3)> "centered"(기본) 은 가운데 좁게, "wide" 는 화면 끝까지 넓게
    initial_sidebar_state="expanded",
    #(4)> 사이드바를 처음부터 펼칠지. "collapsed" 면 접힌 채로 시작
)
# --8<-- [end:page_config]

#! set_page_config는 반드시 `다른 st 함수보다 먼저` 와야 함.
#! 한 번만 부를 수 있음. 두 번 부르면 에러.
#! `layout="wide"` 는 대시보드에 유용함. 표와 차트를 나란히 놓을 공간이 생김.
#! 반대로 글이 많은 화면은 centered 가 읽기 편함.

#== 화면에 뭔가 출력하는 함수들
#> print 자리에 들어가는 것들. 종류가 많은데 용도가 다 다름.

# --8<-- [start:output]
# 제목
st.title("가장 큰 제목")            # 페이지당 하나
st.header("중간 제목")
st.subheader("작은 제목")

# 본문
st.write("아무거나 넣으면 알아서 그려줌")
#(1)> 문자열·숫자·dict·DataFrame·차트까지 다 받음. 제일 만만한 함수
st.markdown("## 마크다운 문법이 먹힘  **굵게**  `코드`")
st.caption("작고 회색인 보조 설명")
#(2)> 각주나 안내 문구에 씀

# 알림 상자 (색이 다름)
#(4)> 알림 상자 4개는 색만 다르고 하는 일은 같음. 상황에 맞게 고르면 됨.
#(4)> 입력 검증 실패 → warning, 저장 완료 → success, 예외 → error
st.info("파란색 — 안내")
st.success("초록색 — 성공")
st.warning("노란색 — 주의")
st.error("빨간색 — 오류")

# 구조화된 데이터
st.json({"이름": "김시연", "점수": 95})
#(3)> dict 를 접었다 펼 수 있는 형태로 예쁘게 보여줌. 디버깅에 유용
st.dataframe(df)   # 표
st.metric("방문자", 152, delta=23)   # 숫자 하나
# --8<-- [end:output]

#! `st.write` 와 `st.markdown` 차이
#! write   → 뭘 넣든 타입을 보고 알아서 처리. dict 를 넣으면 표처럼 그려줌
#! markdown→ 문자열만. 대신 마크다운 문법을 확실히 적용


#== `st.write(dict)` 와 `st.json(dict)` 차이
#> `st.write(*args)`            — 여러 개를 받음. 타입 제한 없음
#> `st.json(body, *, expanded)` — 하나만. 대신 옵션이 있음

# --8<-- [start:write_vs_json]
# write 는 여러 개를 한 번에 받고, 타입별로 알아서 갈라 줌
st.write("문자열", 123)        # → markdown 요소  ('문자열 `123`')
st.write({"a": 1})           # → json 요소
st.write([1, 2, 3])          # → json 요소
st.json({"a": 1})            # → json 요소  ← 위와 같음

# 유일한 차이 → write 로는 접기 조절을 못 함
st.json(data, expanded=False)   # 접힌 채로 시작
st.json(data, expanded=2)       # 2단계까지만 펼침
# --8<-- [end:write_vs_json]
 

#! 뭐가 올지 모름 / 여러 개 한 번에 → write
#! dict·리스트 확실 + 접기 조절 필요 → json
#! `(참고)`
#! `st.json(dict(st.session_state), expanded=False)` 는 디버깅에 좋음.


#== rerun — 제일 먼저 이해해야 할 것
#> 위젯을 건드리면 `파일을 첫 줄부터 끝까지 통째로 다시 실행`함.
#> 위젯이란 "값을 돌려주고, 건드리면 rerun 을 일으키는 것" 
#! 보통은 "버튼이 눌리면 이 함수만 실행" 인데, Streamlit 은 그런 게 없음.
#! 버튼을 누르든 슬라이더를 옮기든 → 파일 전체가 처음부터 다시 돎.
#! 이 재실행을 `rerun` 이라고 부름.
#! 화면은 매번 새로 그려지는 것. "고치는" 게 아니라 "다시 그리는" 것.

# --8<-- [start:what_is_widget]
# 위젯 — 값을 돌려줌
name    = st.text_input("이름")       # → ''
score   = st.slider("점수", 1, 5, 3)  # → 3
clicked = st.button("버튼")           # → False
 
# 위젯 아님 — 값을 안 돌려줌 (화면에 그리기만)
out = st.write("그냥 출력")           # → None
m   = st.metric("숫자", 100)         # → 그리기 도구 객체 (값이 아님)
# --8<-- [end:what_is_widget]

#! 위젯 구분 기준 세 가지. 셋이 같이 움직임.
#! ① `사용자 입력을 값으로 돌려주는가`
#! ② `건드리면 rerun 이 일어나는가`
#! ③ `session_state 에 상태가 저장되는가`
#! `expander·tabs 는 클릭되는데 왜 위젯이 아니냐` →
#! 그건 `레이아웃 도구`임. 화면을 나누고 접는 것뿐이고 사용자 입력을 안 받음.
#! 펼치든 접든 서버는 모름. 값을 돌려주지도 않고 session_state 에도 안 남음.

#== 그래서 일반 변수는 값이 안 쌓임
 
# --8<-- [start:wrong_counter]
import streamlit as st
 
st.title("일반 변수 카운터")
 
count = 0
if st.button("+1"):
    count += 1

# 아무 일도 안 하는 버튼. rerun 만 일으키는걸 눈으로 확인하기 위한 용도
#(1)> +1 만 계속 누르면 값이 1로 고정돼서 "버튼이 고장났나" 처럼 보임.
#(1)> 해당 버튼을 눌렀을 때 `1 이 0 으로 돌아가는 걸` 봐야
#(1)> "내가 안 건드린 값이 왜 초기화되지?" → "파일이 다시 돌았구나" 알 수 있어서 예제 변경함
st.button("확인용 버튼")
 
st.write("현재 값:", count)

# 전체 흐름 
#(2)> 첫 화면        → 현재 값: 0
#(2)> +1 클릭        → 현재 값: 1
#(2)> `확인용 클릭`   → 현재 값: `0`   ← 여기가 핵심. 안 건드린 값이 초기화됨
# --8<-- [end:wrong_counter]
 
 
#! ① 확인용 버튼 클릭
#! ② 파일 처음부터 재실행
#! ③ `count = 0` 이 다시 실행됨 ← 여기서 초기화됨
#! ④ 지금 눌린 버튼이 +1 이면 count += 1 → 1
#! ⑤ 확인용 버튼을 눌렀으면 +1 은 False → count 가 0 그대로
#! 2 가 되려면 `count = 0` 이 다시 안 돌아야 하는데, rerun 이라 무조건 돎.
#! → 일반 변수는 rerun 을 못 버팀. 매번 새로 태어남.


#== session_state — rerun 을 버티는 저장소
#> 화면 뒤에 따로 있는 보관함. 파일이 다시 실행돼도 안 지워짐.
 
#! 정체가 뭐냐 → `딕셔너리처럼 쓰는 물건`
#! 중요한 건 `{}` 처럼 쓸 수 있다는 것. dict 라고 생각하면 다 맞음.
 
# --8<-- [start:ss_dict]
# 넣기 — 두 방법 다 같음
st.session_state["count"] = 0
st.session_state.count = 0
 
# 꺼내기
st.session_state["count"]
st.session_state.count
 
# 있는지 확인 — dict 와 똑같이 in
"count" in st.session_state     # True / False
# --8<-- [end:ss_dict]
 
#! `{'count': 3}`
#! 진짜 그냥 딕셔너리임. 키에 이름, 값에 저장할 것.
#! 어디에 저장되냐 → 브라우저 탭 하나(세션)마다 하나씩.
#! 다른 사람이 접속하면 그 사람은 자기 것을 따로 가짐.
#! 새로고침(F5)하면 세션이 새로 시작돼서 초기화됨.


# --8<-- [start:ss_bad_init]
# ❌ 조건문 없이 이렇게 쓰면
st.session_state.count = 0

# session_state 를 썼는데도 화면은 계속 1
if st.button("+1"):
    st.session_state.count += 1
# --8<-- [end:ss_bad_init]


# --8<-- [start:ss_init]
import streamlit as st

if "count" not in st.session_state:
#(2)> `if not in` 은 "첫 실행에만 만들어라" 라는 뜻.
#(2)> 첫 실행 → 없으니까 만듦 (0)
#(2)> 두 번째 rerun → 이미 있으니까 건너뜀 → 기존 값 유지
    st.session_state.count = 0
    
if st.button("+1"):
    st.session_state.count += 1
 
st.write("현재 값:", st.session_state.count)
# --8<-- [end:ss_init]
  
#! 왜 조건문이 필요하냐 → rerun 때마다 이 줄도 다시 실행됨. 조건이 없으면 매번 0 으로 덮어씀.

 
# --8<-- [start:ss_plain]
# 파이썬으로 단순화하면 이 구조임

state = {}
 
def one_rerun(state):
    if "count" not in state:      # ← 없을 때만 만들기
        state["count"] = 0
    state["count"] += 1
    return state["count"]
 
print([one_rerun(state) for _ in range(3)])   # [1, 2, 3]
# --8<-- [end:ss_plain]
 
 
#== 정리하면 세 줄
 
#! 일반 변수  → rerun 때 다시 태어남. 값이 안 남음
#! session_state → rerun 을 넘어서 살아남음
#! `if not in` → rerun 때마다 초기화되는 걸 막는 장치
#! 핵심 → "rerun 때 다시 실행되면 곤란한 줄은 if not in 으로 감싼다".
 
 
#== st.button 은 눌린 그 순간만 True
 
#! 이것도 rerun 때문에 생기는 특징임.
#! `if st.button("저장")` 은 버튼을 누른 그 rerun 에서만 True.
#! 다음 rerun 에서는 다시 False 가 됨.
#! "눌렀다" 는 사실을 계속 기억해야 하면 session_state 에 저장할 것.

# --8<-- [start:button_state]
if st.button("시작"):
    st.session_state.started = True
    #(1)> 버튼 자체는 곧 False 로 돌아가니 사실을 따로 남겨둠
 
if st.session_state.get("started"):
    st.write("시작된 상태입니다")
# --8<-- [end:button_state]
 
#! `st.rerun()` — 코드에서 직접 rerun 을 일으키는 함수.
#! 값을 바꾼 뒤 화면에 즉시 반영하고 싶을 때 씀 (초기화 버튼 같은 것).


#== 입력 위젯 — 화면을 그리면서 값도 돌려줌
#> `st.text_input(...)` 은 입력칸을 그리는 동시에 현재 값을 반환함. 두 가지를 한 번에.
 
# --8<-- [start:widgets]
import streamlit as st
 
name = st.text_input("이름")
age = st.number_input("나이", min_value=0, step=1)
city = st.selectbox("도시", ["서울", "부산", "대전"])
grade = st.radio("등급", ["basic", "gold"], horizontal=True)
agree = st.checkbox("개인정보 수집에 동의합니다")
score = st.slider("만족도", 1, 5, 3)
#(1)> slider(라벨, 최소, 최대, 기본값)
 
if st.button("입력 확인"):
    if not name:
        st.warning("이름을 입력하세요.")
    elif not agree:
        st.warning("동의 항목을 확인하세요.")
    else:
        st.write(f"{name}님, {age}세, {city}, {grade}, 만족도 {score}점")
# --8<-- [end:widgets]
 
#! 아무것도 안 건드렸을 때 반환값을 직접 찍어봤음
#! text_input   → `''`      (빈 문자열)
#! number_input → `0`       (min_value 값)
#! selectbox    → `'서울'`   (목록의 첫 항목)
#! radio        → `'basic'` (목록의 첫 항목)
#! checkbox     → `False`
#! slider       → `3`       (세 번째 인자로 준 기본값)
 
 
# --8<-- [start:widget_table]
 위젯             반환값             
 text_input      문자열             
 number_input    숫자                
 selectbox       고른 항목            
 radio           고른 항목            
 checkbox        True / False       
 slider          숫자                
 button          눌린 경우 True 
# --8<-- [end:widget_table]
 
#! 값이 바뀌면 그 즉시 rerun 이 일어남.
#! 슬라이더를 옮기는 순간 파일이 처음부터 다시 돎 → 아래 코드가 새 값으로 다시 실행됨.
#! 그래서 "값을 받아서 바로 아래에서 쓰는" 구조가 자연스럽게 됨.
 
 
#== st.form — 여러 입력을 한 번에 제출
#> 위젯 하나 건드릴 때마다 rerun 되는 게 곤란할 때 씀.
 
#! 문제 상황 → 설문에 입력칸이 5개인데, 하나 칠 때마다 rerun 되면서
#! 결과 처리 코드가 계속 실행됨. DB 저장이 걸려 있으면 큰일남.
 
# --8<-- [start:form]
with st.form("survey"):
    #(1)> "survey" 는 form 을 구분하는 이름. 여러 개면 서로 달라야 함
    name = st.text_input("이름")
    subject = st.selectbox("수강 과목", ["Python", "SQL", "Streamlit"])
    score = st.slider("만족도", 1, 5, 3)
    recommend = st.checkbox("다른 사람에게 추천하겠습니다")
    submitted = st.form_submit_button("제출")
    #(2)> st.button 이 아니라 st.form_submit_button. form 안에서는 이걸 써야 함
 
if submitted:
#(3)> 제출 버튼을 누르면 rerun 이 일어나고, 그 rerun 에서만 여기가 실행됨
#(3)> 다음 rerun 부터는 submitted 가 다시 False 라 건너뜀
    st.success("제출 완료")
    st.write({"이름": name, "수강 과목": subject, "만족도": score, "추천": recommend})
# --8<-- [end:form]
 
 
#== form 안에서는 rerun 이 아예 안 일어남
#> 이게 form 의 전부임. "묶어서 한 번에 보낸다" 는 뜻.
 
#! form 밖 위젯 → 건드리는 즉시 rerun. 슬라이더 한 칸 옮겨도 파일 전체가 다시 돎
#! form 안 위젯 →  아무리 건드려도 rerun `안 일어남`.
#!               브라우저가 값을 들고만 있고 서버로 안 보냄
#! 제출 버튼      → 이때 값을 전부 한 번에 보내면서 rerun 이 딱 `1회` 일어남
  

#== submitted 는 제출한 그 rerun 에만 True
#> "제출 후에 오는 rerun" 이 아니라 "제출 클릭이 만든 그 rerun" 임. 
  
#! 즉 `제출 클릭 = rerun 시작`. 클릭이 rerun 을 만드는 것이지
#! "제출하고 나서 따로 rerun 이 온다" 가 아님.
#! st.button 과 완전히 같은 성격임 — 눌린 그 rerun 에서만 True.
#! 제출 횟수를 세려면 session_state 에 쌓아야 함.
 
 
#== name 같은 변수는 어떻게 값을 유지하나
#> 변수가 살아있는 게 아님. `위젯이` 값을 들고 있는 것.
 
# --8<-- [start:form_value_alive]
with st.form("f"):
    name = st.text_input("이름", key="name")
    submitted = st.form_submit_button("제출")
 
st.markdown(f"rerun #{st.session_state.n} | name={name!r} | submitted={submitted}")
# --8<-- [end:form_value_alive]
 

#! rerun #1  첫 실행       name=''        submitted=False
#! rerun #2  이름 입력      name='김시연'   submitted=False
#! rerun #3  제출 클릭      name='김시연'   submitted=True
#! rerun #4  그냥 rerun    name='김시연'   submitted=False  ← 아무것도 안 했는데 값이 있음
#! rerun #5  다시 제출      name='김시연'   submitted=True
#! `변수가 살아남은 게 아니라`
#! → `st.text_input(...)` 이 다시 실행되면서 위젯이 저장해둔 값을 또 돌려준 것.
#! `즉 `name` 이라는 변수는 rerun 마다 죽고 새로 태어남.`
#! `값을 들고 있는 건 변수가 아니라 위젯임.`
 
 
# --8<-- [start:who_holds]
# 값을 들고 있는 주체가 누구냐
   count = 0                        → 아무도 안 들고 있음
                                      rerun 마다 0 으로 초기화
   name = st.text_input(...)        → 위젯이 들고 있음
                                      rerun 마다 같은 값을 다시 줌
   submitted = st.form_submit_...   → 아무도 안 들고 있음
                                      제출한 rerun 에만 True
# --8<-- [end:who_holds]
 
#! 카운터가 안 쌓였던 이유가 여기서 명확해짐.
#! `count` 는 그냥 파이썬 변수라 들고 있는 주체가 없었고,
#! `name` 은 위젯이 들고 있어서 살아남는 것.
#! 그래서 form 을 쓰든 안 쓰든 위젯 값은 유지됨.
#! form 이 바꾸는 건 "언제 rerun 이 일어나는가" 하나뿐임.
 
#== metric · 표 · 차트
#> 같은 데이터라도 목적에 따라 표시 방법이 다름.
 
#! 숫자 하나를 크게      → st.metric
#! 여러 행을 정확히      → st.dataframe
#! 항목 간 크기 비교     → st.bar_chart
#! 시간에 따른 변화      → st.line_chart
 
# --8<-- [start:metric]
# 화면을 세 칸으로 나눔. 
c1, c2, c3 = st.columns(3)

# metric(라벨, 값, delta). delta 는 이전 대비 변화량
#(2)> 양수면 초록 위 화살표, 음수면 빨강 아래 화살표
c1.metric("오늘 방문자", 152, delta=23)
c2.metric("대출 권수", 87, delta=5)
c3.metric("연체 권수", 4, delta=-2)
# --8<-- [end:metric]
 
 
#==  차트에서 set_index 를 왜 하나
#> DataFrame 의 `인덱스가 x축`이 되기 때문.
 
# --8<-- [start:set_index]
import pandas as pd

# set_index 설정 없이 표를 그리면 일어나는 일
#(1)> 인덱스: [0, 1, 2, 3]  ← 이대로 차트를 그리면 x축이 0,1,2,3
#(1)> 열: ['카테고리', '문서 수']  ← 카테고리도 하나의 열로 취급됨
df = pd.DataFrame({"카테고리": ["이용안내","대출","시설","프로그램"],
                   "문서 수": [8, 5, 7, 4]})
 
df = df.set_index("카테고리")
#(2)> 인덱스: ['이용안내','대출','시설','프로그램']  ← x축이 카테고리 이름이 됨
#(2)> 열: ['문서 수']  ← 카테고리가 열에서 빠지고 인덱스로 올라감
 
st.dataframe(df, use_container_width=True)
st.bar_chart(df)
# --8<-- [end:set_index]
 
#! set_index 는 "이 열을 이름표로 삼아라" 는 뜻.
#! 안 하면 x축에 0,1,2,3 이 뜨고, 카테고리는 막대로 그려지려다 에러가 남.
#! `use_container_width=True` — 표를 가로 폭에 꽉 채움. 없으면 좁게 나옴.
 
 
#== 레이아웃 — 화면 나누기
 
# --8<-- [start:layout]
# ① columns — 가로로 나란히
c1, c2 = st.columns(2)
c1.write("왼쪽")
c2.write("오른쪽")
 
# ② sidebar — 왼쪽 고정 패널
#(1)> st.sidebar.무엇 형태. 필터·설정을 여기 몰아두면 본문이 깔끔해짐
city = st.sidebar.selectbox("도시", ["서울", "부산"])
 
# ③ tabs — 탭으로 전환
overview_tab, detail_tab = st.tabs(["개요", "상세"])
with overview_tab:
    st.write("개요 내용")
with detail_tab:
    # ④ expander — 접었다 펴기
    with st.expander("원본 데이터", expanded=False):
        st.write("접힌 내용")
# --8<-- [end:layout]
 
#== @st.cache_resource — DB 연결이 매번 새로 생기는 걸 막기
#> rerun 때마다 파일 전체가 돈다 = DB 연결 코드도 매번 다시 실행됨.
 
# --8<-- [start:cache_resource]
# 처음 한 번만 실제로 실행되고, 그 뒤로는 저장된 연결을 그대로 돌려줌
@st.cache_resource
def get_connection(pw):
    return psycopg.connect(host="localhost", port=5432,
                           dbname="library", user="postgres", password=pw)
 
conn = get_connection(password)
# --8<-- [end:cache_resource]
 
#== session_state와 cache_resource의 차이

# --8<-- [end:cache_resource]
 `session_state 와 뭐가 다르냐 → 범위가 다름.`
 session_state   → 브라우저 탭(세션)마다 따로. 사용자별 값
 cache_resource  → 앱 전체에서 하나. 모든 세션이 공유 

 `그래서 담는 것도 다름`
 session_state  → 카운터, 대화 이력 (사람마다 달라야 하는 것)
 cache_resource → DB 연결, 모델 객체 (모두가 같은 걸 써도 되는 것)
 
 예전에 정리한 `lru_cache vs Redis` 와 같은 구분임.
 "도구는 공유해도 되고, 데이터는 사람마다 달라야 한다".
# --8<-- [end:cache_resource]

#! `@st.cache_data` 도 있음 — 조회 `결과`를 캐시함.
#! cache_resource → 연결·모델 같은 `물건`
#! cache_data     → 조회 결과·DataFrame 같은 `값`
#! 인자가 다르면 따로 캐시됨. lru_cache 랑 같은 방식.
 
 
#== 채팅 화면 — chat_message 와 chat_input
#> 이것도 결국 rerun + session_state 얘기임. 새로운 개념이 아님.
 
# --8<-- [start:chat]
import streamlit as st
 
st.title("도서관 안내 채팅")
 
# ① 대화 이력 보관함 만들기 (첫 실행에만)
if "messages" not in st.session_state:
    st.session_state.messages = []

# ② 지금까지의 이력을 전부 다시 그리기
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        #(1)> chat_message = 말풍선 하나를 만드는 컨테이너
        #(1)> ① 아바타(아이콘)를 왼쪽에 붙이고 ② 안쪽을 말풍선 모양으로 감쌈
        #(1)> "user" 면 사람 아이콘, "assistant" 면 로봇 아이콘이 자동으로 붙음
        #(1)> with 블록 안에서 그린 건 전부 그 말풍선 안으로 들어감
        st.markdown(message["content"])
        #(2)> 실제 글자를 쓰는 건 이 줄. chat_message 는 껍데기만 만듦

# ③ 새 입력 받기
prompt = st.chat_input("메시지를 입력하세요")

if prompt:
    # ④ 사용자 메시지 — 보관함에 넣고, 화면에도 그리기
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ⑤ 답변 — 똑같이 넣고 그리기
    answer = f"입력한 내용: {prompt}"
    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)
# --8<-- [end:chat]
 
#! ① session_state 전체 — 바깥은 dict. 'messages' 라는 키 하나가 있음
#! {'messages': [ ... ]}

#! ② st.session_state.messages — 그 값은 list
#! [
#!     {'role': 'user',      'content': '안녕'},
#!     {'role': 'assistant', 'content': '입력한 내용: 안녕'},
#!     {'role': 'user',      'content': '몇시에 열어?'},
#!     {'role': 'assistant', 'content': '입력한 내용: 몇시에 열어?'},
#! ]
 

#== 왜 이력을 매번 다시 그려야 하나
#> 이 부분이 제일 헷갈렸던 곳. 
 
# --8<-- [start:no_history]
# ② 이력 렌더 루프를 빼면 방금 친 것만 보이고 앞의 대화가 전부 사라짐
prompt = st.chat_input("메시지")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
# --8<-- [end:no_history]
 
#! 1회 입력 후 화면: ['첫 메시지']
#! 2회 입력 후 화면: ['둘째 메시지']   ← 첫 메시지가 사라짐
#! session_state → 데이터는 안 사라짐. `화면만` 사라지는 것.(rerun)
#! 그래서 매번 보관함을 처음부터 순회해서 다시 그려야 함. 
#! 이력 루프는 반드시 `chat_input 보다 위`에 둘 것.
#! 아래에 두면 새 메시지가 위에 오고 옛날 게 아래로 가서 순서가 뒤집힘.
 
  

#== 종합 연습 ① — form + session_state + metric
#> 제출할 때마다 횟수를 누적해서 metric 으로 보여주기.
 
# --8<-- [start:ex_survey_bad]
# 흔히 쓰는 방식 — 둘 중 하나가 항상 어긋남
st.metric("제출 횟수", st.session_state.submit_count)   # ① 먼저 그림
 
with st.form("survey"):
    name = st.text_input("이름")
    submitted = st.form_submit_button("제출")
 
if submitted:
    st.session_state.submit_count += 1   # ② 그린 뒤에 증가 → metric 이 옛날 값
    st.success("제출 완료")
    st.markdown(f"결과: {name}")
    st.rerun()                            # ③ 맞추려고 rerun → 결과가 지워짐
# --8<-- [end:ex_survey_bad]
 
#! `st.rerun() 있음`  → metric='1' 인데 success·결과가 `사라짐` (빈 화면)
#! `st.rerun() 없음`  → success·결과는 나오는데 metric 이 `'0'` (한 박자 늦음)
 
#! 왜 이러냐 → metric 을 form 보다 위에서 이미 그려버렸기 때문.
#! 그 아래에서 값을 올려봐야 화면은 이미 그려진 뒤임.
#! 그때는 submitted 가 False 라 success 블록을 아예 안 지나감.
 
# --8<-- [start:ex_survey_fix]
# st.empty() 로 자리만 잡아두고 나중에 채우기
if "submit_count" not in st.session_state:
    st.session_state.submit_count = 0

# 화면에 빈 자리를 하나 확보. 아직 아무것도 안 그림
slot = st.empty()
 
with st.form("survey"):
    name = st.text_input("이름")
    subject = st.selectbox("수강 과목", ["Python", "SQL", "Streamlit"])
    score = st.slider("만족도", 1, 5, 3)
    recommend = st.checkbox("추천합니다")
    submitted = st.form_submit_button("제출")
 
if submitted:
    st.session_state.submit_count += 1

# 아까 잡아둔 자리에 지금 값을 채움 → 위치는 위, 값은 최신
slot.metric("제출 횟수", st.session_state.submit_count)
 
if submitted:
    st.success("제출 완료")
    st.write({"이름": name, "과목": subject, "만족도": score, "추천": recommend})
# --8<-- [end:ex_survey_fix]
 
#! `st.empty()` = "여기에 자리 하나 잡아둬. 내용은 나중에 넣을게".
#! 반환된 slot 에 `.metric()`, `.write()` 를 부르면 그 자리에 그려짐.
#! 화면 순서와 계산 순서가 어긋날 때 쓰는 도구.
 
 
#== 종합 연습 ② 대시보드 — sidebar + 차트 연동
#> 사이드바 선택을 바꾸면 차트와 합계가 같이 바뀌는 구조.
 
# --8<-- [start:ex_dashboard]
import pandas as pd
import streamlit as st
 
st.set_page_config(page_title="미니 대시보드", layout="wide")
st.title("미니 대시보드")

# 여기서 값이 바뀌면 rerun → 아래가 전부 새 값으로 다시 계산됨
week = st.sidebar.selectbox("주차", ["1주차", "2주차"])

 
# 선택값을 key 로 쓰는 dict. 이게 sidebar 와 차트를 잇는 고리
weekly_sales = {
    "1주차": [18, 23, 17, 26, 22],
    "2주차": [21, 19, 24, 28, 25],
}
 
sales_df = pd.DataFrame({
    "요일": ["월", "화", "수", "목", "금"],
    "매출": weekly_sales[week],
}).set_index("요일")
 
c1, c2, c3 = st.columns(3)
c1.metric("방문자", 152, 23)
c2.metric("매출", f"{sum(weekly_sales[week])}만원")
c3.metric("처리 건수", 87, 5)
 
st.bar_chart(sales_df)
with st.expander("원본 데이터"):
    st.dataframe(sales_df, use_container_width=True)
# --8<-- [end:ex_dashboard]
 

 
 
#== 최종 정리
  
#! 하나만 기억하면 → `화면은 매번 새로 그려진다`.
#! 여기서 파생되는 함정 → `이미 그린 것은 못 고침`.
#! 그래서 metric 을 위에 그려놓고 아래에서 값을 올리면 한 박자 늦게 나옴.
#! st.empty() 로 자리를 잡아두거나, 계산을 먼저 하고 그리기.
 
#! 범위 세 가지를 구분해둘 것
#! 일반 변수      → 이번 rerun 동안만
#! session_state → 이 브라우저 탭이 살아있는 동안
#! cache_resource→ 앱이 떠 있는 동안 (모든 사용자 공유)
 

 