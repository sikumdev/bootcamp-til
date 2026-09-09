---
title: 검색 품질 - TF-IDF 기초 개념
date: 2026-09-09
tags: [rag]
---

# 검색 품질  — TF-IDF 기초 개념

> 원본 노트북: [`6__검색_품질_1_TF-IDF_계산.ipynb`](6__검색_품질_1_TF-IDF_계산.ipynb), [`6__검색_품질_1_하이브리드.ipynb`](6__검색_품질_1_하이브리드.ipynb)

## 기본 세팅 — 문서와 질문

문서 6개는 공백으로만 토큰화함. 조사·어미·문장부호를 안 떼서 "연차"와 "연차를"은 다른 토큰으로 잡힘.

<div class="til-code" markdown>
```python
documents = [
    "연차를 신청하려면 인사 포털에서 승인 요청을 등록합니다.",
    "반차를 사용하려면 팀장 승인이 필요합니다.",
    "연차 잔여일은 급여 시스템에서 확인합니다.",
    "출장을 신청하려면 경비 포털에 등록합니다.",
    "회의실 예약은 협업 도구에서 진행합니다.",
    "보안 교육은 분기마다 이수합니다.",
]
query = "연차를 신청하려면 어떻게 해야 하나요?"

tokenized_documents = [document.split() for document in documents]
query_tokens = query.split()
```
</div>

## TF — 문서 안에서 단어가 몇 번 나왔나

TF(Term Frequency)는 그냥 등장 횟수 세는 거임. 질문 단어 기준으로 문서마다 세어봄.

<div class="til-code" markdown>
```python hl_lines="9"
query_terms = list(dict.fromkeys(query_tokens))
query_tf = {term: query_tokens.count(term) for term in query_terms}

document_tf_rows = [
    {term: tokens.count(term) for term in query_terms}
    for tokens in tokenized_documents
]

print("문서1 TF:", document_tf_rows[0])
```
<div class="til-note" data-til-line="9" hidden>문서1 TF: {'연차를': 1, '신청하려면': 1, '어떻게': 0, '해야': 0, '하나요?': 0}</div>
</div>

!!! info "TF만 쓰면 안 되는 이유"
    TF만으로 점수를 매기면 "합니다", "에서" 같은 흔한 말도 많이 나왔다고 점수가 높아짐.  
    그래서 "이 단어가 원래 드문 단어인가"를 따로 재는 IDF가 필요함.

!!! note "이 TF는 미리보기용, 최종 벡터 아님"
    여기서는 "문서가 질문 단어를 포함하는지"만 빠르게 보려고 질문 단어 기준으로만 셈.  
    실제 코사인 유사도 계산에 쓰는 문서 벡터는 뒤에서 전체 어휘(29개) 기준으로 다시 만듦 — 이유는 아래 "문서 벡터는 왜 전체 어휘 기준으로 만들어야 하나"에서 확인.

## DF·IDF — 드문 단어일수록 가중치를 크게

**DF(Document Frequency)** 부터: "이 단어가 전체 문서 중 몇 개에 나오는가"임.  
한 문서 안에서 여러 번 나와도 DF에는 1만 더함 — 문서 하나에 5번 나오든 1번 나오든  
"그 단어가 있는 문서"로는 똑같이 셈. (문서 안에서 몇 번 나왔는지 세는 TF랑 세는 단위 자체가 다름 — TF는 "등장 횟수", DF는 "문서 개수".)

**IDF(Inverse Document Frequency)** 는 이 DF의 역수 개념 — `log(전체 문서 수 / DF)`임.  
DF가 작을수록(드문 단어일수록) IDF가 커짐. 

