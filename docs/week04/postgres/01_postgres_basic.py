"""
title: PostgreSQL — psycopg
tags: [PostgreSQL]
"""

#== psycopg 로 접속하기

# --8<-- [start:connect]
# pip install "psycopg[binary]" python-dotenv

import os

import psycopg
from dotenv import load_dotenv

load_dotenv()
pw = os.environ["PGPASSWORD"]

# 도커로 띄웠어도 host 는 localhost 임
#(1)> -p 로 내 PC 포트에 연결해뒀으니까
conn = psycopg.connect(
    host="localhost", port=5432,
    dbname="library", user="postgres", password=pw,
)

cur = conn.cursor()
# --8<-- [end:connect]


#== placeholder 가 ? 가 아니라 %s

# --8<-- [start:placeholder]
cur.execute("INSERT INTO b (title, year) VALUES (%s, %s)", ("1984", 1949))

# --8<-- [end:placeholder]

#! 위 에러는 직접 돌려서 나온 메시지임.

#! `%s` 이지만  문자열 전용이 아님. 숫자·날짜·None 다 됨.
#! 타입에 따라 %d 로 바꾸거나 하지 말 것. 무조건 %s.


#== BIGSERIAL 과 REFERENCES

# --8<-- [start:schema]

# BIGSERIAL — 번호를 자동으로 매겨주는 타입. INSERT 할 때 id 를 생략하면 됨
# REFERENCES — 외래키. FOREIGN KEY(...) REFERENCES ... 의 짧은 형태
# CASCADE — 이 표를 참조하는 것들도 같이 정리하고 지움

cur.execute("""
DROP TABLE IF EXISTS rentals, members, books CASCADE;

CREATE TABLE books (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT, year INTEGER, genre TEXT
);
CREATE TABLE rentals (
    id BIGSERIAL PRIMARY KEY,
    book_id BIGINT REFERENCES books(id),
    member_id BIGINT REFERENCES members(id),
    rental_date TEXT, return_date TEXT
);
""")
conn.commit()

# --8<-- [end:schema]

#! BIGSERIAL 은 실제로 `bigint` 임 
#! books.id       → bigint
#! rentals.book_id → integer   ← 이게 어긋난 상태였음
#! 근데 가리키는 쪽과 가리켜지는 쪽 타입이 다르면 나중에 문제가 됨 → BIGINT 로 맞출 것.
#! INTEGER 로 참조해도 에러는 안 남 — Postgres 가 허용해 줌.

#== SQLite 와 다른 점 ① — commit 전에는 남이 못 봄
#> psycopg 는 autocommit 이 False 가 기본.

# --8<-- [start:tx]
A = psycopg.connect()
B = psycopg.connect()

# A 가 넣었지만 commit 을 안 해서 B 에게는 아직 안 보임
A.execute("INSERT INTO b (title) VALUES ('COMMIT TEST')")
B.execute("SELECT count(*) FROM b WHERE title='COMMIT TEST'")   # → 0

# commit 후에야 보임
A.commit()
B.execute("SELECT count(*) FROM b WHERE title='COMMIT TEST'")   # → 1
# --8<-- [end:tx]


#! 내 화면에서는 commit 전에도 보임. 내 트랜잭션 안에서는 반영돼 있으니까.
#! "나만 보이는 임시 상태" 라고 생각하면 됨.


#== SQLite 와 다른 점 ② — 에러가 나면 그 뒤가 전부 막힘


# --8<-- [start:aborted]
cur.execute("SELECT * FROM 없는표") # UndefinedTable

cur.execute("SELECT 1")   # InFailedSqlTransaction: current transaction is aborted
#(1)> 멀쩡한 쿼리인데도 실패함. 트랜잭션이 통째로 잠긴 상태라서

conn.rollback()
#(2)> rollback 을 해야 잠금이 풀림
cur.execute("SELECT 1")   # (1,)  ← 이제 됨
# --8<-- [end:aborted]


#! 습관 → try/except 로 감싸고 except 에서 rollback 하기.
#! `except Exception: conn.rollback(); raise`


#== SQLite 와 다른 점 ③ — CREATE TABLE 도 롤백됨

# --8<-- [start:ddl_tx]
conn.execute("CREATE TABLE tmp_tbl (id INT)")
conn.rollback()

