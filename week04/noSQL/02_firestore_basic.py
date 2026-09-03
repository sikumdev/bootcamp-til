"""
title: Firestore — 문서 기반 NoSQL
tags: [firebase, firestore]
"""

#== Firestore 가 뭐냐 — SQL 과 뭐가 다른가
#> 표(테이블)가 아니라 `문서(document)`에 데이터를 담는 DB.

# --8<-- [start:vs_sql]
SQL(Postgres)              Firestore
데이터베이스                  프로젝트
테이블(table)                컬렉션(collection)
행(row)                     문서(document)
열(column)                  필드(field)
# --8<-- [end:vs_sql]


# --8<-- [start]

① 스키마가 없음.
- Postgres 는 CREATE TABLE 로 열과 타입을 미리 정했음.
- Firestore 는 미리 정하는 게 없음. 문서마다 필드가 달라도 됨.

② 컬렉션을 미리 만들 필요가 없음.
- db.collection("customers") 는 없으면 알아서 생김.

③ JOIN 이 없음.
- books · rentals 를 이어붙이는 걸 DB 가 안 해 줌.
- 필요하면 화면에 쓸 값을 문서에 미리 복사해둠 (비정규화)

# --8<-- [end]


#! 스키마가 없다는 건 장점이자 단점임.
#! 빨리 시작할 수 있는데, 오타 난 필드명도 그냥 들어감.



#== 준비 — 서비스 계정 키

# --8<-- [start:setup]
# Firebase Console → 프로젝트 설정 → 서비스 계정 → 새 비공개 키 생성
# 받은 JSON 을 serviceAccountKey.json 으로 저장

# pip install firebase-admin

from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

KEY_PATH = Path("serviceAccountKey.json")
assert KEY_PATH.exists(), "serviceAccountKey.json 을 같은 폴더에 넣으세요."

if not firebase_admin._apps:
    #(1)> 이미 초기화됐는지 확인. 주피터에서 셀을 두 번 돌리면 에러 나는 걸 막음
    credential = credentials.Certificate(str(KEY_PATH))
    firebase_admin.initialize_app(credential)

db = firestore.client()
print("연결 완료:", db.project)
# --8<-- [end:setup]


#== 문서 만들기 — 직접 문서 ID 지정

# --8<-- [start:set_doc]
agent_ref = db.collection("customers").document("agent")

agent_ref.set({
    "name": "Agent",
    "city": "Seoul",
    "points": 1000,
})


print(agent_ref.id)   # 'agent'
# --8<-- [end:set_doc]


#== 자동 ID 로 만들기

# --8<-- [start:add_doc]
write_result, new_ref = db.collection("customers").add({
    "name": "김민준", "city": "Busan", "points": 700,
})

print(write_result,new_ref)
#(1)> 반환값이 (시간, 참조) 순서임. 참조가 두 번째라 헷갈리기 쉬움
#(1)> write_result 는 문서가 만들어진 시각(update_time)

print(new_ref.id)   # 'xK3mP...' 같은 무작위 문자열

# 같은 결과를 두 줄로 나눠서
new_ref = db.collection("customers").document()
#(2)> 인자를 안 주면 자동 ID 참조를 미리 만들어 줌
new_ref.set({"name": "김민준"})

# --8<-- [end:add_doc]

#! ID 를 어떻게 정할지 기준
#! 자동 ID   → 계속 늘어나는 것 (게시글, 주문, 상담 내역)
#! 직접 지정  → 이미 고유한 값이 있는 것 (국가 코드, 상품 코드)
#! Auth UID  → 사용자 한 명당 프로필 문서 하나


#== 문서 읽기 — get 과 stream

# --8<-- [start:read]
# 단건 — get()
snapshot = db.collection("customers").document("agent").get()

if snapshot.exists:
    print(snapshot.id)         # 'agent'
    print(snapshot.to_dict())  # {'name':'Agent', 'points':1000, 'city':'Seoul'}
