---
title: 임베딩 유사도 실측
date: 2026-09-06
tags: [embedding, rag]
---

# 임베딩 유사도 실측 — OpenAI vs BGE-M3, 코사인 유사도로 Top-K 검색 직접 구현

> 원본 코드: [`06_embedding.py`](06_embedding.py)

## 시작 전에

문장을 벡터로 바꾸고, 코사인 유사도로 "얼마나 비슷한지"를 숫자로 재고,<br>Top-K 검색을 직접 구현해서 OpenAI 임베딩과 BGE-M3를 같은 입력으로 비교함.

## 문장을 벡터로 바꾸기 — OpenAIEmbeddings

`embed_query()` 하나 호출해서 반환값 자료형·차원·값을 확인.

<div class="til-code" markdown>
```python
import os, logging
os.environ["TQDM_DISABLE"] = "1"

from dotenv import load_dotenv
load_dotenv()   

from langchain_openai import OpenAIEmbeddings

embedding = OpenAIEmbeddings(model="text-embedding-3-small")

# 입력은 문장 1개 → 반환값은 실수 1536개짜리 리스트 1개
vec = embedding.embed_query("카카오가 자체 개발 모델 카나나를 공개했다")

print("벡터 길이(차원):", len(vec))          # 1536
print("앞 5개 숫자:", [round(v, 4) for v in vec[:5]])
```
</div>

!!! note "embed_query 와 embed_documents"
    `embed_query()` 는 문장 "하나"를 벡터 하나로 바꿈. 여러 문장은 `embed_documents()`.

## 코사인 유사도 — 값이 클수록 더 비슷함

두 벡터가 얼마나 같은 방향을 보는지를 -1~1 사이 숫자로 나타냄. 1에 가까울수록 비슷함.

<div class="til-code" markdown>
```python hl_lines="7"
from langchain_community.utils.math import cosine_similarity

v1 = embedding.embed_query("카카오가 카나나 테크니컬 리포트를 공개했다")
v2 = embedding.embed_query("카카오가 개발한 LLM의 기술 문서가 나왔다")     # 뜻이 비슷 
v3 = embedding.embed_query("오늘 점심은 김치찌개가 좋겠다")               # 무관한 주제

# `cosine_similarity()` 는 항상 2차원 배열을 받고 2차원 배열을 돌려줌.
result = cosine_similarity([v1], [v2])   # -> array([[0.26700678]])
score = result[0, 0]

print("비슷한 뜻 쌍:", round(score, 3))
print("무관한   쌍:", round(cosine_similarity([v1], [v3])[0, 0], 3))
```
<div class="til-note" data-til-line="7" hidden>벡터 하나끼리 비교해도 결과는 `[[0.267]]` 처럼 1x1 배열이라, 스칼라값을 꺼내려면<br>`result[0, 0]` 처럼 "행 인덱스, 열 인덱스" 순서로 넣어야함.</div>
</div>

## 유사도 행렬 — 네 문장을 서로 비교

`cosine_similarity(X, Y)` 에서 X, Y 가 몇 개짜리 배열인지에 따라 결과 shape이 달라짐.

!!! info "shape 규칙 정리"
    cosine_similarity(X, Y) 규칙 정리  
    X: 벡터 n1개 담은 2차원 배열, Y: 벡터 n2개 담은 2차원 배열 -> 결과 shape (n1, n2)  
    cosine_similarity([vi], vecs)  -> vi 1개 vs 전체 4개  -> (1, 4)  
    cosine_similarity(vecs, vecs)  -> 전체 4개 vs 전체 4개(자기자신 포함) -> (4, 4)  
    cosine_similarity([v1], [v2])  -> 1개 vs 1개 -> (1, 1)

