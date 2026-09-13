"""
title: DB 기초 — RDBMS 개념
tags: [sqlite]
"""

#== 테이블 — 행과 열
#> 관계형 DB 는 데이터를 표(테이블) 로 저장함. 표는 행과 열로 이루어짐.

# --8<-- [start:table]
          ┌─ 열(column) = 속성. 이름과 타입을 미리 정해 둠
          ▼
     name(TEXT)  math(INT)  science(INT)
   ┌────────────────────────────────────
   │  홍길동        30         20        ← 행(row) = 레코드. 데이터 한 건
   │  박철수        70         65        ← 행
   │  이민지        95         88        ← 행
# --8<-- [end:table]


#! 행(row) = 레코드 = 가로줄 = "홍길동의 성적 한 건"
#! 열(column) = 속성 = 세로줄 = "math 라는 항목" 
#! 타입(INTEGER, TEXT)을 정해두는 건 `열` 임.
#! 스키마(schema) = 어떤 테이블에 어떤 열이 있고 각 열의 타입이 뭔지 정한 설계도.



#== 키 — 행을 구분하고 표끼리 연결하기

#! 기본키(PK, Primary Key) = 행 하나를 유일하게 구분하는 열.
#! 조건 두 개 → 중복 불가(UNIQUE) + 빈 값 불가(NOT NULL).
#! 외래키(FK, Foreign Key) = 다른 표의 키를 가리키는 열.


# --8<-- [start:fk]

CREATE TABLE rentals (
    id INTEGER PRIMARY KEY,
    book_id INTEGER,
    member_id INTEGER,
    rental_date TEXT,
    return_date TEXT,
    # "book_id 에 들어갈 값은 books.id 에 실제로 있는 값이어야 한다"
    FOREIGN KEY(book_id) REFERENCES books(id),
    FOREIGN KEY(member_id) REFERENCES members(id)
);

# --8<-- [end:fk]


# --8<-- [start:fk_pragma]
import sqlite3

conn = sqlite3.connect("library.db")

# foreign_keys=OFF (기본) → 존재하지 않는 book_id 999 를 넣어도 그냥 들어감
# foreign_keys=ON        → IntegrityError: FOREIGN KEY constraint failed
conn.execute("PRAGMA foreign_keys = ON")
#(1)> 연결할 때마다 켜 줘야 함. 연결이 새로 생기면 다시 꺼짐


# --8<-- [end:fk_pragma]


#! 즉 FOREIGN KEY 를 CREATE TABLE 에 써놓기만 하면 그냥 메모일 뿐임.
#! PRAGMA 로 켜야 진짜 검사를 함.
#! MySQL·PostgreSQL 은 기본으로 켜져 있음. SQLite 만 호환성 때문에 꺼져 있음.


#== SQL 의 세 갈래
#> SQL(Structured Query Language) = DBMS 에게 요청을 보내는 언어.

# --8<-- [start:sql_kinds]
-- DDL (Data Definition Language) — 표의 구조(설계도)를 다룸
CREATE TABLE / ALTER TABLE / DROP TABLE

-- DML (Data Manipulation Language) — 표 안의 데이터를 다룸
SELECT / INSERT / UPDATE / DELETE

-- TCL (Transaction Control Language) — 작업을 확정하거나 되돌림
COMMIT / ROLLBACK
# --8<-- [end:sql_kinds]



#== COMMIT — 저장 확정 버튼
#> INSERT / UPDATE / DELETE 는 commit 을 해야 파일에 실제로 반영됨.

# --8<-- [start:commit]
import sqlite3

# DB 연결 -> Connection 객체 반환. 파일이 없으면 새로 만듦
conn = sqlite3.connect('new.db')

# .cursor() -> Cursor 객체 반환. SQL 을 실어 나르고 결과를 받는 손잡이
cur = conn.cursor()

cur.execute("INSERT INTO scores VALUES ('홍길동', 30, 20, 10)")

conn.commit()

# --8<-- [end:commit]


#! 왜 이렇게 만들었냐 → 여러 작업을 "전부 되거나 전부 안 되거나" 로 묶기 위해서.
#! 계좌이체가 대표 예시. A 에서 빼고 B 에 넣는 두 작업 중 하나만 되면 큰일남.
#! 둘 다 하고 나서 commit → 중간에 터지면 rollback 으로 통째로 취소.


#== 파이썬에서 SQL 실행하기 — 연결과 커서

# --8<-- [start:connect]
import sqlite3