conn.execute("SELECT * FROM tmp_tbl")   # UndefinedTable: relation "tmp_tbl" does not exist
# --8<-- [end:ddl_tx]

#! 표를 만들었으면 반드시 commit 을 해야 함.


#== SQLite 와 다른 점 ④ — 외래키를 기본으로 강제함

# --8<-- [start:fk]
# books 에 id=999가 없을 경우 아래 실행 시 거부됨
cur.execute("INSERT INTO rentals (book_id) VALUES (999)")
#(1)> ForeignKeyViolation: violates foreign key constraint "rentals_book_id_fkey"

# --8<-- [end:fk]

#! SQLite 는 PRAGMA foreign_keys = ON 을 켜야 검사했는데 Postgres 는 기본으로 함.
#! 그래서 넣는 순서가 중요해짐. books·members 를 먼저 넣고 rentals 를 넣어야 함.
#! 반대로 하면 "참조 대상이 없다" 고 거부됨.


#== SQLite 와 다른 점 ⑤ — GROUP BY 가 엄격함

# --8<-- [start:groupby]
# GroupingError: column "t.b" must appear in the GROUP BY clause
#(1)>  SELECT 에 쓴 비집계 열은 GROUP BY 에도 반드시 있어야 함
SELECT a, b, count(*) FROM t GROUP BY a;

SELECT a, b, count(*) FROM t GROUP BY a, b;   -- OK
SELECT a, max(b), count(*) FROM t GROUP BY a; -- OK (집계 함수로 감싸도 됨)
# --8<-- [end:groupby]


#== 따옴표 규칙 — 큰따옴표와 작은따옴표가 다름
#> 파이썬에서는 "a" 와 'a' 가 같은데 SQL 에서는 완전히 다름.

# --8<-- [start:quotes]
# 작은따옴표 = 문자열 값
# 큰따옴표   = 식별자(열 이름·표 이름)

SELECT 'Alice';     -- ('Alice',)  → 문자열
SELECT "Alice";     -- UndefinedColumn: column "Alice" does not exist

# --8<-- [end:quotes]



#! 더 중요한 것 → 따옴표 없이 쓰면 전부 소문자로 바뀜.
# --8<-- [start:case]
# 대문자로 썼는데 소문자로 접힘
CREATE TABLE Books2 (Id INT, Title TEXT);   -- 실제로 저장된 이름: books2

# 실제로 저장된 이름: Books3
CREATE TABLE "Books3" (id INT);

# 큰따옴표로 만들면 대문자가 유지되는데, 그 뒤로 매번 따옴표를 써야 함
SELECT * FROM Books3;   -- UndefinedTable: relation "books3" does not exist
# --8<-- [end:case]

#! 결론 → 표 이름·열 이름은 처음부터 소문자에 밑줄로 쓸 것 (`book_id`).

#== 표 목록을 파이썬에서 보기
#> psql 의 \dt 를 psycopg 에서는 못 씀. 대신 시스템 표를 조회함.

# --8<-- [start:tables]
# information_schema = DB 가 자기 구조를 담아둔 표. 표준 규격
# table_schema='public' 을 안 걸면 시스템 표 수백 개가 딸려 나옴

cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")

print(cur.fetchall())
# --8<-- [end:tables]


#== 결과를 이름으로 받기 — dict_row

# --8<-- [start:dict_row]
from psycopg.rows import dict_row

conn = psycopg.connect(..., row_factory=dict_row)
row = conn.execute("SELECT id, title FROM b LIMIT 1").fetchone()
print(row)            # {'id': 1, 'title': 'Moby'}
print(row["title"])   # Moby
#(1)> 기본은 튜플이라 row[0], row[1]. 열이 많아지면 세다가 실수함
# --8<-- [end:dict_row]


#== SQLite ↔ Postgres 차이 정리

# --8<-- [start:diff]
                   SQLite              Postgres(psycopg)
자리표시자             ?                   %s
자동 번호           INTEGER PRIMARY       KEY  BIGSERIAL
외래키             기본 꺼짐(PRAGMA)       기본 켜짐
GROUP BY           느슨함                엄격함
에러 후            그냥 계속 가능           rollback 전까지 전부 막힘
CREATE TABLE       롤백 안 됨(대체로)      롤백됨
이름 대소문자       구분 안 함(대체로)        소문자로 접힘
서버               없음. 파일 하나         별도 프로세스. 여러 연결
# --8<-- [end:diff]