<div class="til-code" markdown>
```python hl_lines="13"
sentences = [
    "카카오가 카나나 리포트를 공개했다",         # A
    "카카오의 새 언어모델이 발표됐다",          # B (A와 비슷)
    "구글이 오픈소스 모델 젬마 3를 공개했다",    # C (모델 발표라는 점은 비슷, 회사 다름)
    "주말에 등산을 다녀왔다",                 # D (무관)
]
vecs = embedding.embed_documents(sentences)   # [[임베딩값...], [임베딩값...], ...] 문장 개수만큼

labels = ["A", "B", "C", "D"]
print("     " + "      ".join(labels))

for i, vi in enumerate(vecs):
    row = [f"{s:.3f}" for s in cosine_similarity([vi], vecs)[0]]
    print(labels[i], " ", "  ".join(row))
```
<div class="til-note" data-til-line="13" hidden>`cosine_similarity([vi], vecs)` 는 (1, 4) 배열이라 `[0]` 으로 그 한 줄(행)을 꺼냄.</div>
</div>

!!! example "결과 — 유사도 행렬"
    `결과`  
    A      B      C      D  
    A  1.000  0.436  0.259  0.132  
    B  0.436  1.000  0.384  0.139  
    C  0.259  0.384  1.000  0.163  
    D  0.132  0.139  0.163  1.000  
    A-B(같은 회사·모델발표) > A-C(모델발표는 같은데 회사 다름) > A-D(무관) 순서로 나옴.  
    주제·대상이 가까울수록 점수가 높게 나온 사례. 항상 이렇다는 보장은 아니고 이 4문장에서만 그럼.

## Top-K 검색 직접 구현

`similarity_search()` 내부에서 실제로 벌어지는 일을 손으로 그대로 짜봄:<br>질문 임베딩 → 문서별 유사도 계산 → 점수로 정렬 → 상위 K개.

<div class="til-code" markdown>
```python hl_lines="15"
documents = [
    "카카오가 카나나의 테크니컬 리포트를 공개했다.",
    "구글이 단일 GPU로 구동 가능한 젬마 3를 공개했다.",
    "엔비디아가 GTC에서 신규 AI 칩 로드맵을 발표했다.",
    "2024년 튜링상은 강화학습 연구자들이 수상했다.",
    "옥스퍼드 연구는 AI 채용에서 실무기술이 중요하다고 밝혔다.",
]
doc_vecs = embedding.embed_documents(documents)          # 문서를 전부 벡터로 (색인)

question = "카카오가 만든 AI 모델 소식 알려줘"
q_vec = embedding.embed_query(question)                   # 질문도 벡터로

sims = cosine_similarity([q_vec], doc_vecs)[0]             # 질문 1개 vs 문서 5개 유사도

ranked = sorted(range(len(documents)), key=lambda i: sims[i], reverse=True)

print("질문:", question)

for rank, i in enumerate(ranked[:3], 1):                  # 상위 K=3
    print(f"{rank}위 ({sims[i]:.3f}) {documents[i]}")
```
<div class="til-note" data-til-line="15" hidden>`documents` 의 "인덱스"를 정렬하는 거지 문장 자체를 정렬하는 게 아님.<br>`key=lambda i: sims[i]` 로 각 인덱스의 점수를 기준 삼고, `reverse=True` 로 높은 점수부터.</div>
</div>

!!! question "왜 카카오 문장이 1위가 아닌가"
    `결과`  
    질문: 카카오가 만든 AI 모델 소식 알려줘  
    1위 (0.485) 엔비디아 문장  
    `카카오 모델 소식`을 물었는데 카카오 문장이 1위가 아니라 2위로 나옴.  
    임베딩·유사도 계산·정렬 로직 자체는 의도대로 다 돌아갔고, 이건 계산 버그가 아니라  
    `text-embedding-3-small` 이 이 입력에서 실제로 그렇게 벡터를 배치했다는 뜻.  
    → "검색이 항상 원하는 문서를 1위로 준다"는 보장이 없다는 걸 숫자로 확인한 셈.

## 검산 — 빈칸 없이 같은 패턴으로 새 질문 테스트

위에서 만든 `doc_vecs` 를 그대로 재사용해서 다른 질문의 Top-1만 다시 확인.