conn = sqlite3.connect("score.db")
#(1)> 파일이 없으면 새로 만듦. 경로는 "지금 실행 중인 위치" 기준
#(1)> sqlite3.connect(":memory:") 로 하면 RAM 에만 만듦 (연습·테스트용)

cur = conn.cursor()
#(2)> 커서 = SQL 을 실어 보내고 결과를 받아오는 손잡이
#(2)> conn 은 "DB 와의 연결", cur 은 "그 연결로 일을 시키는 도구"

# ... 작업 ...

conn.commit()
conn.close()
# --8<-- [end:connect]

#! conn 과 cur 을 왜 나누냐 → 커서는 "지금 어디까지 읽었는지" 를 기억함.
#! 결과를 하나씩 꺼내려면 그 위치를 들고 있을 뭔가가 필요해서 따로 있는 것.


#== execute 계열 세 가지

# --8<-- [start:execute]

# ① execute — SQL 한 문장
cur.execute("INSERT INTO scores VALUES (?, ?, ?, ?)", ("홍길동", 30, 20, 10))

# ② executemany — 같은 SQL 을 값 목록만큼 반복
#(1)> 같은 문장 × 여러 값. for 문으로 execute 를 도는 것보다 빠름
cur.executemany(
    "INSERT INTO scores VALUES (?, ?, ?, ?)",
    [
        ("박철수", 70, 65, 90),
        ("이민지", 95, 88, 76),
    ],
)

# ③ executescript — 서로 다른 문장 여러 개를 세미콜론으로 이어서
# (2)> placeholder(?) 를 못 씀 → 값이 고정된 스크립트 전용
cur.executescript("""
DROP TABLE IF EXISTS scores;
CREATE TABLE scores (
    name TEXT PRIMARY KEY,
    math INTEGER,
    science INTEGER,
    english INTEGER
);
INSERT INTO scores VALUES ('홍길동', 30, 20, 10);
""")

# --8<-- [end:execute]

#! executescript 는 실행 전에 대기 중인 트랜잭션을 알아서 commit 해버림.
#! INSERT 후 commit 없이 executescript 를 부르고 연결을 닫았는데 그 INSERT 가 파일에 남아 있었음.
#! → rollback 으로 되돌릴 생각이었다면 그 기회가 사라짐. 초기화용으로만 쓸 것.


#== placeholder(?) — 값을 안전하게 넘기기
#> SQL 문자열에 값을 직접 붙이지 말고 `?` 자리를 만들어 두고 따로 넘기는 방식.

# --8<-- [start:placeholder]
# 문자열을 직접 이어붙이기
#(1)> name 에 `' OR '1'='1` 같은 값이 들어오면 조건이 통째로 무력화됨
#(1)> 이게 SQL 인젝션. 로그인 우회·전체 데이터 유출로 이어짐
name = "홍길동"
cur.execute(f"SELECT * FROM scores WHERE name = '{name}'")

# placeholder 사용
#(2)> ? 자리에 들어가는 건 무조건 "값" 으로만 취급됨
#(2)> 안에 따옴표나 SQL 문법이 섞여 있어도 그냥 글자로 처리됨
cur.execute("SELECT * FROM scores WHERE name = ?", ("홍길동",))

# --8<-- [end:placeholder]

#! 콤마를 빠뜨리기 쉬움. `("홍길동")` 은 튜플이 아니라 그냥 문자열임.
#! → 값이 하나여도 `("홍길동",)` 처럼 콤마를 꼭 붙일 것.

#! placeholder 는 "값" 자리에만 쓸 수 있음. 표 이름·열 이름에는 못 씀.
#! `cur.execute("SELECT * FROM ?", ("t",))` → OperationalError: near "?": syntax error


#== 결과 꺼내기 — fetchone / fetchall

# --8<-- [start:fetch]
cur.execute("SELECT name, math FROM scores")

# fetchone() → "첫 행" 이 아니라 "다음 행" 을 하나씩 꺼내는 것. 커서가 한 칸씩 이동함
cur.fetchone()   # ('홍길동', 30)
cur.fetchone()   # ('박철수', 70)
cur.fetchone()   # ('이민지', 95)
cur.fetchone()   # None  ← 더 없으면 None


cur.execute("SELECT name, math FROM scores")
cur.fetchall()   # [('홍길동', 30), ('박철수', 70), ('이민지', 95)]
cur.fetchall()   # []  ← 두 번째는 빈 리스트
# --8<-- [end:fetch]

