---
title: 벡터 저장소 — Chroma·FAISS로 저장/검색/재연결하기
date: 2026-09-08
tags: [vectorstore]
---

# 벡터 저장소 — Chroma·FAISS로 저장/검색/재연결하기

> 원본 코드: [`04_vectorstore.py`](04_vectorstore.py)

## 기본 세팅

임베딩 모델은 BAAI/bge-m3

<div class="til-code" markdown>
```python
import os, logging
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TQDM_DISABLE"] = "1"
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
from transformers.utils import logging as hf_logging
hf_logging.disable_progress_bar()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

pages = PyPDFLoader("SPRi_AI_Brief_8월호.pdf").load()
docs = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150).split_documents(pages)
embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
```
</div>

## 영속 색인 — persist_directory

`collection_name` 은 저장소 안의 이름표, `persist_directory` 는 저장될 폴더.

<div class="til-code" markdown>
```python
company_ai_documents = [
    Document(
        page_content="보안 검토: 사내 생성형 AI 도입 전 사용자 접근 권한, API 키 보관, 외부 네트워크 연결 정책을 점검한다.",
        metadata={"category": "보안", "title": "도입 전 보안 검토"},
    ),
    Document(
        page_content="보안 통제: 생성형 AI 서비스에는 역할 기반 접근 제어를 적용하고 API 키 노출 여부를 상시 확인한다.",
        metadata={"category": "보안", "title": "접근 제어"},
    ),
    Document(
        page_content="보안 운영: 생성형 AI 계정 권한을 최소화하고 퇴사자 권한과 장기 미사용 API 키를 즉시 회수한다.",
        metadata={"category": "보안", "title": "권한 회수"},
    ),
    Document(
        page_content="개인정보 보호: 고객 이름과 연락처 같은 개인정보를 외부 생성형 AI 서비스에 입력하지 않도록 마스킹 기준을 마련한다.",
        metadata={"category": "개인정보", "title": "입력 데이터 보호"},
    ),
    Document(
        page_content="비용 관리: 모델별 토큰 사용량과 호출 비용을 모니터링하고 부서별 예산 한도와 경보를 설정한다.",
        metadata={"category": "비용", "title": "사용량 관리"},
    ),
    Document(
        page_content="직원 교육: 프롬프트 작성법, 환각 검증법, 기밀정보 입력 금지 원칙을 실제 사례 중심으로 교육한다.",
        metadata={"category": "교육", "title": "사용자 교육"},
    ),
    Document(
        page_content="품질 평가: 정답률, 근거성, 응답 지연 시간을 공통 평가셋으로 측정한 뒤 운영 모델을 선정한다.",
        metadata={"category": "품질", "title": "운영 전 평가"},
    ),
]


persist_directory = "./chroma_ai_brief"
collection_name = "ai_brief"

# 기존 컬렉션이 있으면 재연결하고, 비어 있을 때만 최초 색인을 수행한다.
vectorstore = Chroma(
    collection_name= collection_name,
    embedding_function=embedding,
    persist_directory=persist_directory,
)

if vectorstore._collection.count() == 0:
    vectorstore = Chroma.from_documents(
        company_ai_documents,
        embedding,
        collection_name=collection_name,
        persist_directory=persist_directory,
        ids=[f"company-ai-{i}" for i in range(len(company_ai_documents))],
    )
    print("최초 색인 —", vectorstore._collection.count(), "개")
else:
    print("기존 색인 재연결 —", vectorstore._collection.count(), "개")
```
</div>

## 저장소에는 벡터만 살지 않는다

`similarity_search()` 가 돌려주는 `Document` 안에는 벡터랑 같이 저장해둔<br>`page_content`(원문)·`metadata`(category, title 등)가 그대로 들어있음.

<div class="til-code" markdown>
```python
hit = vectorstore.similarity_search("접근 권한 관리는 어떻게 하나요?", k=1)[0]
print("원문:", hit.page_content[:40], "…")
print("메타데이터:", hit.metadata)
```
</div>

!!! info "원문도 같이 돌아옴"
    저장소가 벡터랑 원문(`page_content`)·메타데이터(`metadata`)를 같이 들고 있다가  
    검색할 때 원문까지 같이 돌려줌. 그래서 검색 결과에서 벡터 숫자를 직접 볼 일은 거의 없고  
    `hit.page_content`, `hit.metadata` 로 바로 원문/출처를 확인하면 됨.