<div class="til-code" markdown>
```python
practice_question = "구글이 공개한 모델은?"
practice_vector = embedding.embed_query(practice_question)

practice_scores = cosine_similarity([practice_vector], doc_vecs)[0]

practice_order = sorted(range(len(documents)), key=lambda i: practice_scores[i], reverse=True)

assert documents[practice_order[0]].startswith("구글")
print(documents[practice_order[0]])   # 구글이 단일 GPU로 구동 가능한 젬마 3를 공개했다.
```
</div>

!!! success "이번엔 기대한 대로"
    이건 기대한 대로 구글 문장이 1위로 나옴. 질문 표현과 문서 표현이 겹치는 단어(구글)가  
    있을 때는 위 카카오 사례보다 순위가 더 안정적으로 나온다는 뜻으로 읽음.

## 검색 한계 확인 — 유의어 쌍 vs 무관 쌍

표현은 다른데 뜻이 같은 문장 쌍, 그리고 뜻도 표현도 다른 무관 문장 쌍을 같은 기준으로 잼.

<div class="til-code" markdown>
```python
test_pairs = [
    ("책을 빌리려면 어떻게 하나요?", "도서 대출은 회원증이 필요합니다", "유의어 (빌리다/대출)"),
    ("책을 빌리려면 어떻게 하나요?", "김치찌개 레시피를 알려주세요",   "무관"),
    ("환불은 어떻게 받나요?",       "구매 취소 및 반품 절차 안내입니다", "유의어 (환불/반품)"),
    ("환불은 어떻게 받나요?",       "내일은 전국에 비가 내리겠습니다",   "무관"),
]

for a, b, tag in test_pairs:
    sim = cosine_similarity([embedding.embed_query(a)], [embedding.embed_query(b)])[0, 0]
    print(f"{sim:.3f}  {tag}")
```
</div>

!!! warning "유의어가 항상 더 높지는 않음"
    `결과`  
    0.108  유의어 (빌리다/대출)   ← 무관 쌍(0.211)보다 오히려 낮음  
    0.211  무관  
    0.291  유의어 (환불/반품)    ← 무관 쌍(0.200)보다 높음  
    0.200  무관  
    핵심은 `빌리다/대출` 유의어 쌍이 무관 쌍보다 점수가 "낮게" 나온 것.  
    즉 OpenAI 임베딩이 늘 유의어를 더 높게 쳐주는 게 아니라는 걸 직접 확인함.

## BGE-M3로 같은 실험 재현

다국어 임베딩 모델 BGE-M3(`BAAI/bge-m3`)를 로컬에 띄워서 위에서 사용했던 같은 test_pairs 문장으로 비교.<br>첫 실행에서만 Hugging Face에서 모델을 내려받고, 그다음부턴 로컬 캐시를 씀.

<div class="til-code" markdown>
```python
from langchain_huggingface import HuggingFaceEmbeddings

bge = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")   # 로컬 캐시에 없으면 여기서 다운로드함

for a, b, tag in test_pairs:
    sim = cosine_similarity([bge.embed_query(a)], [bge.embed_query(b)])[0, 0]
    print(f"{sim:.3f}  {tag}")
```
</div>

!!! success "BGE-M3 는 유의어가 더 높게 나옴"
    `결과`  
    0.697  유의어 (빌리다/대출)  
    0.376  무관  
    0.724  유의어 (환불/반품)  
    0.404  무관  
    유의어가 원하던대로 유사도가 더 높게 측정됨

<div class="til-code" markdown>
```python
documents = [
    "카카오가 카나나의 테크니컬 리포트를 공개했다.",
    "구글이 단일 GPU로 구동 가능한 젬마 3를 공개했다.",
    "엔비디아가 GTC에서 신규 AI 칩 로드맵을 발표했다.",
    "2024년 튜링상은 강화학습 연구자들이 수상했다.",
    "옥스퍼드 연구는 AI 채용에서 실무기술이 중요하다고 밝혔다.",
]

question = "카카오가 만든 AI 모델 소식 알려줘"

doc_vecs_bge = bge.embed_documents(documents)
q_vec_bge = bge.embed_query(question)

sims_bge = cosine_similarity([q_vec_bge], doc_vecs_bge)[0]
ranked_bge = sorted(range(len(documents)), key=lambda i: sims_bge[i], reverse=True)

print("질문:", question)

for rank, i in enumerate(ranked_bge[:3], 1):
    print(f"{rank}위 ({sims_bge[i]:.3f}) {documents[i]}")
```
</div>

