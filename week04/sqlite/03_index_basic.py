"""
title: 인덱스
tags: [sqlite]
"""

#== 인덱스가 뭐냐
#> 처음부터 한 장씩 넘기느냐, 색인에서 페이지를 바로 찾느냐의 차이.

#! DB 용어
#! SCAN(전체 훑기)   = 표를 처음부터 끝까지 다 봄. 인덱스가 없을 때
#! SEARCH(색인 탐색) = 색인을 보고 바로 그 자리로 감. 인덱스가 있을 때

#! 인덱스는 원래 표와 별개로 DB 가 따로 만들어 두는 자료구조임.
#! "member_id 값 → 그 행이 있는 위치" 를 정렬해서 담아 둔 것.


#== 문법 — 만들기 · 보기 · 지우기

# --8<-- [start:syntax]
# index 만들기
#(1)> idx_member 는 내가 붙이는 이름. idx_표_열 형태가 흔한 관례
CREATE INDEX idx_member ON rentals(member_id);


# index 중복 없이 만들기 
CREATE UNIQUE INDEX idx_email ON members(email);

# 여러 열을 묶어서 (복합 인덱스)
CREATE INDEX idx_bm ON rentals(book_id, member_id);

# 목록 보기
SELECT name FROM sqlite_master WHERE type='index';

# 지우기
DROP INDEX idx_member;
# --8<-- [end:syntax]

#! CREATE INDEX 는 대부분의 RDBMS 에서 똑같이 씀. SQLite 전용 문법이 아님.


#== 눈으로 확인하기 — EXPLAIN QUERY PLAN
#> 이 질의를 DB 가 '어떻게' 처리할지 미리 보여주는 명령.

# --8<-- [start:explain]
QUERY = "SELECT * FROM rentals WHERE member_id = 2"

plan = cur.execute("EXPLAIN QUERY PLAN " + QUERY).fetchall()

# 인덱스 전 → SCAN rentals
print(plan[0][3])
#(1)> 결과가 여러 줄일 수 있어서 [0], 설명 문구가 4번째 칸이라 [3]

# 인덱스 후 → SEARCH rentals USING INDEX idx_member (member_id=?)
cur.execute("CREATE INDEX idx_member ON rentals(member_id)")

# --8<-- [end:explain]

#! 표가 작으면 시간 차이가 눈에 안 보임. 그래서 시간 대신 실행계획으로 확인함.

#== PK 는 인덱스를 안 만들어도 이미 빠름

# --8<-- [start:pk]
SELECT * FROM rentals WHERE id = 100;
# 결과 SEARCH rentals USING INTEGER PRIMARY KEY (rowid=?)
# --8<-- [end:pk]

#! 확인해보니 PK 에는 인덱스가 자동으로 딸려 있음.
#! UNIQUE 를 건 열도 마찬가지. 따로 CREATE INDEX 를 할 필요 없음.

#! 그럼 어디에 걸어야 하냐 → WHERE·JOIN 에 자주 쓰는데 PK 가 아닌 열.
#! rentals.member_id, rentals.book_id 같은 `외래키 열이 1순위`.
#! JOIN 은 결국 그 열로 짝을 찾는 일이라서 인덱스 효과가 큼.


#==  인덱스가 있어도 안 타는 경우
#> 인덱스는 "열의 값" 을 정렬해둔 것이라, 값을 그대로 안 쓰면 무용지물임.

# --8<-- [start:not_used]
-- ① 열에 함수를 씌우면
#(1)> 인덱스에는 원래 값이 들어있는데 함수를 거친 값은 거기 없음
WHERE rental_date = '20240100'                  -- SEARCH (탐)
WHERE substr(rental_date, 1, 4) = '2024'        -- SCAN   (못 탐)


-- ② LIKE 앞에 % 가 붙으면
#(2)> 앞글자를 모르면 색인에서 시작점을 못 찾음. 사전에서 중간 글자로 찾는 격
WHERE rental_date LIKE '%100'                   -- SCAN

-- ③ 범위 비교로 바꾸면 탐
#(3)> 앞부분이 정해지면 색인에서 구간을 잡을 수 있음
WHERE rental_date >= '2024' AND rental_date < '2025'   -- SEARCH

# --8<-- [end:not_used]


#! 참고 → SQLite 에서는 `LIKE '2024%'` 도 기본 인덱스로는 SCAN 이 나옴.
#! LIKE 가 기본적으로 대소문자를 무시하는데 인덱스는 구분해서 정렬돼 있어서 그럼.
#! 어차피 위 ③처럼 범위 비교로 바꾸는 게 더 확실함.