else:
    print("문서가 없습니다.")

# 여러 건 — stream()
snapshots = list(db.collection("customers").stream())
#(2)> stream() 은 제너레이터를 돌려줌 → len() 이나 재사용을 하려면 list() 로 받을 것
print("고객 수:", len(snapshots))

for s in snapshots:
    print(s.id, s.to_dict())
# --8<-- [end:read]

#! 없는 문서를 get() 해도 에러가 안 남. 빈 스냅샷이 돌아옴.
#! 그래서 `snapshot.exists` 확인이 필수. 안 하면 to_dict() 가 None 을 줌.

#! ★ stream() 은 `문서 수만큼 읽기 비용이 발생`함. Firestore 는 읽은 문서 수로 과금.
#! `.limit(20)` 을 붙이는 습관을 들일 것.


#== set · update · merge · delete 차이

# --8<-- [start:write_ops]
 메서드                    문서가 없을 때    문서가 있을 때
 set(data)                생성             전체 교체 ← 나머지 필드 사라짐
 set(data, merge=True)    생성             전달한 필드만 병합
 update(data)             에러(NotFound)   전달한 필드만 수정
 delete()                 아무 일 없음      문서 삭제
# --8<-- [end:write_ops]

# --8<-- [start:write_example]
# points 만 바뀜. name·city 는 그대로
agent_ref.update({"points": 1200})

# phone 이 추가됨. 기존 필드 유지
agent_ref.set({"phone": "010-1234-5678"}, merge=True)

# merge 없이 set 하면 name·city·points 가 전부 날아가고 phone 만 남음
agent_ref.set({"phone": "010-1234-5678"})
# --8<-- [end:write_example]


#! `update` vs `merge=True` 차이
#! update      → 문서가 없으면 에러. "있는 걸 고친다" 는 의도가 분명할 때
#! merge=True  → 문서가 없으면 만들어 줌. "있으면 고치고 없으면 만들어" 일 때

#! 필드 하나만 지우려면 → `update({"phone": firestore.DELETE_FIELD})`


#== 쿼리 — where · order_by · limit

# --8<-- [start:query]
q = (
    db.collection("customers")
    .where(filter=FieldFilter("city", "==", "Seoul"))
    .order_by("points", direction=firestore.Query.DESCENDING)
    .limit(20)
)

for s in q.stream():
    data = s.to_dict()
    print(data.get("name", "이름없음"), data.get("points", 0))
# --8<-- [end:query]



#== 조건 연산자 — SQL 과 대응

# --8<-- [start:operators]

# SQL                    Firestore
# =                      "=="
# !=                     "!="
# >, >=, <, <=           같은 기호
# IN (...)               "in"
# 배열에 값이 있나          "array_contains"
# 배열 값 중 하나라도       "array_contains_any"

db.collection("customers").where(
    filter=FieldFilter("city", "in", ["Seoul", "Busan"])
)


db.collection("customers").where(
    filter=FieldFilter("tags", "array_contains", "VIP")
    #(2)> tags 가 ["AI","VIP"] 인 문서가 걸림. 배열 안을 들여다보는 조건
)
# --8<-- [end:operators]

#! `where` 를 여러 번 이으면 SQL 의 AND 와 같음. OR 는 기본적으로 안 됨.



#== 복합 인덱스 — 조건을 조합하면 에러가 나는 이유

# --8<-- [start:composite]
q = (
    db.collection("customers")
    .where(filter=FieldFilter("city", "==", "Seoul"))
    .where(filter=FieldFilter("points", ">=", 1000))
    .order_by("points", direction=firestore.Query.DESCENDING)
    #(2)> 부등호(>, >=, <) 조건과 정렬을 같이 쓸 때는
    #(2)> 첫 order_by 가 그 부등호 필드여야 함. 위 예시에서 points 로 정렬한 게 그래서임.

)

from google.api_core.exceptions import FailedPrecondition

