"""
title: pgvector — 임베딩 검색과 HNSW
tags: [pgvector]
"""

#== 왜 벡터 검색을 쓰나
#> 예전에 만든 ILIKE 검색의 한계에서 출발함.

# --8<-- [start]
- ILIKE 는 `글자가 겹쳐야` 찾음.
- "책은 며칠 동안 빌릴 수 있나요?" 로 물으면
- "2주 동안 대출할 수 있습니다" 를 못 찾음. why? → `대출` 이라는 글자가 질문에 없어서.
# --8<-- [start]

#! 임베딩 검색은 `뜻이 비슷하면` 찾음.
#! "빌리다" 와 "대출" 이 숫자상 가까운 위치에 있어서 잡힘.
#! 임베딩(embedding) = 문장을 숫자 목록으로 바꾼 것.
#! 뜻이 비슷한 문장끼리 숫자가 비슷해지도록 만들어져 있음.
#! 1024차원이면 숫자 1024개짜리 목록 하나가 문장 하나를 대표함.


#== numpy 가 뭐고 왜 쓰나
#> 숫자 목록을 다루는 라이브러리. 리스트로 해도 되는데 왜 쓰냐가 핵심.

# --8<-- [start:numpy_basic]
import numpy as np

arr = np.array([0.1, 0.2, 0.3], dtype=np.float32)
#(1)> dtype — 안에 담을 숫자의 종류를 미리 못 박음
#(1)> float32 = 소수 하나에 4바이트, float64 = 8바이트

type(arr)    # ndarray   ← 리스트가 아니라 별도 타입
arr.dtype    # float32
arr.shape    # (3,)      ← 모양. 1024차원이면 (1024,)
len(arr)     # 3
# --8<-- [end:numpy_basic]

#! `ndarray` = N-dimensional array. numpy 의 기본 타입.
#! 리스트랑 겉보기는 비슷한데 안이 완전히 다름.
#! `리스트` → 칸마다 "파이썬 객체를 가리키는 주소" 가 들어있음. 
#! `ndarray`→ 같은 타입의 숫자가 `한 덩어리로 붙어서` 저장됨
#! `그래서 세 가지가 달라짐 → 크기 · 연산 방식 · 속도.`


#== 이유 ① 메모리를 훨씬 덜 씀
#> 리스트는 숫자를 직접 안 담음. `주소`를 담고 값은 따로 떨어져 있음.

# --8<-- [start:list_layout]
# 파이썬 리스트 — 두 덩어리로 나뉨
#
#   리스트 껍데기                       따로 흩어진 float 객체들
   ┌──────────────┐                  ┌──────────┐
   │ 관리정보  56   │                  │ 0.001    │ 24바이트
   ├──────────────┤                  ├──────────┤
   │ 주소 → ────── ┼─────────────────▶│ 0.002    │ 24바이트
   │ 주소 → ────── ┼─────────────────▶│ 0.003    │ 24바이트
   │ ... 8바이트씩  │                  │ ...      │
   └──────────────┘                  └──────────┘

# numpy 배열 — 한 덩어리

   ┌────┬────┬────┬────┬────┐
   │0.001│0.002│0.003│... │    │   숫자가 4바이트씩 붙어 있음
   └────┴────┴────┴────┴────┘
# --8<-- [end:list_layout]

#! 리스트 칸에는 숫자가 아니라 `주소`가 들어감. 하나에 8바이트.
#! 진짜 값은 다른 곳에 float 객체로 있고, 그게 하나에 24바이트임.
#! (값 8바이트 + 파이썬이 붙이는 관리 정보 16바이트)
#! numpy 는 그 이중 구조가 없음. 숫자만 붙여서 저장함.


#== 실제로 재본 값 (1024개짜리 소수)

# --8<-- [start:numpy_memory]
# 파이썬 리스트  = 33,432 바이트
   껍데기        8,856  = 56 + (1024칸 × 8바이트 주소)
   float 객체   24,576  = 24바이트 × 1024개

 float32 배열  =  4,096 바이트   (1024 × 4)
 float64 배열  =  8,192 바이트   (1024 × 8)

 → 리스트가 float32 의 약 8.2배
# --8<-- [end:numpy_memory]