## 검색 거리 확인 — similarity_search_with_score

Chroma 거리는 작을수록 가깝고, 작은 거리부터 반환됨.

<div class="til-code" markdown>
```python hl_lines="3"
score_results = vectorstore.similarity_search_with_score("생성형 AI 보안 대책", k=3)

# 결과 
for document, distance in score_results:
    print(round(distance, 4), document.metadata["title"])
```
<div class="til-note" data-til-line="3" hidden>1.3618 도입 전 보안 검토<br>1.3676 접근 제어<br>1.3734 권한 회수</div>
</div>

!!! warning "거리 함수 기본값은 l2"
    거리 함수 자체를 안 정하면 Chroma는 기본으로 `l2`(유클리드 거리 제곱)를 씀.  
    `Chroma(...)` 만들 때 `collection_metadata={"hnsw:space": "cosine"}` 처럼 명시해야 코사인으로 바뀜.

## 메타데이터 필터 — filter

검색 후보를 metadata 조건 안으로 좁힘.

<div class="til-code" markdown>
```python hl_lines="4 8"
no_filter = vectorstore.similarity_search("정책 준비", k=3)
print("필터 없이:", [d.metadata["category"] for d in no_filter])

# 실행 결과
with_filter = vectorstore.similarity_search("정책 준비", k=3, filter={"category": "보안"})
print("category=보안 필터:", [d.metadata["category"] for d in with_filter])

# 실행 결과
with_filter2 = vectorstore.similarity_search("정책 준비", k=3, filter={"category": "교육"})
print("category=교육 필터:", [d.metadata["category"] for d in with_filter2])
```
<div class="til-note" data-til-line="4" hidden>필터 없이: ['보안', '품질', '보안']       <- 다른 범주(품질)가 섞여 나옴<br>category=보안 필터: ['보안', '보안', '보안']  <- 조건 건 대로 보안만 남음</div>
<div class="til-note" data-til-line="8" hidden>['교육']  <- 조건에 맞는 문서 1개만 남음 (직접 확인함)</div>
</div>

## 본문 필터 — where_document

`filter` 가 메타데이터 조건이면, `where_document` 는 본문 문자열 자체에 거는 조건.<br>`$contains` 로 본문에 그 글자가 실제로 있는지 검사함.

<div class="til-code" markdown>
```python hl_lines="7"
content_results = vectorstore.similarity_search_with_score(
    "생성형 AI 도입 준비",
    k=3,
    where_document={"$contains": "API 키"},
)

# 결과
for document, distance in content_results:
    print(round(distance, 4), document.metadata["title"])

# 본문에 'API 키' 다 포함: True
print("본문에 'API 키' 다 포함:", all("API 키" in d.page_content for d, _ in content_results))


# 메타데이터 필터 + 본문 필터를 같이 걸면 AND 조건
combined = vectorstore.similarity_search_with_score(
    "생성형 AI 도입 준비",
    k=3,
    filter={"category": "보안"},
    where_document={"$contains": "API 키"},
)

print("결합 필터 결과 수:", len(combined))
```
<div class="til-note" data-til-line="7" hidden>1.2998 도입 전 보안 검토<br>1.6259 접근 제어<br>1.6294 권한 회수</div>
</div>

## 궁금했던거 

`similarity_search()` 시그니처엔 `where_document`가 안 보이고 `filter`까지만 있는데<br>`similarity_search_with_score()`엔 `where_document`까지 있음.

<div class="til-code" markdown>
```python
# similarity_search() 에 where_document 인자 넣어보는 테스트

result_a = vectorstore.similarity_search("보안 정책", k=3, where_document={"$contains": "API 키"})
result_b = vectorstore.similarity_search_with_score("보안 정책", k=3, where_document={"$contains": "API 키"})
print([d.metadata["title"] for d in result_a])
print([d.metadata["title"] for d, _ in result_b])
print("둘이 같은 문서인가:", [d.page_content for d in result_a] == [d.page_content for d, _ in result_b])
```
</div>