try:
    for s in q.stream():
        print(s.to_dict())
except FailedPrecondition as e:
    print("복합 인덱스가 필요합니다. 아래 링크를 여세요.")
    print(e)
    #(1)> 에러 메시지 안에 인덱스 생성 링크가 같이 들어옴
# --8<-- [end:composite]

#! Firestore 는 컬렉션 전체를 훑는 방식이 아예 없음. 무조건 인덱스로 찾음.
#! 단일 필드 인덱스는 자동으로 만들어지는데, 여러 필드를 조합하면 그 조합에 맞는
#! `복합 인덱스`가 따로 있어야 함. 없으면 실행이 거부됨.

#== 복합 인덱스 에러 해결 순서
#! ① 에러 메시지의 console.firebase.google.com 링크 열기
#! ② 컬렉션·필드가 자동으로 채워져 있는지 확인
#! ③ Create index 누르고 Indexes 탭에서 활성화될 때까지 기다리기 (몇 분 걸림)
#! ④ 쿼리 다시 실행


#== 필드 타입 — 문자열·숫자 말고도

# --8<-- [start:types]
profile_ref = db.collection("customer_profiles").document("profile-sample")
profile_ref.set({
    "name": "김민준",              # 문자열
    "active": True,                # 불리언
    "age": 31,                     # 숫자
    "interests": ["AI", "Cloud"],  # 배열
    "address": {                   # 맵 (중첩 객체)
        "city": "Seoul",
        "zip_code": "04524",
    },
    "created_at": firestore.SERVER_TIMESTAMP,
    #(1)> 내 컴퓨터 시각이 아니라 Firestore 서버 시각이 기록됨
    #(1)> 사용자 PC 시계가 틀려도 상관없어서 시간 기록엔 이걸 쓸 것
})
# --8<-- [end:types]

#! 배열이 계속 커지는 데이터는 문서 안에 넣으면 안 됨 → 하위 컬렉션으로 뺄 것.


#== 원자적 수정 — ArrayUnion · ArrayRemove · Increment
#> "먼저 읽고 → 계산하고 → 쓰기" 를 하지 않아도 되는 명령들.

# --8<-- [start:atomic]
profile_ref.update({"interests": firestore.ArrayUnion(["Firebase", "AI"])})
# 추가 후: ['AI', 'Cloud', 'Firebase']
#(1)> 'AI' 는 이미 있어서 중복으로 안 들어감. 'Firebase' 만 뒤에 붙음

profile_ref.update({"interests": firestore.ArrayRemove(["Cloud"])})
# 삭제 후: ['AI', 'Firebase']

# 현재 값을 안 읽고도 300 을 더함
agent_ref.update({"points": firestore.Increment(300)})
# --8<-- [end:atomic]

#! 왜 이런 게 따로 있냐 → 직접 하면 값이 틀어질 수 있어서.
#! `읽기 → +300 → 쓰기` 사이에 다른 사람이 끼어들면 한 명의 증가분이 사라짐.
#! Increment 는 서버에서 한 번에 처리해서 그런 일이 없음.
#! Redis 의 `incr` 과 같은 이유임. 거기서도 get→+1→set 은 위험하다고 정리했음.



#== 데이터 설계 — 문서에 넣을까, 하위 컬렉션으로 뺄까

#> 문서 안에 포함 (배열·맵)
#! 적합 → 크기가 작고 항상 같이 읽는 것 (주소, 환경 설정)
#! 장점 → 한 번 읽으면 다 나옴. 읽기 비용 1회
#! 한계 → 계속 커지는 데이터는 안 됨 (문서 1MB 제한)

#> 하위 컬렉션으로 분리
#! 적합 → 개수가 계속 늘어나는 것 (주문, 댓글, 상담 이력)
#! 장점 → 필요한 것만 쿼리·정렬 가능
#! 한계 → 상위 문서와 따로 읽어야 함