#! 껍데기 공식 → `56 + (칸 개수 × 8)`
#! 56 = 빈 리스트도 차지하는 관리 정보 (길이·타입·데이터 주소 등)
#! 8  = 칸 하나에 들어가는 주소 크기. 


#== 왜 dtype=np.float32 를 명시하나
#> numpy 기본값이 `float64` 임. 그냥 두면 메모리가 정확히 2배.

#! float32 → 4,096 바이트 / float64 → 8,192 바이트
#! 임베딩 값은 소수점 아래 정밀도가 그렇게까지 필요 없음.
#! pgvector 에 넣을 때도 float32 로 맞추는 게 자연스러움.


#== 이유 ② 연산이 통째로 됨

# --8<-- [start:numpy_ops]
a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
b = np.array([4.0, 5.0, 6.0], dtype=np.float32)

a + b        # [5. 7. 9.]   ← 원소끼리 더해짐
a * 2        # [2. 4. 6.]
a @ b        # 32.0         ← 내적 (1*4 + 2*5 + 3*6)

# --8<-- [end:numpy_ops]

#! 같은 `+` 인데 뜻이 다름. 리스트는 이어붙이고 배열은 더함.
#! 벡터를 다룰 때는 "더한다" 가 필요하니까 배열이 맞음.
#! `@` 는 내적(dot product). 두 벡터가 얼마나 같은 방향인지 재는 계산.
#! 유사도 계산의 바탕이 이거임. 리스트로 하려면 for 문을 직접 돌려야 함.


#== 이유 ③ 훨씬 빠름

#! 파이썬 for 문은 한 칸씩 파이썬 코드로 도는데
#! numpy 는 C 로 짜인 계산을 한 번에 시킴. 그래서 차이가 큼.
#! 정리 → 벡터는 숫자가 수천 개씩이고 계산이 반복됨.
#! 그 조건에서는 리스트로 하면 메모리도 크고 느림. 그래서 numpy 를 씀.


#== np.asarray 와 np.array 차이

# --8<-- [start:asarray]
np.array(원본, dtype=np.float32)     # 항상 새로 복사함
np.asarray(원본, dtype=np.float32)   # 이미 맞으면 그대로 씀 (복사 안 함)
# --8<-- [end:asarray]

#! asarray → 원본과 `같은 객체` (복사 안 함)
#! array   → 항상 `다른 객체` (복사함)


#== OpenAI 임베딩 응답 구조
#> `client.embeddings.create(...)` 가 돌려주는 게 리스트가 아니라 객체임.

# --8<-- [start:response_shape]
 CreateEmbeddingResponse
   ├ object : 'list'
   ├ model  : 'text-embedding-3-small'
   ├ usage  : Usage
   │            ├ prompt_tokens : 8
   │            └ total_tokens  : 8
   └ data   : [                       ← 리스트! 문장 개수만큼 들어있음
                Embedding
                  ├ object    : 'embedding'
                  ├ index     : 0      ← 몇 번째 문장이었는지
                  └ embedding : [0.0023, -0.0091, ...]   ← 숫자 1024개
              ]
# --8<-- [end:response_shape]

#! `response`                  → CreateEmbeddingResponse 객체
#! `response.data`             → 리스트
#! `response.data[0]`          → Embedding 객체
#! `response.data[0].embedding`→ 드디어 숫자 목록 (파이썬 list)
#! `index` 는 "내가 보낸 문장 중 몇 번째냐" 를 알려줌.
#! 응답 순서가 보낸 순서와 다를 수 있어서 붙어있는 번호표.


#== 임베딩을 통한 벡터화 embeddings.create()
#> embeddings.create() -> CreateEmbeddingResponse 객체 반환

# --8<-- [start:embed_helpers]
from openai import OpenAI

client = OpenAI()