!!! info "알고 보니 껍데기였음"
    `similarity_search()` 는 사실 `similarity_search_with_score()` 를 부르고 점수만 떼어내는 껍데기였음

<div class="til-code" markdown>
```python
def similarity_search(self, query, k=4, filter=None, **kwargs):
    docs_and_scores = self.similarity_search_with_score(query, k, filter=filter, **kwargs)
    return [doc for doc, _ in docs_and_scores]
```
</div>

!!! note "**kwargs 뒤에 숨은 인자"
    `where_document` 처럼 시그니처에 이름이 안 적힌 인자는 `**kwargs` 로 묶여서 그대로 다음 함수한테 전달됨.  
    VS Code 호버는 "이름 붙여 받는 인자"만 보여주니까 `**kwargs` 뒤에 숨은 진짜 동작까지는 안 보여준다는 걸 배움.

## 필터 연산자 정리

metadata 필터(`filter`) 연산자

<div class="til-code" markdown>
```python
- $eq (같음, 그냥 값만 써도 이거랑 같음)
- $ne(다름)
- $gt/$gte(초과/이상)
- $lt/$lte(미만/이하)
- $in(목록 중 하나)
- $nin(목록에 없음)
- 여러 조건 묶을 땐 $and/$or
```
</div>

본문 필터(`where_document`) 연산자

<div class="til-code" markdown>
```python
- $contains(포함)
- $not_contains(미포함)
- $regex/$not_regex (정규식도 가능)
```
</div>

## MMR — 유사도 검색의 중복을 줄이기

그냥 `similarity_search`는 쿼리랑 제일 비슷한 순서로만 뽑아서 내용 겹치는 문서가 몰릴 수 있음.<br>MMR은 "쿼리랑 비슷하면서 이미 뽑은 것들이랑 안 겹치는" 문서를 고름.<br>lambda_mult가 1에 가까우면 관련성, 0에 가까우면 다양성 위주

<div class="til-code" markdown>
```python hl_lines="5 9 14 16"
mmr_query = "사내 생성형 AI를 안전하게 도입하려면 무엇을 준비해야 하나요?"

similarity_results = vectorstore.similarity_search(mmr_query, k=4)

# 실행 결과: ['보안', '보안', '보안', '개인정보'] 
print("유사도 검색:", [d.metadata["category"] for d in similarity_results])


# mmr 원리
mmr_results = vectorstore.max_marginal_relevance_search(
    mmr_query, k=4, fetch_k=7, lambda_mult=0.5
)

# 실행 결과
print("MMR (lambda_mult=0.5):", [d.metadata["category"] for d in mmr_results])
# 실행 결과 
for lam in [0.1, 0.5, 0.9]:
    r = vectorstore.max_marginal_relevance_search(mmr_query, k=4, fetch_k=7, lambda_mult=lam)
    print(f"lambda_mult={lam}:", [d.metadata["category"] for d in r])
```
<div class="til-note" data-til-line="5" hidden>보안 3개가 몰림</div>
<div class="til-note" data-til-line="9" hidden>fetch_k=12개 후보 확보<br>→ 1번째: 쿼리와 가장 유사한 문서 선택<br>→ 2번째: (쿼리 유사도 - 1번째와의 유사도) 점수 최고인 문서 선택<br>→ 3번째: (쿼리 유사도 - max(1,2번째와의 유사도)) 점수 최고인 문서 선택<br>→ 4번째: 위 과정 반복<br>→ k=4개 채워지면 종료</div>
<div class="til-note" data-til-line="14" hidden>['보안', '개인정보', '비용', '교육']  <- 범주가 더 다양해짐</div>
<div class="til-note" data-til-line="16" hidden>lambda_mult=0.1: ['보안', '비용', '교육', '품질']   <- 다양성 위주라 보안 1개만<br>lambda_mult=0.5: ['보안', '개인정보', '비용', '교육']<br>lambda_mult=0.9: ['보안', '보안', '보안', '개인정보'] <- 관련성 위주라 유사도 검색과 비슷해짐</div>
</div>

!!! tip "fetch_k 를 k 보다 넉넉히"
    `fetch_k` 는 일단 후보로 몇 개 가져올지, `k` 는 최종 몇 개 돌려줄지임.  
    후보(`fetch_k`) 안에서만 다양성을 비교하니까 `fetch_k` 가 `k` 보다 너무 작으면  
    MMR을 걸어도 다양해질 여지가 별로 없다는 걸 위 비교로 알게 됨.