#! 커서가 책갈피처럼 위치를 기억하고 한 칸씩 넘어가는 구조임.
#! fetchall 도 두 번 부르면 두 번째는 `[]`. 
#! 결과를 여러 번 쓸 거면 변수에 담아둘 것 → `rows = cur.fetchall()`


#== 결과를 이름으로 꺼내기 — row_factory
#> 기본은 튜플이라 row[0], row[1] 로 접근해야 함. 열 순서가 바뀌면 다 깨짐.

# --8<-- [start:row_factory]
# 연결에 걸어두면 이후 결과가 이름으로 접근 가능해짐
conn.row_factory = sqlite3.Row

row = conn.execute("SELECT * FROM scores").fetchone()
print(row["name"], row["math"])   # 홍길동 30
# --8<-- [end:row_factory]

#! row["name"] = 홍길동 / row["math"] = 30 
#! 열이 많아지면 튜플 인덱스를 세는 게 실수의 근원이라 이게 편함.


#== SELECT 기본 구조

# --8<-- [start:select]
SELECT name, math          -- ① 어떤 열을 볼지
FROM scores                -- ② 어느 표에서
WHERE math >= 60           -- ③ 어떤 조건의 행만
ORDER BY math DESC         -- ④ 어떤 순서로 (DESC 내림차순, ASC 오름차순)
LIMIT 3;                   -- ⑤ 몇 개만

-- 자주 쓰는 WHERE 조건
WHERE math BETWEEN 60 AND 80      -- 범위 (양끝 포함)
WHERE genre IN ('Fiction', 'Dystopian')   -- 여러 값 중 하나
WHERE title LIKE '%Farm%'          -- 부분 일치 (% = 아무 글자 여러 개)
# --8<-- [end:select]


#== NULL 은 "값이 없음" 이라 비교가 안 됨
#> 아직 값이 없는 칸. 파이썬 None 이 NULL 로 들어감.

# --8<-- [start:null]
# 아직 반납하지 않은 대여 기록(id) 찾기
SELECT id FROM rentals WHERE return_date = NULL;   -- 결과: 없음 (빈 목록)

# NULL 을 찾을 때는 반드시 IS NULL / IS NOT NULL
SELECT id FROM rentals WHERE return_date IS NULL;  -- 결과: 제대로 나옴
# --8<-- [end:null]

#! `WHERE return_date = NULL`  → []      (아무것도 안 나옴)
#! `WHERE return_date IS NULL` → [(2,)]  (제대로 나옴)

#! ★ 더 헷갈리는 것 → `WHERE return_date != '20240215'` 도 NULL 행을 빼고 나옴.
#! "20240215 가 아닌 것" 을 찾았는데 NULL 인 행이 안 나옴. 
#! `NULL 은 "모르는 값" 이라 같은지도 다른지도 판단이 안 되기 때문.`

#! COUNT 도 다름
#! `COUNT(*)`   → 2  (행 개수를 셈)
#! `COUNT(return_date)` → 1  (NULL 이 아닌 값만 셈)


#== INTEGER PRIMARY KEY 는 자동으로 번호를 매김

# --8<-- [start:autoincrement]

CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT);
# id 를 안 넣었는데도 1, 2, 3 이 자동으로 들어감
INSERT INTO t (name) VALUES ('a'), ('b'), ('c');
# --8<-- [end:autoincrement]


#! SQLite 에서 `INTEGER PRIMARY KEY` 는 특별 취급이라 자동 채번이 됨.


#== UPDATE / DELETE — WHERE 를 빠뜨리면

# --8<-- [start:danger]
# WHERE 가 없으면 모든 행의 math 가 100 이 됨
UPDATE scores SET math = 100;

#  WHERE 가 없으면 모든 행이 지워짐
DELETE FROM scores;
# --8<-- [end:danger]

#! 습관 → 지우거나 고치기 전에 같은 WHERE 로 SELECT 를 먼저 돌려볼 것.
#! `SELECT * FROM scores WHERE name='홍길동'` 으로 대상 확인 → 그 다음 DELETE.
#! commit 전이면 rollback 으로 살릴 수 있음. commit 후면 못 되돌림.


#== 정리

#! execute = 한 문장 · executemany = 같은 문장 여러 값 · executescript = 여러 문장
#! ? = 값을 안전하게 넘기는 자리 (값에만, 표 이름엔 못 씀)
#! fetchone = 다음 한 행 · fetchall = 남은 전부 (커서가 소진됨)
#! commit 안 하면 저장 안 됨