<div class="til-code" markdown>
```python hl_lines="11"
document_count = len(documents)
document_frequency = {
    term: sum(term in tokens for tokens in tokenized_documents)
    for term in vocabulary
}
idf = {
    term: math.log(document_count / document_frequency[term])
    for term in vocabulary
}

print("연차를 DF:", document_frequency["연차를"], "IDF:", round(idf["연차를"], 4))
print("신청하려면 DF:", document_frequency["신청하려면"], "IDF:", round(idf["신청하려면"], 4))
```
<div class="til-note" data-til-line="11" hidden>연차를 DF: 1 IDF: 1.7918   <- 문서 6개 중 1개에만 있음, 드문 단어라 IDF가 큼<br>신청하려면 DF: 2 IDF: 1.0986   <- 2개 문서에 있음, 상대적으로 흔해서 IDF가 작음</div>
</div>

## 공통 어휘(vocabulary) — 좌표 순서를 문서로만 고정

벡터로 비교하려면 "같은 단어는 항상 같은 자리(인덱스)"에 들어가야 함.  
그래서 문서 6개에 나온 단어만 모아서 정렬한 고정 좌표계를 하나 만듦 — **질문 단어는 여기 안 들어감.**

<div class="til-code" markdown>
```python hl_lines="2 6"
vocabulary = sorted({term for tokens in tokenized_documents for term in tokens})
print("어휘 개수:", len(vocabulary))

surviving = [term for term in query_tokens if term in vocabulary]
dropped = [term for term in query_tokens if term not in vocabulary]
print("어휘에 남은 질문 단어:", surviving)
print("DF=0이라 제외된 질문 단어:", dropped)
```
<div class="til-note" data-til-line="2" hidden>어휘 개수: 29</div>
<div class="til-note" data-til-line="6" hidden>어휘에 남은 질문 단어: ['연차를', '신청하려면']<br>DF=0이라 제외된 질문 단어: ['어떻게', '해야', '하나요?']</div>
</div>

!!! warning "질문 단어인데 벡터에서 통째로 빠짐"
    "어떻게", "해야", "하나요?"는 문서 어디에도 안 나와서(DF=0) IDF 자체를 못 구함.  
    그래서 이 질문은 실질적으로 "연차를 + 신청하려면" 두 단어만으로 문서와 비교되는 거임.  


## TF-IDF 벡터 · 코사인 유사도 — 최종 순위

벡터 좌표값은 `TF × IDF`임. 코사인 유사도는 내적을 두 벡터 크기로 나눈 값 — 같은 단어(같은 자리)에  
질문·문서가 동시에 큰 값을 가질수록 내적이 커지고, 벡터 크기로 나눠서 "방향"만 비교함.

<div class="til-code" markdown>
```python hl_lines="18"
def tfidf_vector(tokens, terms, idf_values):
    return [tokens.count(term) * idf_values[term] for term in terms]

def cosine_similarity(left, right):
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(v * v for v in left))
    right_norm = math.sqrt(sum(v * v for v in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)

query_vector = tfidf_vector(query_tokens, vocabulary, idf)
document_vectors = [tfidf_vector(tokens, vocabulary, idf) for tokens in tokenized_documents]

scores = [cosine_similarity(query_vector, v) for v in document_vectors]
ranking = sorted(range(len(documents)), key=lambda i: (-scores[i], i))
for rank, i in enumerate(ranking, start=1):
    print(f"{rank}위 문서{i+1} {scores[i]:.4f}")
```
<div class="til-note" data-til-line="18" hidden>1위 문서1 0.4891   <- "연차를","신청하려면" 둘 다 겹침<br>2위 문서4 0.1655   <- "신청하려면"만 겹침(출장 안내인데도 점수 받음)<br>3위 문서2 0.0000<br>4위 문서3 0.0000   <- "연차 안내"인데 "연차"≠"연차를"라 0점<br>5위 문서5 0.0000<br>6위 문서6 0.0000</div>
</div>

!!! note "코사인 유사도 = 정답일 확률이 아님"
    이 점수는 단어 일치만으로 계산한 벡터 유사도임. 문서3은 내용상 정답인데도  
    토큰이 안 겹쳐서 0점 — "점수 높다 = 답이 맞다"가 아니라는 걸 여기서 확인함.

## 문서 벡터는 왜 "전체 어휘" 기준으로 만들어야 하나

TF를 셀 때 질문은 질문 단어만 세도 되는데, 문서는 왜 전체 어휘(29개) 기준으로 세야 하는지 직접 비교해봄.

