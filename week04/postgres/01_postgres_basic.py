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

#== 커서(Cursor)가 뭐냐
#> conn.cursor() 를 부르면 Cursor 객체가 나옴. 
#> `Connection` → "DB 에 연결돼 있다" 는 상태. commit·rollback·close 를 담당
#> `Cursor`     → "SQL 을 보내고 결과를 받아온다". execute·fetch 를 담당

# --8<-- [start:cursor_what]
conn = psycopg.connect(...)   # Connection 객체 — DB 와의 통로
cur = conn.cursor()           # Cursor 객체 — 그 통로로 일을 시키는 도구

# --8<-- [end:cursor_what]

#! `커서의 핵심은 `지금 어디까지 읽었는지 기억한다` 는 것.`
#! 결과가 100행이면 그걸 통째로 주는 게 아니라
#! 책갈피를 꽂아두고 "다음 거 줘" 할 때마다 한 칸씩 넘겨줌.
#! 그래서 conn 과 따로 있는 것. 책갈피를 들고 있을 뭔가가 필요해서.

# --8<-- [start:cursor_props]
cur.execute("SELECT 1")   # 반환값이 cur 자기 자신임
#(1)> 그래서 conn.cursor().execute(...).fetchall() 처럼 이어 쓸 수 있음

# 커서를 직접 for 로 돌려도 됨
#(2)> fetchall() 로 다 받지 않고 한 행씩 처리 → 결과가 클 때 메모리 절약
for row in cur:          
    print(row)

# with 로 쓰면 블록 끝에 자동으로 닫힘
#(3)> 블록을 나오면 c.closed 가 True
with conn.cursor() as c: 
    c.execute("SELECT count(*) FROM b")
    print(c.fetchone())

# 커서를 안 만들고 바로 쓸 수도 있음
#(4)> 내부에서 커서를 새로 만들어 돌려줌. 부를 때마다 다른 커서라 주의
conn.execute("SELECT 1") 
# --8<-- [end:cursor_props]


#== fetchone 과 fetchall 차이
#> 둘 다 결과를 꺼내는데, 반환 타입도 다르고 커서 위치도 다르게 움직임.

# --8<-- [start:fetch_basic]
cur.execute("SELECT id, title FROM b ORDER BY id")

# "첫 행" 이 아니라 "다음 행". 부를 때마다 책갈피가 한 칸씩 이동
cur.fetchone()   # (1, '1984')   ← 튜플 하나
cur.fetchone()   # (2, 'Moby')   ← 다음 행
cur.fetchone()   # (3, 'Farm')
cur.fetchone()   # None          ← 더 없으면 None

# 남은 걸 전부 꺼내고 책갈피를 끝으로 보냄. 다시 보려면 execute 를 다시
cur.execute("SELECT id, title FROM b ORDER BY id")
cur.fetchall()   # [(1,'1984'), (2,'Moby'), (3,'Farm')]  ← 리스트
cur.fetchall()   # []   ← 두 번째는 빈 리스트
# --8<-- [end:fetch_basic]

# --8<-- [start:fetch_return]
 메서드             반환 타입        결과가 없을 때      책갈피
 fetchone()       튜플 하나        None            한 칸 이동
 fetchall()       튜플의 리스트     빈 리스트 []      끝으로
 fetchmany(n)     튜플의 리스트     빈 리스트 []      n 칸 이동
# --8<-- [end:fetch_return]

#! `결과가 없을 때 반환값이 서로 다름.`
#! `fetchone` → `None`
#! `fetchall` → `[]`
#!  → 그래서 판별 코드가 달라짐
#!   row = cur.fetchone();  if row is None: ...
#!   rows = cur.fetchall(); if not rows: ...

#! 섞어 쓰면 fetchall 은 "남은 것" 만 줌.
#! fetchone() → (1,'1984')
#! fetchall() → [(2,'Moby'), (3,'Farm')]   ← 첫 행은 이미 꺼내서 없음

# --8<-- [start:fetchmany]
cur.execute("SELECT id, title FROM b ORDER BY id")
cur.fetchmany(2)   # [(1,'1984'), (2,'Moby')]
cur.fetchmany(2)   # [(3,'Farm')]           ← 남은 만큼만
# --8<-- [end:fetchmany]

#==  fetchone, fetchall, fetchmany 언제 쓰는지 
# --8<-- [start]
 fetchone  → 1건만 나오는 게 확실할 때 (id 로 조회, count 결과)
 fetchall  → 건수가 적고 목록을 다 쓸 때
 for 문     → 건수가 많아서 한 번에 메모리에 올리기 부담될 때
 fetchmany → 대량을 덩어리 단위로 처리할 때
# --8<-- [end]

#! `SELECT count(*)` 결과가 `(3,)` 이라 값만 쓰려면 `cur.fetchone()[0]` 임.
#! 한 칸짜리 튜플이라 [0] 을 빼먹기 쉬움.


#== fetch 로 자주 나는 에러

# --8<-- [start:fetch_error]
cur.execute("INSERT INTO b (title) VALUES ('X')")

# ProgrammingError: the last operation didn't produce records
#(1)> INSERT·UPDATE 는 돌려줄 행이 없음. fetch 하면 에러
#(1)> 넣은 행을 받고 싶으면 RETURNING 을 붙일 것
cur.fetchone()   
# --8<-- [end:fetch_error]

# --8<-- [start:rowcount]
cur.execute("UPDATE b SET title = title")

# INSERT·UPDATE·DELETE 결과를 확인할 때 이걸 봄
cur.rowcount    # 3   ← 영향받은 행 수

# 결과에 어떤 열이 있는지. 튜플만 봐서는 모를 때 유용
cur.execute("SELECT id, title FROM b LIMIT 1")
[d.name for d in cur.description]   # ['id', 'title']
# --8<-- [end:rowcount]


#== row_factory 를 바꾸면 fetch 반환 타입이 바뀜

# --8<-- [start:rowfactory_fetch]
from psycopg.rows import dict_row

conn = psycopg.connect(..., row_factory=dict_row)
#(1)> 기본은 튜플, dict_row 를 걸면 딕셔너리
#(1)> "하나냐 리스트냐" 구조는 그대로. 안에 든 것만 바뀜
cur = conn.cursor()

cur.execute("SELECT id, title FROM b ORDER BY id LIMIT 2")
cur.fetchone()   # {'id': 1, 'title': '1984'}
cur.fetchall()   # [{'id':1,...}, {'id':2,...}]
# --8<-- [end:rowfactory_fetch]

#! 열이 많아지면 row[0], row[3] 세는 게 실수의 근원이라 이게 편함.
#! sqlite3 의 `conn.row_factory = sqlite3.Row` 와 같은 역할.

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

