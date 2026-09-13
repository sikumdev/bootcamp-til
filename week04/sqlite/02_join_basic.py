"""
title: JOIN — INNER 와 LEFT
tags: [sqlite]
"""

#== JOIN 이 뭐냐
#> 어려운 새 문법이 아님. "번호를 기준으로 다른 표의 정보를 찾아 붙이는 것".

# --8<-- [start:concept]
# rentals 표에는 누가 빌렸는지가 `member_id: 1` 이라는 숫자로만 적혀 있음.
# 이름을 보려면 members 표에서 id=1 인 행을 찾아 옆에 붙여야 함. 그게 JOIN 임.

-- rentals                        members
-- id  book_id  member_id         id  name
-- 1   1        1        ──────►  1   Alice
-- 2   3        1        ──────►  1   Alice
-- 3   2        2        ──────►  2   Bob
--
-- 붙이면
-- id  book_id  member_id  name
-- 1   1        1          Alice
-- 2   3        1          Alice
-- 3   2        2          Bob
# --8<-- [end:concept]

#! "어느 열끼리 맞춰볼지" 를 알려주는 게 ON 뒤에 오는 조건.
#! `ON r.member_id = m.id` = "rentals 의 member_id 와 members 의 id 가 같은 것끼리".


#== 기본 형태와 별칭(alias)

# --8<-- [start:basic]
# JOIN 은 INNER JOIN 의 줄임말. 그냥 JOIN 이라고 쓰면 INNER 임
SELECT m.name, r.rental_date
FROM rentals r
JOIN members m ON r.member_id = m.id

# --8<-- [end:basic]

#! 별칭을 왜 쓰냐 → `rentals.member_id` 를 매번 쓰면 길어서.
#! 표가 3개 넘어가면 별칭 없이는 못 읽음.



#== INNER JOIN — 양쪽에 다 있는 것만
#> 두 표를 맞춰봐서 짝이 있는 행만 남김. 짝이 없으면 결과에서 빠짐.

# --8<-- [start:inner]
SELECT COUNT(*) FROM rentals r
JOIN members m ON r.member_id = m.id;   -- 결과: 10
# --8<-- [end:inner]

#! INNER JOIN 은 "교집합" 이라고 생각하면 됨.
#! 회원인데 안 빌린 사람, 없는 회원 번호가 적힌 대여 기록 → 둘 다 탈락.


#== LEFT JOIN — 왼쪽은 전부 남김
#> 왼쪽(FROM 에 쓴) 표의 행은 짝이 없어도 남기고, 오른쪽 자리를 NULL 로 채움.

# --8<-- [start:left]
#  Emma 는 대여 기록이 하나도 없는데 행이 살아남음
#(1)> 대신 rentals 쪽에서 온 값은 전부 NULL(파이썬에선 None)
SELECT m.name, r.id, r.book_id
FROM members m
LEFT JOIN rentals r ON m.id = r.member_id
WHERE m.name = 'Emma';   -- 결과: ('Emma', None, None)

# --8<-- [end:left]


#! 어느 표를 왼쪽에 둘지가 결정적임.
#! "회원 전원을 보고 싶다" → members 를 왼쪽에
#! "대여 기록 전부를 보고 싶다" → rentals 를 왼쪽에


#== LEFT JOIN 의 대표 용도 — "없는 것" 찾기
#> LEFT JOIN 한 뒤 오른쪽이 NULL 인 행만 고르면 "짝이 없는 것" 이 나옴.

# --8<-- [start:antijoin]
-- 한 번도 책을 안 빌린 회원
SELECT m.name
FROM members m
LEFT JOIN rentals r ON m.id = r.member_id
WHERE r.id IS NULL;   -- 결과: ('Emma',)


-- 한 번도 안 빌려진 책
SELECT b.title
FROM books b
LEFT JOIN rentals r ON b.id = r.book_id
WHERE r.id IS NULL;   -- 결과: 없음 ("6권이 전부 한 번 이상 대여됐다" 는 뜻)
# --8<-- [end:antijoin]

#! `WHERE r.id IS NULL` 에서 왜 하필 r.id 냐 →
#! PK 라서 원래는 절대 NULL 이 될 수 없는 열이기 때문.
#! 그런 열이 NULL 이면 "짝이 없어서 채워진 가짜 NULL" 이 확실함.


#== LEFT JOIN 에서 WHERE 를 잘못 쓰면 INNER 가 됨
#> 제일 많이 하는 실수. 조건을 ON 에 두느냐 WHERE 에 두느냐로 결과가 달라짐.

# --8<-- [start:on_vs_where]
# ① 조건을 ON 에 → LEFT JOIN 이 유지됨. 회원 5명 전원 나옴
#(1)> 결과 ('Alice', 9) ('Bob', 8) ('Charlie', 10) ('David', None) ('Emma', None)
SELECT m.name, r.id FROM members m
LEFT JOIN rentals r ON m.id = r.member_id AND r.rental_date >= '20240401';

# ② 같은 조건을 WHERE 로 옮기면 → 3명만 남음. LEFT 가 무의미해짐
#(2)> 결과 ('Bob',8) ('Alice',9) ('Charlie',10)
#(2)> David·Emma 는 r.rental_date 가 NULL → 비교가 성립 안 해서 탈락
SELECT m.name, r.id FROM members m
LEFT JOIN rentals r ON m.id = r.member_id
WHERE r.rental_date >= '20240401';

# --8<-- [end:on_vs_where]