#! 감 잡는 법 → "WHERE 왼쪽에 열 이름만 딱 있는가?"
#! 열을 가공했으면 인덱스는 못 씀.


#== 복합 인덱스는 순서가 중요함
#> (book_id, member_id) 로 만들면 book_id 가 앞, member_id 가 뒤.

# --8<-- [start:composite]
CREATE INDEX idx_bm ON rentals(book_id, member_id);

WHERE book_id = 3                        -- SEARCH  (첫 열이라 탐)
WHERE member_id = 2                      -- SCAN    (둘째 열만으론 못 탐)
WHERE book_id = 3 AND member_id = 2      -- SEARCH  (둘 다 씀)
# --8<-- [end:composite]


#! 이유 → 전화번호부가 (성, 이름) 순으로 정렬된 것과 같음.
#! "김" 으로 시작하는 사람은 금방 찾는데, 이름이 "철수" 인 사람은 다 뒤져야 함.
#! 그래서 복합 인덱스는 자주 쓰는 조건을 앞에 둬야 함.


#== 인덱스는 '정렬된 별도 사본' 임
#> 열에 붙은 표시가 아님. 따로 만들어진 물건이 하나 더 생기는 것.
 
# --8<-- [start:structure]
-- 원본 표 rentals                인덱스 idx_member
-- (id 순으로 저장)                (member_id 순으로 정렬된 별도 구조)
--
-- id  member_id                  member_id → 어느 행인지
--  1     3                          1     → id 2
--  2     1                          1     → id 4
--  3     5                          2     → id 5
--  4     1                          3     → id 1
--  5     2                          5     → id 3
# --8<-- [end:structure]
 
#! 인덱스는 "값 → 그 행이 어디 있는지" 를 담은 손가락 목록이고,
#! 그 목록이 값 순서대로 줄 세워져 있는 것.
 
# --8<-- [start:proof]
# 정렬돼 있다는 증거 — ORDER BY 를 안 썼는데 정렬돼서 나옴
#(1)> SEARCH rentals USING COVERING INDEX idx_member (member_id>?)
#(1)> 결과: (1,2) (1,4) (2,5) (3,1) (5,3)
#(1)> 원본 표는 3·1·5·1·2 순인데 인덱스로 읽으니 1·1·2·3·5 로 나옴
SELECT member_id, id FROM rentals WHERE member_id > 0;

# --8<-- [end:proof]

#== 그래서 쓰기가 느려짐
#> "정렬을 유지해야 한다" 는 게 비용의 정체.
 
#! member_id = 2 인 행을 새로 넣는다고 하면
#! 원본 표  → 맨 뒤에 그냥 붙이면 끝. id 순이라 새 id 는 항상 맨 뒤. 쌈
#! 인덱스   → 맨 뒤에 못 붙임. 1·1·2 다음, 3 앞에 끼워넣어야 함. 자리를 찾아야 함
#! 인덱스가 3개면 이 작업을 3번 함. DELETE 도 각 인덱스에서 빼줘야 함.
 

 
#== 속도 트레이드 오프

# --8<-- [start]
INSERT               → 항상 모든 인덱스에 항목 추가
DELETE               → 항상 모든 인덱스에서 항목 제거
UPDATE (인덱스 없는 열) → 인덱스 안 건드림. 추가 비용 없음
UPDATE (인덱스 걸린 열) → 빼고 다시 꽂기. 제일 비쌈
 # --8<-- [end]

#! 읽기는 빨라지고 쓰기는 느려지는 맞교환.
#! WHERE·JOIN 에 쓰이는 열에만 index 걸 것.
#! 저장 공간도 더 씀. 별도 구조라 표 하나에 사본이 여러 개 생기는 셈.
 

#== 정리

# --8<-- [start]
인덱스        — "값 → 위치" 를 정렬해 따로 저장해둔 찾아보기
CREATE INDEX 이름 ON 표(열)   — 만들기
DROP INDEX 이름                — 지우기
EXPLAIN QUERY PLAN 질의        — 인덱스를 타는지 확인
SCAN   = 전체 훑기 (인덱스 안 씀)
SEARCH = 색인 탐색 (인덱스 씀)
# --8<-- [end]

#! 걸 곳 → WHERE·JOIN 에 자주 쓰는 열, 특히 외래키. PK·UNIQUE 는 이미 있음
#! 안 걸 곳 → 값 종류가 적은 열, 쓰기가 아주 잦은 표
#! 못 타는 조건 → 열에 함수를 씌움 · LIKE '%...' · 복합 인덱스의 뒤쪽 열만 사용