!!! example "결과 — BGE-M3 Top-K"
    `결과`  
    질문: 카카오가 만든 AI 모델 소식 알려줘  
    1위 (0.585) 카카오가 카나나의 테크니컬 리포트를 공개했다.  
    2위 (0.509) 엔비디아가 GTC에서 신규 AI 칩 로드맵을 발표했다.  
    3위 (0.475) 구글이 단일 GPU로 구동 가능한 젬마 3를 공개했다.  
    "BGE-M3가 항상 더 낫다"가 아니라 "이 입력에서는" 더 잘 맞았다는 것만 확인한 거임.

## 교차언어 검색 + 벡터 차원 고정 확인

BGE-M3에 한국어 질문을 넣고 영어 문서 중에서 찾게 함. 그리고 입력 길이가 달라도 벡터 차원은 항상 고정인지 직접 재봄.

<div class="til-code" markdown>
```python
mixed_docs = [
    "Google released Gemma 3, an open-source model that runs on a single GPU.",
    "NVIDIA announced its new AI chip roadmap at GTC 2025.",
    "카카오가 카나나 테크니컬 리포트를 공개했다.",
    "The 2024 Turing Award went to two reinforcement learning researchers.",
]

mixed_vecs = bge.embed_documents(mixed_docs)

cross_question = "구글이 공개한 경량 오픈소스 모델은?"          # 한국어 질문, 문서는 영어 위주
q_vec_cross = bge.embed_query(cross_question)

mixed_sims = cosine_similarity([q_vec_cross], mixed_vecs)[0]
best = max(range(len(mixed_docs)), key=lambda i: mixed_sims[i])

for i, d in enumerate(mixed_docs):
    mark = " [1위]" if i == best else ""
    print(f"({mixed_sims[i]:.3f}) {d[:60]}{mark}")
```
</div>

!!! example "결과 — 교차언어 검색"
    `결과`  
    (0.629) Google released Gemma 3, an open-source model that runs on a [1위]  
    (0.430) NVIDIA announced its new AI chip roadmap at GTC 2025.  
    (0.420) 카카오가 카나나 테크니컬 리포트를 공개했다.  
    (0.318) The 2024 Turing Award went to two reinforcement learning res  
    한국어 질문("구글이 공개한 경량 오픈소스 모델은?")으로 검색했는데 영어 Gemma 3 문장이  
    0.629로 1위. 언어가 달라도 뜻이 통하면 검색이 됨(교차언어).

<div class="til-code" markdown>
```python
short = bge.embed_query("카나나")                                 # 3글자
long_ = bge.embed_query("카나나는 카카오가 개발한 언어모델로, " * 20)    # 수백 자

print("BGE-M3 :", len(short), "차원 /", len(long_), "차원")   # 입력 길이 달라도 차원 같음
print("OpenAI :", len(vec), "차원")                           # OpenAIEmbeddings로 임베딩한 값
```
</div>

!!! info "차원은 모델이 정함"
    3글자짜리 입력이든 수백 자짜리 입력이든 BGE-M3는 항상 1024차원, OpenAI는 항상 1536차원.  
    → **임베딩 모델이** 벡터 차원 개수를 정하고, **입력 문장의 길이는** 차원 수에 영향 안 줌.

## 두 임베딩 모델을 섞으면 안 되는 이유

OpenAI 벡터는 1536차원, BGE-M3 벡터는 1024차원 — 좌표 공간 자체가 다름.<br>그래서 문서는 A모델로, 질문은 B모델로 임베딩하면 비교 자체가 성립 안 함.