## retriever로 쓰는 MMR — 체인에 물릴 때의 형태

`as_retriever()` 로 감싸면 이후 LCEL 체인(`|`)에 바로 연결할 수 있는 형태가 됨.<br>`search_kwargs` 에 검색 옵션을 다 넣고 `invoke()` 로 질문함.

<div class="til-code" markdown>
```python hl_lines="14"
mmr_retriever = vectorstore.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 4, "fetch_k": 7, "lambda_mult": 0.3},
)
retriever_results = mmr_retriever.invoke(mmr_query)
print("retriever 결과:", [d.metadata["category"] for d in retriever_results])

method_results = vectorstore.max_marginal_relevance_search(mmr_query, k=4, fetch_k=7, lambda_mult=0.3)
print("메서드 직접 호출:", [d.metadata["category"] for d in method_results])

# retriever는 메서드를 그대로 감싸놓은 것뿐이라 옵션만 똑같이 주면 결과도 똑같음
print("둘이 같은 결과인가:", [d.page_content for d in retriever_results] == [d.page_content for d in method_results])

# 실행 결과 
```
<div class="til-note" data-til-line="14" hidden>retriever 결과: ['보안', '비용', '교육', '품질']<br>메서드 직접 호출: ['보안', '비용', '교육', '품질']<br>둘이 같은 결과인가: True</div>
</div>

## 문서 추가·삭제

<div class="til-code" markdown>
```python
before = vectorstore._collection.count()
new_ids = vectorstore.add_documents([
    Document(page_content="원격근무 정책: 생성형 AI 도입과 별개로 원격근무 시 VPN 접속을 의무화한다.",
             metadata={"category": "보안", "title": "원격근무 보안"})
])

after_add = vectorstore._collection.count()

hit = vectorstore.similarity_search("원격근무 VPN 규정", k=1)[0]
print("방금 넣은 문서가 검색되나:", hit.page_content[:20])

vectorstore.delete(ids=new_ids)
after_delete = vectorstore._collection.count()

print(before, after_add, after_delete)
```
</div>

같은 id로 문서를 다시 추가한 뒤 저장 개수가 증가하는지 확인 해보기

<div class="til-code" markdown>
```python
same_id_store = Chroma(collection_name="note-upsert", embedding_function=embedding)
same_id_store.add_documents([Document(page_content="A 원본")], ids=["fixed-id"])
before_upsert = same_id_store._collection.count()

same_id_store.add_documents([Document(page_content="A 수정본")], ids=["fixed-id"])  # 같은 id로 재추가
after_upsert = same_id_store._collection.count()

print(before_upsert, after_upsert)

# ['A 수정본']  <- 개수는 그대로고 내용만 새 걸로 덮어써짐
print(same_id_store.get(ids=["fixed-id"])["documents"])
```
</div>

!!! warning "같은 id 는 추가가 아니라 덮어쓰기"
    답: 개수 안 늘어남. 같은 id로 `add_documents()` 하면 추가가 아니라 **덮어쓰기(upsert)**.  
    id를 안 주고 add하면 매번 랜덤 id라 그때는 진짜 중복으로 쌓임 — id를 주느냐 마느냐 차이임.

## 재연결 — 재색인 없이 저장소 다시 열기

<div class="til-code" markdown>
```python
reopened = Chroma(
    collection_name=collection_name,
    embedding_function=embedding,
    persist_directory=persist_directory,   # 아까 저장해 둔 그 폴더
)

print("재연결 —", reopened._collection.count(), "개 (재색인 없이, 즉시)")

hit = reopened.similarity_search("퇴사자 권한 회수", k=1)[0]
print("검색도 그대로:", hit.metadata["title"])
```
</div>

## FAISS 기본 실습

같은 문서·같은 임베딩이면 Chroma든 FAISS든 검색 결과가 같아야 함.