<div class="til-code" markdown>
```python hl_lines="5 8"
query_terms_only = [term for term in dict.fromkeys(query_tokens) if term in vocabulary]

doc1_partial_vector = [tokenized_documents[0].count(t) * idf[t] for t in query_terms_only]
query_partial_vector = [query_tokens.count(t) * idf[t] for t in query_terms_only]
print("질문 단어만 기준 코사인:", round(cosine_similarity(query_partial_vector, doc1_partial_vector), 4))

doc1_full_vector = document_vectors[0]
print("전체 어휘 기준 코사인:", round(cosine_similarity(query_vector, doc1_full_vector), 4))
```
<div class="til-note" data-til-line="5" hidden>질문 단어만 기준 코사인: 1.0   <- 문서1에 딴 단어가 더 있는데도 "완벽 일치"로 나옴 (틀린 결과)</div>
<div class="til-note" data-til-line="8" hidden>전체 어휘 기준 코사인: 0.4891   <- 실제 최종 계산값. 문서1의 나머지 단어들까지 반영됨</div>
</div>

!!! danger "★ 질문 벡터는 질문 단어만 세도 되지만, 문서 벡터는 안 됨"
    문서1 벡터를 "질문 단어(연차를, 신청하려면)만" 기준으로 만들면 코사인이 1.0(완벽 일치)로  
    나오는데, 실제로는 문서1에 `인사`, `포털에서`, `승인` 같은 다른 단어도 더 있어서 이건 틀린 결과임.  
    전체 어휘(29개) 기준으로 만들면 0.4891로 나오는 게 맞는 값임.

    이유는 코사인 유사도 = 내적 ÷ (벡터 크기 곱) 이라서 그럼.
    - **분자(내적)**: 질문에 없는 단어는 질문 쪽 값이 0이라 곱해도 0 → 어차피 기여 안 함
    - **분모(벡터 크기)**: 문서 벡터 크기는 "그 문서에 있는 모든 단어"를 반영함 → 질문에 없는 단어라도 문서 벡터를 키워서 분모가 커짐 → 코사인 유사도는 오히려 작아짐

    그래서 **문서 벡터는 "그 문서가 원래 얼마나 많은 내용을 담고 있는지"를 분모에 반영해야 해서 전체 어휘로 만들어야 하고,**  
    **질문 벡터는 질문에 없는 단어는 어차피 값이 0이라 질문 단어만 세도 결과가 똑같음** — 그래서 앞부분(TF 섹션)에서  
    질문 단어만 세도 괜찮았던 거임. 문서 쪽은 사정이 다름.

## 단어를 5번 반복하면 유사도도 5배일까

<div class="til-code" markdown>
```python hl_lines="9"
single_vector = tfidf_vector("연차를".split(), vocabulary, idf)
repeated_vector = tfidf_vector("연차를 연차를 연차를 연차를 연차를".split(), vocabulary, idf)
term_index = vocabulary.index("연차를")

for label, vector in [("1번 등장", single_vector), ("5번 등장", repeated_vector)]:
    weight = vector[term_index]
    norm = math.sqrt(sum(v * v for v in vector))
    cos = cosine_similarity(query_vector, vector)
    print(label, "| raw TF-IDF=", round(weight, 4), "| 벡터 크기=", round(norm, 4), "| 코사인=", round(cos, 4))
```
<div class="til-note" data-til-line="9" hidden>1번 등장 | raw TF-IDF= 1.7918 | 벡터 크기= 1.7918 | 코사인= 0.8525<br>5번 등장 | raw TF-IDF= 8.9588 | 벡터 크기= 8.9588 | 코사인= 0.8525   <- raw는 정확히 5배인데 코사인은 그대로임</div>
</div>

!!! danger "반복 = 점수 배수, 이 명제는 틀림"
    raw TF-IDF는 5배가 맞는데(1.7918→8.9588), 벡터 크기도 같이 5배가 돼서 나눗셈하면 코사인은 그대로임.  
    여기선 단어 종류가 하나뿐이라 방향이 안 바뀌어서 그런 거고, 여러 단어가 섞인 문서에서 한 단어만 반복하면 
    방향이 바뀌어서 유사도도 달라질 수 있음.