!!! danger "색인과 검색은 반드시 같은 모델로"
    색인(문서를 벡터로 바꿔서 저장하는 것)과 검색(질문을 벡터로 바꿔서 비교하는 것)은  
    **반드시** 같은 임베딩 모델을 써야함. 모델을 바꾸면 기존 문서 전체를 다시 색인해야함.

## 전체 RAG 파이프라인에서 임베딩 모델 비교

같은 한국어 안내문 4개를 OpenAI/BGE-M3 각각으로 Chroma에 색인하고,<br>검색된 근거를 `gpt-4o-mini` 에 넘겨서 최종 답변까지 비교함.

<div class="til-code" markdown>
```python
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

korean_rag_documents = [
    Document(
        page_content="도서 대출은 사원증을 제시한 뒤 대출대에서 신청합니다. 대출 기간은 14일입니다.",
        metadata={"id": "library", "title": "도서 대출"},
    ),
    Document(
        page_content="구매를 취소하면 결제 수단으로 환불됩니다. 환불 신청은 결제일로부터 7일 안에 접수합니다.",
        metadata={"id": "refund", "title": "환불"},
    ),
    Document(
        page_content="연차 휴가는 입사 첫해에 매월 1일씩 발생하며, 다음 해부터는 매년 15일이 부여됩니다.",
        metadata={"id": "leave", "title": "연차 휴가"},
    ),
    Document(
        page_content="사원증을 분실하면 보안 포털에서 즉시 사용 중지를 신청하고 새 카드를 발급받아야 합니다.",
        metadata={"id": "badge", "title": "사원증 분실"},
    ),
]

korean_search_cases = [
    {"question": "책을 빌리려면 무엇이 필요한가요?", "expected_id": "library"},
    {"question": "결제한 상품을 되돌리고 싶어요.", "expected_id": "refund"},
    {"question": "올해 쉴 수 있는 날은 어떻게 생기나요?", "expected_id": "leave"},
]

embedding_models = {"OpenAI text-embedding-3-small": embedding, "BGE-M3": bge}
rag_vector_stores = {}

for model_name, current_embedding in embedding_models.items():
    rag_vector_stores[model_name] = Chroma.from_documents(
        documents=korean_rag_documents,
        embedding=current_embedding,
        collection_name=f"embedding_rag_{uuid4().hex}",
    )
    print(model_name, "색인 완료")
```
</div>

!!! example "rag_vector_stores 확인"
    rag_vector_stores 확인  
    {'OpenAI text-embedding-3-small': <langchain_chroma.vectorstores.Chroma object at 0x16118b650>,  
    'BGE-M3': <langchain_chroma.vectorstores.Chroma object at 0x16eac8740> }

<div class="til-code" markdown>
```python
rag_search_results = {}
for case in korean_search_cases:
    question_ = case["question"]
    expected_id = case["expected_id"]
    rag_search_results[question_] = {}

    print("\n질문:", question_)
    print("기대 문서:", expected_id)

    for model_name, vector_store in rag_vector_stores.items():
        document = vector_store.similarity_search(question_, k=1)[0]
        rag_search_results[question_][model_name] = document
        matched = document.metadata["id"] == expected_id

        print(f"{model_name}: {document.metadata['title']} | 기대 문서와 일치: {matched}")
        print("  ", document.page_content)
```
</div>

