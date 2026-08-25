"""
title: Text-to-SQL — 자연어 질문을 SQL 로 바꾸기
tags: [text_to_sql]
"""

#== 무엇을 만드는 건가
#> 사용자는 표 이름·열 이름을 모름. 그냥 한국어로 물어봄.
#> LLM 이 그 질문을 SQL 로 바꿔주고, 우리가 검사한 뒤 실행함.

# --8<-- [start:flow]
 사용자 질문  "책은 모두 몇 권인가요?"
     ↓
 LLM 이 DB 스키마를 참고해 SQL 생성
     ↓
  읽기 전용 SQL 인지 검사      ← 여기가 이 실습의 핵심
     ↓
 PostgreSQL 에서 실행
     ↓
 직접 작성한 검증 SQL 과 결과 비교
# --8<-- [end:flow]

#! 왜 검증 단계가 필요하냐 →
#! LLM 은 `없는 표 이름을 지어내거나` 질문 뜻을 잘못 알아들을 수 있음.
#! 게다가 SQL 은 실행되면 데이터를 지울 수도 있음. 되돌릴 수 없음.

#== 준비 — SQLDatabase 와 체인 만들기

# --8<-- [start:setup]
# pip install -U langchain langchain-openai langchain-community sqlalchemy "psycopg[binary]"

from langchain_classic.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI

# SQLAlchemy 형식의 접속 주소. psycopg 로 직접 연결할 때와 형식이 다름
#(1)> `postgresql+psycopg` — 어떤 드라이버를 쓸지까지 적음
library_uri = f"postgresql+psycopg://postgres:{password}@localhost:5432/library"
#(5)> import URL
#(5)> library_uri = URL.create(
#(5)>        drivername="postgresql+psycopg",
#(5)>        username="postgres",
#(5)>        password=os.environ["password"],
#(5)>        host="localhost",
#(5)>        port=5432,
#(5)>        database=library, )
            


db = SQLDatabase.from_uri(
    library_uri,
    include_tables=["books", "members", "rentals"],
    #(2)> 이 3개만 LLM 에게 보여줌. 안 적은 표는 존재 자체를 모름
    sample_rows_in_table_info=2,
    #(3)> 표마다 실제 데이터 2행을 예시로 같이 보냄
    #(3)> 열 이름만 보는 것보다 값을 보면 SQL 을 더 잘 만듦
    #(3)> `장점` → 값의 형태를 보고 더 정확한 SQL 을 만듦 (날짜 형식 등)
    #(3)> `단점` → `실제 데이터가 OpenAI 로 나감`. 개인정보가 있으면 0 으로 둘 것
)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

query_chain = create_sql_query_chain(llm, db)
# --8<-- [end:setup]

#! `SQLDatabase` 가 하는 일 → DB 에 접속해서 `표 구조를 읽어옴`.
#! CREATE TABLE 문 같은 걸 만들어서 프롬프트에 넣어줌.
#! `include_tables` 는 보안 장치이기도 함.
#! 회원 비밀번호가 든 표를 안 적으면 LLM 이 그 표를 아예 모름.

#== create_sql_query_chain 내부
#> `create_sql_query_chain` 은 SQL `문자열만` 돌려줌. 실행은 안 함.
# --8<-- [start]

create_sql_query_chain(
  llm: BaseLanguageModel,
  db: SQLDatabase,
  prompt: BasePromptTemplate | None = None,
  k: int = 5,
  *,
  get_col_comments: bool | None = None
) -> Runnable[SQLInput | SQLInputWithTables | dict[str, Any], str]

# --8<-- [end]

#== 왜 실행 체인을 안 쓰고 직접 sql 생성만 하는 체인을 사용하는 지
#> LangChain 에는 SQL 을 만들고 바로 실행까지 하는 도구가 있음.
#> 근데 그러면 `LLM 이 만든 SQL 이 그대로 DB 에 날아감` → 되돌릴 수 없음

#! 왜 그게 문제냐 →
#! DELETE·DROP 은 실행되면 `되돌릴 수 없음`. 백업이 없으면 그걸로 끝.
#! LLM 이 악의가 없어도 질문을 잘못 알아들으면 그럴 수 있고,
#! 사용자가 일부러 "모든 책을 삭제해줘" 라고 할 수도 있음.

# --8<-- [end]
[핵심] → 생성과 실행 사이에 `사람이 짠 검사`를 끼워넣는 것.
 이 실습에서 만드는 방어막이 3겹임
 ① clean_sql        — 응답에서 SQL 만 뽑아냄
 ② validate_read_only_sql — 조회 SQL 인지 검사
 ③ SET LOCAL TRANSACTION READ ONLY — DB 쪽에서 한 번 더 막음
# --8<-- [end]

#== ① clean_sql — 응답에서 SQL 만 뽑아내기
#> LLM 응답에는 SQL 말고 다른 게 섞여 나옴.

# --8<-- [start:clean_sql]
import re