def embed_text(value: str) -> np.ndarray:
    """문장 하나를 1024차원 float32 벡터로 변환한다."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=value,
        dimensions=EMBEDDING_DIMENSIONS,
        #(1)> dimensions — 차원 수를 줄여서 받을 수 있음 (기본 1536 → 1024)
        #(1)> 작을수록 저장 공간·검색 비용이 줄고 정확도는 조금 떨어짐
    )
    return np.asarray(response.data[0].embedding, dtype=np.float32)
    #(2)> data[0] → 문장 1개니까 원소도 1개
    #(2)> .embedding → 그 안의 숫자 목록
    #(2)> np.asarray(..., float32) → 파이썬 리스트를 ndarray 로


def embed_many(values: list[str]) -> list[np.ndarray]:
    """여러 문장을 하나의 API 요청으로 변환한다."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=values,
        #(3)> 리스트를 넣으면 여러 개를 한 번에 처리. 요청 1번으로 끝남
        dimensions=EMBEDDING_DIMENSIONS,
    )
    ordered_items = sorted(response.data, key=lambda item: item.index)
    #(4)> index 순으로 다시 정렬. 응답 순서가 보낸 순서와 다를 수 있어서
    return [
        np.asarray(item.embedding, dtype=np.float32)
        for item in ordered_items
    ]
# --8<-- [end:embed_helpers]

#! 문장 6개를 하나씩 부르면 API 호출 6번, embed_many 로 하면 1번.
#! 네트워크 왕복이 줄어서 훨씬 빠름. 비용은 토큰 기준이라 같음.
#! `sorted(..., key=lambda item: item.index)` 는 안전장치임.
#! 보통은 순서대로 오는데, 보장은 안 되니까 index 로 다시 줄 세우는 것.


#== register_vector 가 뭐냐
#> psycopg 에게 "ndarray 를 vector 타입으로 보내는 법" 을 알려주는 등록 절차.

# --8<-- [start:register]
from pgvector.psycopg import register_vector

conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
# DB 쪽 준비 — Postgres 에 vector 타입과 <=> 연산자를 추가
conn.commit()

register_vector(conn)
#(2)> 파이썬 쪽 준비 — 이 연결에서 ndarray ↔ vector 변환을 켬
#(2)> 연결마다 따로 해줘야 함. 새 연결을 만들면 다시 불러야 함
# --8<-- [end:register]

#! `register_vector 없이` ndarray 를 넣으면
#! → ProgrammingError: cannot adapt type 'ndarray' using placeholder '%s'
#! psycopg 는 파이썬 타입을 SQL 값으로 바꾸는 규칙을 갖고 있음.
#! str·int·datetime 같은 건 기본으로 아는데 `ndarray 는 모름`.
#! register_vector 가 그 규칙을 하나 추가해주는 것.
#! 반대 방향도 같이 등록됨. 꺼낼 때 문자열이 아니라 Vector 객체로 나옴.



#== 표 만들기와 <=> 연산자

# --8<-- [start:create_table]
conn.execute("""
    CREATE TABLE documents (
        id BIGSERIAL PRIMARY KEY,
        content TEXT NOT NULL,
        category TEXT NOT NULL,
        embedding vector(1024) NOT NULL
    )
""")
# --8<-- [end:create_table]

# --8<-- [start:distance]
SELECT
    content,
    embedding <=> %s AS distance,        -- 코사인 거리 (작을수록 비슷)
    1 - (embedding <=> %s) AS similarity -- 유사도 (클수록 비슷)
FROM documents
ORDER BY embedding <=> %s                -- 가까운 것부터
LIMIT 3
# --8<-- [end:distance]

#! 실제 검색 결과 (질문: "책은 며칠 동안 빌릴 수 있나요?")
#! 1위 거리=0.6306 유사도=0.3694  "한 번에 최대 5권까지 2주 동안 대출할 수 있습니다."
#! 2위 거리=0.6713 유사도=0.3287  "도서관 휴관일은 매주 월요일입니다."
#! 3위 거리=0.6970 유사도=0.3030  "주차장은 지하 1층에..."

#! 유사도 0.37 이 낮아 보이는데 이게 정상임.
#! 임베딩 유사도는 절대값보다 `순위`가 중요함. 1위가 맞으면 잘 된 것.
#! 문서가 6개뿐이라 관련 없는 것도 2·3위에 들어옴. LIMIT 로 자르는 이유.

#== 거리 종류가 세 가지 있음
# --8<-- [start]
 <=> 코사인 거리   — 방향만 봄. 문장 임베딩에 가장 많이 씀
   - 거리 0 = 완전히 같은 방향, 1 = 무관, 2 = 정반대
 <-> L2 거리      — 직선 거리
 <#> 내적의 음수   — 크기까지 봄
# --8<-- [end]

#== HNSW — 왜 필요한가
#> 인덱스가 없으면 질문 하나에 `모든 문서와 일일이 비교`함.