??? example "결과 — 모델별 검색 비교 (3개 질문)"
    `결과`  
    질문: 책을 빌리려면 무엇이 필요한가요?  
    기대 문서: library  
    OpenAI text-embedding-3-small: 사원증 분실 | 기대 문서와 일치: False  
    사원증을 분실하면 보안 포털에서 즉시 사용 중지를 신청하고 새 카드를 발급받아야 합니다.  
    BGE-M3: 도서 대출 | 기대 문서와 일치: True  
    도서 대출은 사원증을 제시한 뒤 대출대에서 신청합니다. 대출 기간은 14일입니다.  
    질문: 결제한 상품을 되돌리고 싶어요.  
    기대 문서: refund  
    OpenAI text-embedding-3-small: 환불 | 기대 문서와 일치: True  
    구매를 취소하면 결제 수단으로 환불됩니다. 환불 신청은 결제일로부터 7일 안에 접수합니다.  
    BGE-M3: 환불 | 기대 문서와 일치: True  
    구매를 취소하면 결제 수단으로 환불됩니다. 환불 신청은 결제일로부터 7일 안에 접수합니다.  
    질문: 올해 쉴 수 있는 날은 어떻게 생기나요?  
    기대 문서: leave  
    OpenAI text-embedding-3-small: 연차 휴가 | 기대 문서와 일치: True  
    연차 휴가는 입사 첫해에 매월 1일씩 발생하며, 다음 해부터는 매년 15일이 부여됩니다.  
    BGE-M3: 연차 휴가 | 기대 문서와 일치: True  
    연차 휴가는 입사 첫해에 매월 1일씩 발생하며, 다음 해부터는 매년 15일이 부여됩니다.

<div class="til-code" markdown>
```python hl_lines="21"
rag_prompt = PromptTemplate.from_template(
    "다음 문맥만 사용하여 질문에 답하세요. "
    "문맥에 답의 근거가 없으면 '제공된 문서에서 근거를 찾지 못했습니다.'라고 답하세요. "
    "답변은 두 문장 이내의 한국어로 작성하세요.\n\n"
    "문맥:\n{context}\n\n질문: {question}\n답변:"
)

def format_docs(documents_):
    return "\n\n".join(d.page_content for d in documents_)

def build_rag_chain(retriever, llm):
    return (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | rag_prompt | llm | StrOutputParser()
    )

rag_question = "책을 빌리려면 무엇이 필요한가요?"
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)


for model_name, vector_store in rag_vector_stores.items():
    retriever = vector_store.as_retriever(search_kwargs={"k": 1})
    retrieved_document = retriever.invoke(rag_question)[0]

    rag_chain = build_rag_chain(retriever, llm)
    response = rag_chain.invoke(rag_question)

    print("\n" + "=" * 70)
    print(model_name)
    print("검색 근거:", retrieved_document.metadata["title"])
    print(retrieved_document.page_content)
    print("RAG 답변:", response)
```
<div class="til-note" data-til-line="21" hidden>{'OpenAI text-embedding-3-small': <langchain_chroma.vectorstores.Chroma object at 0x16118b650>,<br>'BGE-M3': <langchain_chroma.vectorstores.Chroma object at 0x16eac8740> }</div>
</div>

??? example "결과 — 모델별 RAG 답변"
    `결과`  
    ======================================================================  
    OpenAI text-embedding-3-small  
    검색 근거: 사원증 분실  
    사원증을 분실하면 보안 포털에서 즉시 사용 중지를 신청하고 새 카드를 발급받아야 합니다.  
    RAG 답변: 제공된 문서에서 근거를 찾지 못했습니다.  
    ======================================================================  
    BGE-M3  
    검색 근거: 도서 대출  
    도서 대출은 사원증을 제시한 뒤 대출대에서 신청합니다. 대출 기간은 14일입니다.  
    RAG 답변: 책을 빌리려면 사원증을 제시해야 합니다. 대출대에서 신청하면 됩니다.

!!! warning "확인 문구를 실제 출력과 대조 안 했음"
    `관찰`  
    실제 LLM 답변에는 `사원증`만 있고 `14일`은 없음. 확인 문구를 실제 출력값과 대조 안 하고 적었던 것.  
    검색이 맞아도 LLM이 문맥의 모든 숫자를 다 답변에 넣어주는 건 아니라는 뜻으로 정정함.

## 개인 실습 — 코사인 유사도를 직접 구현하기

cos(θ) = (a·b) / (‖a‖ × ‖b‖) — 분자는 내적, 분모는 두 벡터 크기(norm)의 곱.