!!! info "TF-IDF가 임베딩이랑 비슷한 효과인 이유"
    알고리즘이 같다는 게 아니라 "텍스트를 벡터로 바꿔서 코사인 유사도로 비교한다"는 틀이 같다는 뜻임.  
    TF-IDF는 좌표 하나하나가 "그 단어 자체"라서 "연차"≠"연차를"이면 완전 무관 취급됨(글자만 봄).  
    진짜 Dense 임베딩은 좌표가 신경망이 학습한 의미 축이라 "연차"랑 "휴가"도 가깝게 배치됨(뜻을 봄).  
    이 벡터 연산은 `sklearn.feature_extraction.text.TfidfVectorizer`로 대체 가능.

## BM25 — TF-IDF에 포화·길이 보정을 더한 랭킹 함수

TF가 커질수록 점수 증가폭이 줄어들게(포화) 만들고, 문서 길이로 점수를 보정함.  
Elasticsearch·Lucene 기본 랭킹이라 실무에서 계속 마주침.

<div class="til-code" markdown>
```python hl_lines="19 24"
def bm25_score(query_terms, doc_tokens, all_docs, k1=1.5, b=0.75):
    document_count = len(all_docs)
    average_length = sum(len(d) for d in all_docs) / document_count
    score = 0.0
    for term in query_terms:
        document_frequency = sum(term in d for d in all_docs)
        idf = math.log(
            (document_count - document_frequency + 0.5)
            / (document_frequency + 0.5)
        )
        term_frequency = doc_tokens.count(term)
        length_norm = 1 - b + b * len(doc_tokens) / average_length
        score += idf * (term_frequency * (k1 + 1)) / (term_frequency + k1 * length_norm)
    return score

manual_scores = [bm25_score(query_tokens, doc, tokenized_documents) for doc in tokenized_documents]
ranking = sorted(range(len(documents)), key=lambda i: manual_scores[i], reverse=True)
for rank, i in enumerate(ranking, start=1):
    print(f"{rank}위 {manual_scores[i]:.4f} {documents[i]}")

engine = BM25Okapi(tokenized_documents, k1=1.5, b=0.75)
library_scores = engine.get_scores(query_tokens)
max_diff = max(abs(a - b) for a, b in zip(manual_scores, library_scores))
print("수동 계산 vs 라이브러리 최대 오차:", f"{max_diff:.1e}")
```
<div class="til-note" data-til-line="19" hidden>1위 1.6272 연차를 신청하려면 인사 포털에서 승인 요청을 등록합니다.<br>2위 0.5964 출장을 신청하려면 경비 포털에 등록합니다.<br>3~6위 0.0000</div>
<div class="til-note" data-til-line="24" hidden>수동 계산 vs 라이브러리 최대 오차: 0.0e+00   <- 완전 일치 (직접 확인함)</div>
</div>

!!! warning " IDF 공식이 라이브러리마다 다르게 쓰임"
    처음엔 "IDF는 다 `log(N/DF)` 하나"인 줄 알았는데 아니었음. 같은 단어 "연차를"(N=6, DF=1)인데  
    방식별로 값이 다 다름 — TF-IDF 방식 `log(N/DF)`=1.7918, BM25 Robertson 방식  
    `log((N-DF+0.5)/(DF+0.5))`=1.2993, sklearn류 smooth 방식 `log((N+1)/(DF+1))+1`=2.2528.  
    라이브러리 바꿔쓸 때 IDF 정의부터 확인해야 함.

!!! note "Robertson IDF는 DF=0에서도 양수값을 줌"
    "어떻게"(DF=0)의 Robertson IDF=2.5649로 양수임 — TF-IDF 벡터 방식이 DF=0이면  
    아예 제외하는 것과 다름. 실제 BM25 최종 점수엔 영향 없음(TF도 0이라 기여도가 0으로 곱해짐).