#! 문서 20만 개면 비교 20만 번. 차원이 1024면 계산량이 어마어마해짐.
#! → 벡터 전용 인덱스가 따로 필요함. 그게 HNSW.


#== HNSW 이름 뜯어보기
#> Hierarchical Navigable Small World. 세 단어를 하나씩 보면 됨.

# --8<-- [start:hnsw_name]
 Navigable Small World  — 벡터들을 '가까운 것끼리 선으로 이은 지도'
                          목적지 쪽으로 선을 따라 걸어가면 도착함

 Hierarchical           — 그 지도를 여러 층으로 쌓음
                          위층일수록 노드가 적고 한 걸음이 큼

 (Approximate)          — 전부 비교하지 않으니 답이 '가장 가까운 것'이
                          아닐 수도 있음. 근사값
# --8<-- [end:hnsw_name]

#! 지하철 노선도로 생각하면 감이 옴.
#! 위층 = 급행. 정차역이 적어서 먼 거리를 몇 정거장에 감
#! 아래층 = 완행. 역이 촘촘해서 목적지 바로 앞까지 감
#! → 급행으로 대충 근처까지 간 뒤, 완행으로 갈아타 정확히 찾아감

#== 검색 순서
#! ① 맨 위층 아무 노드에서 시작
#! ② 이웃 중 질문과 더 가까운 곳으로 이동. 더 가까운 이웃이 없으면 멈춤
#! ③ 그 자리를 아래층 출발점으로 삼아 ②를 반복
#! ④ 맨 아래층(레벨 0)에서 후보를 모아 가까운 순 top-k 를 돌려줌
#! 핵심은 `전부 안 봄`. 걸어간 길 주변만 봄.
#! 그래서 빠른 대신 진짜 1등을 놓칠 수 있음.


#== HNSW 만들고 실행계획 확인하기

# --8<-- [start:hnsw_create]
CREATE INDEX documents_embedding_hnsw
ON documents
USING hnsw (embedding vector_cosine_ops);
--(1)> USING hnsw — 인덱스 종류
--(1)> vector_cosine_ops — <=> (코사인)용 인덱스라는 뜻
--(1)> 검색에 쓰는 연산자와 반드시 맞춰야 함. 안 맞으면 인덱스를 안 탐
--(1)>   <=> 코사인 → vector_cosine_ops
--(1)>   <->  L2   → vector_l2_ops
--(1)>   <#>  내적  → vector_ip_ops
# --8<-- [end:hnsw_create]

#== ef_search — 속도와 정확도를 맞바꾸는 손잡이
#> HNSW 는 답이 틀릴 수 있음. 얼마나 틀릴지를 이 값으로 조절함.
 
# --8<-- [start:ef_search]
SET hnsw.ef_search = 100;
--(1)> 레벨 0 에서 후보를 몇 개나 모아볼지. 기본값 40
--(1)> 이 연결에서만 적용됨. 새 연결을 만들면 다시 40 으로 돌아감
--(1)> 넣을 수 있는 범위는 1 ~ 1000. 초과하면 에러
# --8<-- [end:ef_search]
 
#! 검색 결과가 이상함          → ef_search 부터 올려볼 것
#! 느림                     → ef_search 를 내리거나, 애초에 인덱스가 맞는지 확인
#! 기본값 40 은 꽤 낮은 편     → 정확도가 중요하면 100~200 을 먼저 시도
  
#== 정리

#! `임베딩`       — 문장을 숫자 목록으로. 뜻이 비슷하면 숫자도 비슷해짐
#! `numpy`       — 숫자 뭉치를 다루는 타입. 리스트보다 8배 작고 46배 빠름
#! `dtype`       — float32 로 못 박아야 메모리가 절반
#! `응답 구조`     — response.data[0].embedding 까지 세 겹을 파고들어야 숫자가 나옴
#! `register_vector` — psycopg 에게 ndarray ↔ vector 변환법을 알려주는 등록
#! `vector(1024)` — 차원 고정. 모델 바꾸면 표를 다시 만들어야 함
#! `<=>`        — 코사인 거리. 작을수록 비슷. 유사도 = 1 - 거리
#! `HNSW `       — 다층 지도를 걸어가며 찾는 벡터 전용 인덱스
#! `ef_search`   — 후보를 몇 개 볼지. 올리면 정확해지고 느려짐