<div class="til-code" markdown>
```python
import numpy as np
 
def cosine_similarity_impl(a, b) -> float:
    a = np.array(a)
    b = np.array(b)
 
    dot_product = np.dot(a, b)        # 내적
    norm_a = np.linalg.norm(a)        # a의 크기(벡터 길이)
    norm_b = np.linalg.norm(b)        # b의 크기
 
    return float(dot_product / (norm_a * norm_b))
 
assert abs(cosine_similarity_impl([1, 0], [1, 0]) - 1.0) < 1e-9    # 자기 자신 → 1
assert abs(cosine_similarity_impl([1, 0], [0, 1])) < 1e-9          # 직교 벡터 → 0
print(cosine_similarity_impl([1, 1], [1, 1]))
```
</div>

!!! info "부동소수점 오차"
    `cosine_similarity_impl([1,1],[1,1])` 결과가 정확히 1.0이 아니라  
    `0.9999999999999998` 로 나옴. 수학적으로는 1인데 부동소수점 계산이라 아주 살짝 오차가 남.

## 개인 실습 — 예측한 순위를 실측으로 다시 확인 (다른 주제로)

"AI 관련 수상 소식"이라는 질문 하나로, 관련 문장이 무관 문장 2개보다 정말 위로 오는지 검증.

<div class="til-code" markdown>
```python
base_sentence = "AI 관련 수상 소식을 알려줘"

candidate_sentences = [
    "2024년 튜링상은 강화학습 연구자들이 수상했다.",     # 관련 문장
    "오늘 점심으로 김치찌개를 먹었다.",                # 무관
    "주말에 등산을 다녀왔다.",                       # 무관
]
 
base_vec = embedding.embed_query(base_sentence)
cand_vecs = embedding.embed_documents(candidate_sentences)
sims = cosine_similarity([base_vec], cand_vecs)[0]
 
similarity_rows = [
    {"text": text, "score": float(score)} for text, score in zip(candidate_sentences, sims)
]
for row in sorted(similarity_rows, key=lambda r: r["score"], reverse=True):
    print(f"{row['score']:.3f}  {row['text']}")
```
</div>

!!! success "예측대로 나옴"
    (BGE-M3): 관련 문장 0.516 > 무관(등산) 0.424 > 무관(김치찌개) 0.406.  
    이번엔 예측대로 관련 문장이 확실히 1위로 나옴

## 개인 실습 — 교차언어 검색, 다른 주제로 다시 확인

<div class="til-code" markdown>
```python
english_documents = [
    "The 2024 Turing Award was given to pioneers of reinforcement learning.",
    "Google released Gemma 3, an open-source model that runs on a single GPU.",
    "Kakao published a technical report about its Kanana language model.",
    "Researchers at Oxford found that practical skills matter in AI hiring.",
]
cross_question = "강화학습 연구로 상을 받은 사람이 있어?"     # 한국어 질문
 
vec_d = embedding.embed_documents(english_documents)
vec_q = embedding.embed_query(cross_question)
sims_cross = cosine_similarity([vec_q], vec_d)[0]
 
matched = sorted(
    ({"text": t, "score": s} for t, s in zip(english_documents, sims_cross)),
    key=lambda m: m["score"], reverse=True,
)
cross_lingual_best = matched[0]["text"]
print(cross_lingual_best)
```
</div>

!!! example "결과값"
    `결과값`  
    "The 2024 Turing Award was given to pioneers of reinforcement learning."

## 정리

벡터화 → 코사인 유사도 → Top-K → 모델 비교(OpenAI vs BGE-M3) → RAG 답변까지 이어봄.

!!! abstract "정리"
    임베딩은 문장을 "고정 차원" 벡터로 바꾸는 것. 모델이 정한 차원 수는 입력 길이랑 무관함.  
    Top-K 검색 = 질문 벡터 vs 문서 벡터 유사도 계산 → 점수로 정렬 → 상위 K개.  
    유의어라고 항상 점수가 높게 나오는 게 아님 — OpenAI 실험에서 무관 쌍이 더 높게 나온 사례 있었음.  
    색인 문서와 검색 질문은 반드시 같은 임베딩 모델로 만들어야 하고, 모델을 바꾸면 전체 재색인해야함.