def clean_sql(raw: str) -> str:
    sql = raw.strip()

    # ```sql ... ``` 코드블록 껍데기를 벗김
    #(1)> \x60 은 백틱(`) 문자의 16진수 표현. 코드 안에 백틱을 직접 못 써서 이렇게 씀
    sql = re.sub(r"^\s*\x60\x60\x60(?:sql)?\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"\s*\x60\x60\x60\s*$", "", sql)

    # "SQLQuery:" 같은 라벨 제거
    sql = re.sub(r"^\s*(SQLQuery|SQL)\s*:\s*", "", sql, flags=re.IGNORECASE)

    # 설명 문장이 앞에 붙어 있어도 SELECT/WITH 부터 잘라냄
    #(3)> WITH 도 포함하는 이유 → CTE 로 시작하는 SQL 도 조회문이라서
    start = re.search(r"\b(WITH|SELECT)\b", sql, flags=re.IGNORECASE)
    if start is None:
        raise ValueError("SELECT 또는 WITH로 시작하는 SQL을 찾지 못했습니다.")
    sql = sql[start.start():].strip()

    # 여러 문장을 한 번에 못 보내게. "SELECT 1; DROP TABLE books" 차단
    statements = [part.strip() for part in sql.split(";") if part.strip()]
    if len(statements) != 1:
        raise ValueError("SQL은 한 문장만 허용합니다.")

    return statements[0] + ";"
# --8<-- [end:clean_sql]

# --8<-- [start:clean_sql_trap]
# ① 문자열 안에 세미콜론이 있으면 멀쩡한 SQL 이 막힘
#(1)> ValueError: SQL은 한 문장만 허용합니다.
#(1)>   → split(";") 이 따옴표 안까지 잘라버림
clean_sql("SELECT * FROM books WHERE title = 'a;b'")

# ② 설명에 'SELECT' 라는 단어가 있으면 거기부터 잘림
#(2)> 'SELECT 절을 써서 세어봅시다.\nSELECT count(*) FROM books;'
#(2)>   → 앞의 설명이 SQL 에 섞여 들어감. 실행하면 문법 에러
clean_sql("SELECT 절을 써서 세어봅시다.\nSELECT count(*) FROM books")
# --8<-- [end:clean_sql_trap]

#! 정규식으로 SQL 을 다루는 건 원래 한계가 있음.
#! 제대로 하려면 `SQL 파서`를 써야 함 (sqlparse, sqlglot 같은 것).


#== ② validate_read_only_sql — 쓰기 키워드 검사

# --8<-- [start:validate]
WRITE_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|COPY|CALL|DO)\b",
    #(1)> \b = 단어 경계. UPDATE 라는 '단어' 만 찾고 updated_at 은 안 걸림
    #(1)> re.IGNORECASE = insert · Insert · INSERT 를 전부 잡음
    flags=re.IGNORECASE,
)

def validate_read_only_sql(sql: str) -> None:
    if re.match(r"^\s*(SELECT|WITH)\b", sql, flags=re.IGNORECASE) is None:
        raise ValueError("조회 SQL만 실행할 수 있습니다.")
    if WRITE_KEYWORDS.search(sql):
        raise ValueError("데이터를 변경하는 SQL은 실행할 수 없습니다.")
# --8<-- [end:validate]

#! `\b 있음`  "SELECT * FROM updated_at_log" → 안 걸림 (정상)
#! `\b 없음`  같은 SQL              → 'update' 가 걸려서 `막힘` (오탐)


#== ③ SET LOCAL TRANSACTION READ ONLY — DB 쪽 방어막

# --8<-- [start:read_only]
import psycopg

DB_CONFIG = { "host": "localhost",    
              "port": 5432,    
              "dbname": "library",    
              "user": "postgres",    
              "password": os.environ["PGPWD"]  
              "connect_timeout": 5,}

conn = psycopg.connect(**DB_CONFIG)

def execute_read_only(sql: str):
    validate_read_only_sql(sql)

    # 트랜잭션 시작. 예외가 나면 psycopg 가 알아서 rollback
    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute("SET LOCAL TRANSACTION READ ONLY")
            #(3)> DB 쪽 2차 방어. 이 트랜잭션 안에서는 쓰기를 아예 거부함
            #(3)> LOCAL = 이 트랜잭션에서만. 끝나면 원래대로 돌아감
            cur.execute(sql)
            return cur.fetchall()
# --8<-- [end:read_only]


#== 질문을 돌려보기

# --8<-- [start:run]
questions = [
    "책은 모두 몇 권인가요?",
    "Alice가 빌린 책의 제목을 알려주세요.",
    "장르별 책 수를 세어주세요.",
    "아직 반납하지 않은 책은 몇 권인가요?",
    "회원별 대여 횟수를 많은 순으로 알려주세요.",
]

generated_sql = {}
for question in questions:
    raw_sql = query_chain.invoke({"question": question})
    #(1)> 여기서 OpenAI 호출. SQL 문자열이 돌아옴
    sql = clean_sql(raw_sql)
    generated_sql[question] = sql
    print("질문:", question)
    print(sql, "\n")
# --8<-- [end:run]


#== 정리

#! `SQLDatabase `      — DB 에서 표 구조를 읽어 프롬프트에 넣어줌
#! `include_tables`    — LLM 에게 보여줄 표를 제한. 보안 장치이기도 함
#! `sample_rows`       — 실제 데이터를 예시로 보냄. 정확해지지만 데이터가 외부로 나감
#! `create_sql_query_chain` — SQL 문자열만 만들어 줌. 실행은 안 함

#! `방어막 3겹`
#! ① clean_sql              응답에서 SQL 만 뽑고 한 문장인지 확인
#! ② validate_read_only_sql SELECT/WITH 로 시작하고 쓰기 키워드가 없는지
#! ③ READ ONLY 트랜잭션      DB 쪽에서 쓰기를 아예 거부