<div class="til-code" markdown>
```python
faiss_store = FAISS.from_documents(company_ai_documents, embedding)  # 인메모리

faiss_hit = faiss_store.similarity_search(mmr_query, k=1)[0]
chroma_hit = vectorstore.similarity_search(mmr_query, k=1)[0]
print("FAISS Top-1:", faiss_hit.metadata["title"])
print("Chroma Top-1:", chroma_hit.metadata["title"])
print("같은 결과인가:", faiss_hit.page_content == chroma_hit.page_content)
print("FAISS 벡터 수:", faiss_store.index.ntotal)
```
</div>

## FAISS 수동 영속화 — 저장하고 다시 열기

Chroma는 만들 때부터 폴더에 자동 저장되지만, FAISS는 기본이 인메모리라<br>`save_local()` 을 직접 안 부르면 프로세스 끝나는 순간 사라짐.

<div class="til-code" markdown>
```python
faiss_store.save_local("./faiss_company_ai")

from pathlib import Path
saved_files = sorted(p.name for p in Path("./faiss_company_ai").glob("index.*"))

# 실행 결과: ['index.faiss', 'index.pkl']  <- 벡터 파일 + 원문/메타데이터 파일
print("저장된 파일:", saved_files)

faiss_reopened = FAISS.load_local(
    "./faiss_company_ai",
    embedding,
    allow_dangerous_deserialization=True,
)

print("재연결 후 벡터 수:", faiss_reopened.index.ntotal)
reopened_hit = faiss_reopened.similarity_search(mmr_query, k=1)[0]
print("재연결 후 Top-1이 저장 전과 같은가:", reopened_hit.page_content == faiss_hit.page_content)
```
</div>

!!! danger "내가 만든 폴더에만 True"
    `allow_dangerous_deserialization=True` 안 주면 아예 로드가 막힘.  
    **내가** 직접 만들고 손 안 댄 로컬 폴더에만 True로 열 것.

## 기본 미션 — 저장소 상태 검사 함수

Chroma·FAISS의 저장 개수와 검색 결과를 한 번에 비교하는 함수.

<div class="til-code" markdown>
```python
def inspect_vectorstore(store, store_name, document_count, questions):
    rows = []
    for question in questions:
        document, distance = store.similarity_search_with_score(question, k=1)[0]
        rows.append({
            "question": question,
            "title": document.metadata.get("title"),
            "distance": round(distance, 4),
        })
    return {"store": store_name, "count": document_count, "results": rows}


questions = ["접근 권한 관리", "토큰 사용량 모니터링", "직원 프롬프트 교육"]
print(inspect_vectorstore(vectorstore, "Chroma", vectorstore._collection.count(), questions))
print(inspect_vectorstore(faiss_reopened, "FAISS", faiss_reopened.index.ntotal, questions))
```
</div>

## 종합 연습 — 사내 운영 가이드 저장소로 처음부터 다시

여기부터는 원본 노트북의 "종합 연습" 파트. `practice_documents` 로<br>영속 저장 -> 검색 -> 필터 -> MMR -> 추가삭제 -> 재연결 -> FAISS까지 한 바퀴 더 돌림.

<div class="til-code" markdown>
```python
practice_documents = [
    Document(
        page_content="재택근무는 주 2일까지 가능하며, 전날 오후 6시까지 인사 포털에서 신청합니다.",
        metadata={"title": "재택근무 신청", "department": "인사", "topic": "근무", "year": 2026},
    ),
    Document(
        page_content="국내 출장은 교통비와 숙박비 영수증을 귀환 후 5영업일 안에 경비 시스템에 등록합니다.",
        metadata={"title": "출장비 정산", "department": "재무", "topic": "경비", "year": 2026},
    ),
    Document(
        page_content="2025년 국내 출장비는 귀환 후 10영업일 안에 정산하도록 운영했습니다.",
        metadata={"title": "출장비 정산 이전 규정", "department": "재무", "topic": "경비", "year": 2025},
    ),
    Document(
        page_content="외부 저장장치는 보안팀이 승인한 암호화 USB만 사용할 수 있으며 반출입 기록을 남겨야 합니다.",
        metadata={"title": "외부 저장장치", "department": "보안", "topic": "정보보호", "year": 2026},
    ),
    Document(
        page_content="생성형 AI 사내 교육은 분기마다 실시하며 기밀정보 입력 금지와 결과 검증 방법을 포함합니다.",
        metadata={"title": "생성형 AI 교육", "department": "교육", "topic": "AI", "year": 2026},
    ),
    Document(
        page_content="종합 건강검진은 연 1회 지원되며 예약 결과를 복지 포털에 등록합니다.",
        metadata={"title": "건강검진 지원", "department": "복지", "topic": "건강", "year": 2026},
    ),
]
practice_ids = [
    "guide-remote-work", "guide-business-trip", "guide-business-trip-2025",
    "guide-usb-security", "guide-ai-training", "guide-health-check",
]
```
</div>