# --8<-- [start:subcollection]
# 구조: customers / agent / consultations / consultation-001
#(1)> 컬렉션 → 문서 → 컬렉션 → 문서 로 계속 파고들 수 있음
(db.collection("customers").document("agent")
   .collection("consultations").document("consultation-001")
   .set({"memo": "첫 상담", "at": firestore.SERVER_TIMESTAMP}))
# --8<-- [end:subcollection]

#! 상위 문서를 삭제해도 하위 컬렉션은 안 지워짐.
#! DB 화면에서 안 보이게 될 뿐 데이터는 남아 있음. 직접 지워야 함.

#== 원자적 쓰기 — 배치와 트랜잭션
#> 여러 작업이 "전부 성공하거나 전부 실패" 하게 묶는 것.

# --8<-- [start:batch]
# 배치 — 값을 읽을 필요 없이 여러 문서를 한 번에 쓸 때
batch = db.batch()

ref1 = db.collection("batch_customers").document("batch-1")
ref2 = db.collection("batch_customers").document("batch-2")

batch.set(ref1, {"name": "오하늘", "points": 400})
batch.set(ref2, {"name": "윤도현", "points": 800})
batch.update(ref1, {"points": firestore.Increment(100)})

batch.commit()
# --8<-- [end:batch]

# --8<-- [start:transaction]
# 트랜잭션 — 읽은 값을 보고 계산해서 써야 할 때
@firestore.transactional
def decrease_stock(transaction, ref, amount):
    snapshot = ref.get(transaction=transaction)
    current = snapshot.to_dict()["stock"]

    if current < amount:
        raise ValueError("재고 부족")

    transaction.update(ref, {"stock": current - amount})
    #(1)> 읽는 사이에 다른 사람이 값을 바꾸면 SDK 가 처음부터 다시 시도함
    #(1)> 재시도 기본 횟수는 5회

decrease_stock(db.transaction(), db.collection("items").document("item-1"), 3)
# --8<-- [end:transaction]

#== 배치와 트랜잭션은 언제 쓰나
#> 배치     → 읽을 필요 없이 그냥 쓰기만. "문서 두 개를 같이 만들기"
#> 트랜잭션 → 읽은 값에 따라 쓸 값이 달라짐. "재고를 읽고 부족하면 취소"

#! `참고`
#! 재고 차감은 왜 Increment 로 안 하고 트랜잭션이냐 →
#! Increment 는 "무조건 더하기". 재고가 0인지 확인하는 판단을 못 함.
#! 조건 검사가 필요하면 트랜잭션.

#! 트랜잭션 함수는 여러 번 실행될 수 있음.
#! 안에 print 나 외부 API 호출을 넣으면 여러 번 실행됨. 읽기·쓰기만 넣을 것.
#! 배치는 한 번에 묶을 수 있는 작업 수에 제한이 있음. 대량 처리는 나눠서 할 것.


#== 정리
# --8<-- [start]
 컬렉션 = 테이블 · 문서 = 행 · 필드 = 열 (단, 스키마가 없음)
 .document("id") → 참조만 만듦 · 
 .set() → 실제로 저장
 .add() → (시각, 참조) 튜플. 참조가 두 번째
 .get() → 단건 (exists 확인 필수) · stream() → 여러 건 (제너레이터)
 set = 통째로 교체 · update = 일부 수정 · set(merge=True) = 없으면 생성 + 병합
 ArrayUnion / ArrayRemove / Increment = 읽지 않고 안전하게 고치기
 배치 = 읽기 없이 여러 쓰기 · 트랜잭션 = 읽은 값으로 판단해서 쓰기

 조심할 것 세 개
 ① set 에 일부 필드만 넣으면 나머지가 날아감 → update 나 merge=True
 ② 조건을 조합하면 복합 인덱스가 필요함 → 에러 링크로 만들면 됨
 ③ serviceAccountKey.json 은 절대 git 에 올리지 말 것
# --8<-- [end]