#! 왜 이렇게 되냐 → 순서 때문임.
#! ① JOIN 이 먼저 실행돼서 David·Emma 가 NULL 로 채워진 행으로 남음
#! ② 그 다음 WHERE 가 실행되면서 NULL 인 행을 걸러버림
#! → 애써 살려둔 행을 뒤에서 다시 지우는 꼴.

#! 구분하는 감
#! ON    = "붙일 때 어떤 것만 붙일까" (오른쪽 표를 거르는 조건)
#! WHERE = "다 붙인 뒤 어떤 행만 볼까" (최종 결과를 거르는 조건)

#! 오른쪽 표에 대한 조건은 ON 에, 왼쪽 표에 대한 조건은 WHERE 에.


#== 조건이 IS NULL 이면 반대로 안 걸러짐
#> 위 함정의 사촌. 이건 오히려 안 걸러져서 엉뚱한 답이 나옴.

# --8<-- [start:null_trap]
# "아직 반납 안 한 사람" 을 찾기
#(1)> 결과: ('Alice',2) ('Bob',6) ('Bob',8) ('Charlie',10) ('Emma',None)
#(1)> Emma 가 끼어 있음. Emma 는 빌린 적이 아예 없는데
#(1)> LEFT JOIN 이 채운 가짜 NULL 도 "IS NULL" 조건에 걸려서 통과함
SELECT m.name, r.id FROM members m
LEFT JOIN rentals r ON m.id = r.member_id
WHERE r.return_date IS NULL;

# --8<-- [end:null_trap]

#! "안 빌린 사람" 과 "빌리고 안 반납한 사람" 이 섞임 → 완전히 다른 의미인데.
#! 이 질문의 대상은 대여 기록이므로 애초에 rentals 를 왼쪽에 두거나 INNER 를 써야 맞음.

# --8<-- [start:null_trap_fix]
# 대여 기록이 있는 것 중에서만 고르니까 Emma 는 애초에 안 들어옴
#(1)> 결과: ('Alice',2) ('Bob',6) ('Bob',8) ('Charlie',10) 
SELECT m.name, r.id FROM rentals r
JOIN members m ON r.member_id = m.id
WHERE r.return_date IS NULL;

# --8<-- [end:null_trap_fix]

#! 교훈 → LEFT JOIN 결과에 IS NULL 조건을 걸 때는
#! "이 NULL 이 원래 있던 NULL 인가, JOIN 이 채운 NULL 인가" 를 항상 따져볼 것.


#== COUNT(*) 와 COUNT(열) 이 다름
#> LEFT JOIN + GROUP BY 조합에서 바로 티가 남.

# --8<-- [start:count]
# ① COUNT(*) 로 세면 Emma 가 1
#(1)> Alice 3 · Bob 3 · Charlie 2 · David 2 · Emma 1   ← Emma 가 틀림
SELECT m.name, COUNT(*) FROM members m
LEFT JOIN rentals r ON m.id = r.member_id GROUP BY m.id;


#  ② COUNT(r.id) 로 세면 Emma 가 0
SELECT m.name, COUNT(r.id) FROM members m
LEFT JOIN rentals r ON m.id = r.member_id GROUP BY m.id;
-- Alice 3 · Bob 3 · Charlie 2 · David 2 · Emma 0   ← 이게 맞음
# --8<-- [end:count]


#! 이유 → `COUNT(*)` 는 "행 개수" 를 셈.
#! Emma 는 대여가 없어도 NULL 로 채워진 행이 1개 있으니까 1 이 됨.
#! `COUNT(r.id)` 는 "NULL 이 아닌 값의 개수" 를 셈 → NULL 이라 0.

#! LEFT JOIN 하고 개수를 셀 때는 무조건 `COUNT(오른쪽표.PK)` 를 쓸 것.


#== 표 3개 잇기

# --8<-- [start:three]
#  JOIN 을 이어서 쓰면 됨. rentals 를 가운데 두고 양쪽으로 붙이는 모양
SELECT m.name, b.title, r.return_date
FROM rentals r
JOIN members m ON r.member_id = m.id
JOIN books   b ON r.book_id   = b.id
ORDER BY r.id;

# --8<-- [end:three]

#! rentals 같은 표를 연결 테이블이라고 부름.
#! "누가(member_id) 무엇을(book_id) 언제" 만 담고 있고, 이름·제목은 각 표에서 가져옴.
#! 회원과 책은 다대다 관계임 (한 사람이 여러 책, 한 책을 여러 사람이).
#! 그걸 표 하나로는 못 담아서 가운데에 rentals 를 두는 것.


#== 행 수가 늘어나는 것 주의

#! JOIN 은 짝이 여러 개면 행이 그만큼 불어남.
#! Alice 는 members 에 1행인데 대여가 3건이라 JOIN 하면 3행이 됨.

#! 확인 습관 → JOIN 전후로 COUNT(*) 를 찍어보기.
#! 늘었으면 "왜 늘었는지" 를 설명할 수 있어야 함.


#== 정리

#! 함정 네 가지 
#! ① 열 이름이 겹치면 ambiguous column name 에러 → 표별칭. 을 붙일 것
#! ② LEFT JOIN + 오른쪽 표 조건을 WHERE 에 두면 INNER 가 됨 → ON 으로 옮길 것
#! ③ LEFT JOIN + IS NULL 은 가짜 NULL 까지 걸림 → 왼쪽 표 선택을 다시 볼 것
#! ④ LEFT JOIN 뒤 COUNT(*) 는 짝 없는 행도 1로 셈 → COUNT(오른쪽PK) 를 쓸 것