Chroma 벡터스토어 로컬 저장 및 중복 방지

<div class="til-code" markdown>
```python hl_lines="8"
practice_embedding = embedding
practice_store = Chroma(
    collection_name="company-guide-practice",
    embedding_function=practice_embedding,
    persist_directory="./chroma_company_guide_practice",
)

# chroma 객체 메서드 get() -> get 안에 인자는 필터링 값을 넣어줘야함
print(practice_store.get())


# 이미 저장된 id는 건너뛰고, 없는 것만 골라서 추가 (재실행해도 중복 안 쌓이게)
existing_ids = set(practice_store.get(ids=practice_ids)["ids"])

new_docs = [doc for doc, i in zip(practice_documents, practice_ids) if i not in existing_ids]
new_ids = [i for i in practice_ids if i not in existing_ids]

if new_docs:
    practice_store.add_documents(documents=new_docs, ids=new_ids)

print(practice_store._collection.count())
```
<div class="til-note" data-til-line="8" hidden>{'ids': [],<br>'embeddings': None,<br>'documents': [],<br>'uris': None,<br>'included': ['metadatas', 'documents'],<br>'data': None,<br>'metadatas': []}</div>
</div>

similarity_search - 검색

<div class="til-code" markdown>
```python hl_lines="10"
question = "재택근무는 며칠 가능하고 언제 신청하나요?"
top2 = practice_store.similarity_search(question, k=2)

# 실행 결과: ['재택근무 신청', '출장비 정산 이전 규정']
print([d.metadata["title"] for d in top2])

question2 = "출장비는 언제까지 정산하나요?"
scored = practice_store.similarity_search_with_score(question2, k=3)

# 실행 결과
for d, s in scored:
    print(round(s, 4), d.metadata["title"])
```
<div class="til-note" data-til-line="10" hidden>0.4298 출장비 정산 이전 규정     <- 2025년 옛날 규정(10영업일)<br>0.7171 재택근무 신청<br>0.9742 출장비 정산             <- 진짜 최신(2026, 5영업일) 규정은 오히려 3등</div>
</div>

!!! question "왜 옛날 규정이 더 가깝다고 나올까"
    위 "거리 점수" 결과에서 진짜 정답 문서 ("출장비 정산", 2026년, 5영업일)보다  
    옛날 규정 문서("출장비 정산 이전 규정",2025년, 10영업일)가 더 가깝다고 나옴.  
    겹치는지만 보지 문장 의미는 모르니까, "정산" "출장비" 같은 단어가 똑같이  
    들어간 옛날 문서를 최신 문서보다 더 가깝다고 판단한 것.  
    "임베딩이 단어 겹침만 볼 때는 최신/구버전을 metadata(`year`)로 걸러줘야 한다"  
    는 걸 배움

<div class="til-code" markdown>
```python
# 실행 결과: ['보안']
by_department = practice_store.similarity_search("저장장치 사용 규칙", filter={"department": "보안"})
print([d.metadata["department"] for d in by_department])

by_content = practice_store.similarity_search_with_score(
    "경비 처리 절차", where_document={"$contains": "영수증"} )

# 실행 결과: ['국내 출장은 교통비와 숙']
print([d.page_content[:15] for d, _ in by_content])

# year=2026 필터 + 본문 '영수증' 필터를 같이 걸면 최신 규정만 정확히 남음
rag_style = practice_store.similarity_search_with_score(
    "2026년 출장비 정산은 언제까지 해야 하나요?",
    k=3,
    filter={"year": 2026},
    where_document={"$contains": "영수증"},
)
for d, s in rag_style:
    print(round(s, 4), d.metadata["title"], "|", d.page_content)
```
</div>

!!! tip "후보를 먼저 좁혀두기"
    임베딩 거리 점수가 항상 "가장 맞는 답"을 1등으로 주는 게 아님.  
    **내가** metadata(`year`)나 본문 조건(`where_document`)으로 후보를 먼저 좁혀두면,  
    임베딩이 살짝 헷갈려도 결과는 정확하게 나옴.

## 문서 추가·삭제·재연결 — practice_store로 한 번 더

<div class="til-code" markdown>
```python
new_doc = Document(
    page_content="회의실 예약은 사용 하루 전까지 협업 포털에서 신청합니다.",
    metadata={"title": "회의실 예약", "department": "인사", "topic": "회의실", "year": 2026},
)
before = practice_store._collection.count()
temp_ids = practice_store.add_documents([new_doc])
after_add = practice_store._collection.count()
practice_store.delete(ids=temp_ids)
after_delete = practice_store._collection.count()

# 실행 결과: 6 7 6  
print(before, after_add, after_delete)

practice_reopened = Chroma(
    collection_name="company-guide-practice",
    embedding_function=practice_embedding,
    persist_directory="./chroma_company_guide_practice",
)

base_result = practice_store.similarity_search("건강검진 지원", k=1)[0].page_content
reopened_result = practice_reopened.similarity_search("건강검진 지원", k=1)[0].page_content

# 실행 결과: True  (재색인 없이 그대로 — 직접 확인함)
print(base_result == reopened_result)
```
</div>

## practice_documents로 FAISS까지

벡터 저장소가 달라도 임베딩이 같으면 검색 시 결과가 같음

<div class="til-code" markdown>
```python
practice_faiss_store = FAISS.from_documents(practice_documents, embedding=practice_embedding)
faiss_q = "암호화된 외부 저장장치 규칙"

faiss_result = practice_faiss_store.similarity_search(faiss_q, k=1)[0]
chroma_result = practice_store.similarity_search(faiss_q, k=1)[0]

print("FAISS:", faiss_result.metadata["title"], "| Chroma:", chroma_result.metadata["title"])
print("같은가:", faiss_result.page_content == chroma_result.page_content)


practice_faiss_store.save_local("./faiss_company_guide_practice")
practice_faiss_reopened = FAISS.load_local(
    "./faiss_company_guide_practice", practice_embedding, allow_dangerous_deserialization=True
)

# 실행 결과: 6
print(practice_faiss_reopened.index.ntotal)
```
</div>

## RAG 체인



<div class="til-code" markdown>
```python
# 문맥 문자열로 합치기 -> 프롬프트에 끼워넣기 -> LLM -> 문자열 파서, 순서로 연결.
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

load_dotenv()

def format_practice_documents(documents):
    return "\n\n".join(
        f"[{document.metadata['title']} | {document.metadata['year']}년]\n{document.page_content}"
        for document in documents
    )

practice_rag_retriever = practice_reopened.as_retriever(
    search_type= "mmr",
    search_kwargs={
        "k": 3,
        "fetch_k": 6,
        "lambda_mult": 0.5,
        "filter": {"year": 2026},
    },
)

practice_rag_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "당신은 사내 운영 가이드 질의응답 도우미입니다. "
            "제공된 문맥만 사용해 두 문장 이내로 답하세요. "
            "문맥에 근거가 없으면 '제공된 문서에서 근거를 찾지 못했습니다.'라고 답하세요.",
        ),
        ("human", "문맥:\n{context}\n\n질문: {question}"),
    ]
)

practice_rag_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
)


practice_rag_chain = (
    {
        "context": practice_rag_retriever | format_practice_documents,
        "question": RunnablePassthrough(),
    }
    | practice_rag_prompt
    | practice_rag_llm
    | StrOutputParser()
)

practice_rag_chain.invoke("2026년 출장비 정산은 언제까지 해야 하나요?")
```
</div>

!!! info "LCEL 에서 딕셔너리는 병렬"
    딕셔너리 안의 여러 키에는 원본 입력이 각 키에 그대로 복제되어 전달됨  
    LCEL에서 딕셔너리는 병렬 실행 — RunnableParallel로 바뀌는 문법임  
    A | B (한 키 안의 파이프)는 순차 실행이며 A의 출력이 B의 입력으로 들어가는 구조임