"""
title: 문서 표현 — BoW · DTM/TDM · TF-IDF
tags: [nlp]
"""

#== 단어 표현에서 문서 표현으로
#> 앞 노트는 `단어 하나`를 벡터로 바꿨음. 이번은 `문서 하나`를 벡터로 바꿈.

#! 예전에 정리한 원-핫은 단어 하나에 벡터 하나였음. 문서는 단어가 여러 개라 그대로는 못 씀.
#! BoW 의 아이디어는 `문서 안의 원-핫 벡터를 전부 더하는` 것임.
#! `오늘 동물원에서 봤어 봤어` → 오늘 1, 동물원에서 1, 봤어 2. 이게 그대로 BoW 벡터.
#! 그래서 원-핫과 BoW 의 차이는 `값이 0/1 이냐, 0 이상의 횟수냐` 뿐임.
#! 길이는 둘 다 어휘 크기로 똑같음.


#== 1. Counter 순회 순서 — most_common 과 다름

# --8<-- [start:counter_order]
from collections import Counter

docs = ['오늘 동물원에서 원숭이를 봤어',
        '오늘 동물원에서 코끼리를 봤어 봤어',
        '동물원에서 원숭이에게 바나나를 줬어 바나나를']

doc_ls = [doc.split() for doc in docs]

all_tokens = []

# extend 는 리스트를 풀어서 붙임. append 를 쓰면 리스트가 통째로 원소가 됨
for doc in doc_ls:
    all_tokens.extend(doc)

word_counts = Counter(all_tokens)

# 빈도순이 아니라 `처음 등장한 순서` 임
list(word_counts)
# ['오늘', '동물원에서', '원숭이를', '봤어', '코끼리를', '원숭이에게', '바나나를', '줬어']

# 이쪽이 빈도순
word_counts.most_common()
# [('동물원에서', 3), ('봤어', 3), ('오늘', 2), ('바나나를', 2), ('원숭이를', 1), ...]
# --8<-- [end:counter_order]

#! 여기서 헷갈렸던 것 → `Counter 를 그냥 순회하면 빈도순으로 나올 줄 알았는데 아니었음`.
#! Counter 는 dict 를 상속받은 거라 순회 순서는 `삽입 순서` = 첫 등장 순서임.
#! 빈도순이 필요하면 `most_common()` 을 따로 불러야 함. 직접 돌려서 확인함.
#! Counter 를 쓰면 중복 제거와 빈도 세기를 한 번에 하는 셈.(`list(dict.fromkeys(x))` 와 결과가 같음.)


#== word2id 만드는 두 가지 방법

# --8<-- [start:word2id]
word2id = {}

# enumerate 가 주는 번호를 그대로 씀
for i, word in enumerate(word_counts):
    word2id[word] = i

word2id_alt = {}

# 지금까지 담긴 개수를 번호로 씀. 0개면 0번, 1개면 1번
for word in word_counts:
    word2id_alt[word] = len(word2id_alt)

word2id == word2id_alt   # True
# --8<-- [end:word2id]

#! `len(word2id)` 방식은 `이미 넣은 개수가 곧 다음 번호` 라는 성질을 쓰는 것.
#! 단, 이 방식은 같은 단어가 두 번 들어오면 번호를 덮어쓰면서 중간이 비어버림.
#! Counter 를 거쳐서 이미 중복이 없으니까 안전한 것. 원본 리스트를 그대로 돌리면 안 됨.


#== 2. BoW 만들기

# --8<-- [start:bow]
import numpy as np

BoW_ls = []
for doc in doc_ls:
    # 어휘 크기만큼 0으로 채운 벡터를 문서마다 새로 만듦
    bow = np.zeros(len(word2id), dtype=int)
    for token in doc:
        # 토큰의 번호 자리에 1씩 더함. 두 번 나오면 2가 됨
        bow[word2id[token]] += 1
    BoW_ls.append(bow.tolist())

BoW_ls
# [[1, 1, 1, 1, 0, 0, 0, 0],
#  [1, 1, 0, 2, 1, 0, 0, 0],
#  [0, 1, 0, 0, 0, 1, 2, 1]]
# --8<-- [end:bow]

#== BoW 는 단어 순서를 못 담음

# --8<-- [start:bow_order]
# 양념과 후라이드의 위치만 바뀜. 뜻은 정반대
chicken_docs = ['나는 양념 치킨을 좋아해 하지만 후라이드 치킨을 싫어해',
                '나는 후라이드 치킨을 좋아해 하지만 양념 치킨을 싫어해']

chicken_ls = [d.split() for d in chicken_docs]
chicken_counts = Counter([t for d in chicken_ls for t in d])
chicken_id = {w: i for i, w in enumerate(chicken_counts)}

chicken_bow = []
for doc in chicken_ls:
    b = np.zeros(len(chicken_id), dtype=int)
    for t in doc:
        b[chicken_id[t]] += 1
    chicken_bow.append(b.tolist())

chicken_bow[0]                        # [1, 1, 2, 1, 1, 1, 1]
chicken_bow[1]                        # [1, 1, 2, 1, 1, 1, 1]
chicken_bow[0] == chicken_bow[1]      # True
chicken_docs[0] == chicken_docs[1]    # False
# --8<-- [end:bow_order]

#! 원문은 다른데 BoW 는 완전히 같음. 
#! `양념을 좋아하고 후라이드를 싫어함` 과 그 반대가 구별이 안 됨.


#== 3. DTM 과 TDM — 같은 표를 눕히느냐 세우느냐

# --8<-- [start:dtm_tdm]
DTM = np.zeros((len(doc_ls), len(word2id)), dtype=int)
for i, doc in enumerate(doc_ls):
    for token in doc:
        # [문서번호, 단어번호] — 행이 문서
        DTM[i, word2id[token]] += 1

TDM = np.zeros((len(word2id), len(doc_ls)), dtype=int)
for i, doc in enumerate(doc_ls):
    for token in doc:
        # [단어번호, 문서번호] — 행이 단어
        TDM[word2id[token], i] += 1

DTM.shape                      # (3, 8)   문서 3개 × 단어 8개
TDM.shape                      # (8, 3)   단어 8개 × 문서 3개
np.array_equal(TDM, DTM.T)     # True
# --8<-- [end:dtm_tdm]

#! DTM 과 TDM 은 서로 전치 관계일 뿐 담긴 정보가 똑같음. 
#! `D`ocument-`T`erm 이면 문서가 먼저, `T`erm-`D`ocument 면 단어가 먼저.
#! 이름 순서가 곧 `(행, 열)` 순서임. 

#== 원본에서 틀렸던 것 — np.zeros 에 shape 을 튜플로 안 줌

# --8<-- [start:bug_zeros_shape]
v_dict = {'빨강': 0, '파랑': 1, '초록': 2}

try:
    np.zeros(len(v_dict), 2, dtype=int)
#(1)> 2 가 dtype 자리로 들어감. dtype 을 위치로도 이름으로도 준 셈이 됨
except TypeError as error:
    print(error)   # argument for zeros() given by name ('dtype') and position (position 1)

# 괄호를 한 겹 더 씌워서 shape 을 튜플로 넘겨야 함
np.zeros((len(v_dict), 2), dtype=int)
# --8<-- [end:bug_zeros_shape]

#! `np.zeros(shape, dtype, order)` 순서라서 두 번째 위치 인자는 항상 dtype 임.

#== 표로 보기 — word2id 를 열 이름으로 되돌리기
#> 숫자만 보면 어느 열이 무슨 단어인지 알 수 없어서 항상 같이 봐야 함.

# --8<-- [start:to_dataframe]
import pandas as pd

# {'오늘': 0, ...} 를 (0, '오늘') 튜플로 뒤집어서 번호순 정렬
sorted_vocab = sorted((value, key) for key, value in word2id.items())

#['오늘', '동물원에서', '원숭이를', '봤어', '코끼리를', '원숭이에게', '바나나를', '줬어']
vocab = [v[1] for v in sorted_vocab]

# 행이 문서, 열이 단어. DTM 을 그대로 표로 본 것
pd.DataFrame(BoW_ls, columns=vocab)

doc_names = ['문서' + str(i) for i in range(len(doc_ls))]
# 전치해서 넣으면 TDM 표가 됨. 행이 단어, 열이 문서
pd.DataFrame(np.array(BoW_ls).T, columns=doc_names, index=vocab)
# --8<-- [end:to_dataframe]

#! 왜 정렬하냐 → dict 는 `단어 → 번호` 인데 표의 열 이름은 `번호 순서의 단어 목록` 이 필요해서.
#! `(key, value)` 를 `(value, key)` 로 뒤집어야 번호 기준으로 정렬됨.
#! 파이썬은 튜플을 정렬할 때 앞 원소부터 비교하니까 앞자리에 번호를 둬야 함.


#== 4. TF — 문서 길이로 나누기

# --8<-- [start:tf]
def computeTF(DTM):
    # 그 단어 횟수 / 그 문서의 전체 토큰 수(하나의 문서에서의 전체 합)
    doc_len, word_len = DTM.shape
    tf = np.zeros((doc_len, word_len))
    for doc_i in range(doc_len):
        for word_i in range(word_len):
            tf[doc_i, word_i] = DTM[doc_i, word_i] / DTM[doc_i].sum()
            

    return tf

tf = computeTF(DTM)
# [[0.25 0.25 0.25 0.25 0.   0.   0.   0.  ]
#  [0.2  0.2  0.   0.4  0.2  0.   0.   0.  ]
#  [0.   0.2  0.   0.   0.   0.2  0.4  0.2 ]]
# --8<-- [end:tf]

#! `DTM[doc_i].sum()` 은 그 행의 합. 문서0 은 토큰 4개라 전부 `1/4 = 0.25`.
#! 문서1 은 토큰 5개라 `봤어` 만 `2/5 = 0.4`.
#! 왜 나누냐 → 문서 길이를 맞추려고.
#! 긴 문서는 모든 단어의 횟수가 통째로 커짐. 그대로 비교하면 `길다`는 이유로 이겨버림.



#== 5. IDF — 여러 문서에 퍼진 단어를 깎기

# --8<-- [start:idf]
import math

def computeIDF(DTM):
    doc_len, word_len = DTM.shape
    idf = np.zeros(word_len)
    for i in range(word_len):
        idf[i] = -math.log10(np.count_nonzero(DTM[:, i]) / doc_len)
        #(1)> np.count_nonzero(DTM[:, i]) = i번 단어가 등장한 `문서 수`(df)
        #(1)> -log10(df / N) 은 log10(N / df) 와 같음. 앞의 마이너스로 뒤집는 것

    return idf

idf = computeIDF(DTM)
# [ 0.176091 -0.  0.477121  0.176091  0.477121  0.477121  0.477121  0.477121]
# --8<-- [end:idf]

#! `DTM[:, i]` 는 i번 `열` 전부. 콤마 앞이 행, 뒤가 열이고 `:` 는 전부라는 뜻.
#! 중요한 건 `count_nonzero` 라서 `몇 번 나왔는지가 아니라 몇 개 문서에 나왔는지` 를 셈.
#! `동물원에서` df=3 → log10(3/3) = 0 → 완전히 깎임
#! `오늘` df=2 → log10(3/2) = 0.176
#! `원숭이를` df=1 → log10(3/1) = 0.477 ← 한 문서에만 있어서 가장 높음


#== 6. TF-IDF — 곱하기

# --8<-- [start:tfidf]
def computeTFIDF(DTM):
    tf = computeTF(DTM)
    idf = computeIDF(DTM)
    tfidf = np.zeros(tf.shape)
    for doc_i in range(tf.shape[0]):
        for word_i in range(tf.shape[1]):
            tfidf[doc_i, word_i] = tf[doc_i, word_i] * idf[word_i]

    return tfidf

tfidf = computeTFIDF(DTM)
tfidf.shape                              # (3, 8)   DTM 과 같은 모양
np.allclose(tf * idf, tfidf)             # True
# --8<-- [end:tfidf]

#! TF-IDF 값의 뜻
#! 높다 = 이 문서에는 자주 나오는데 다른 문서에는 안 나옴 → 이 문서의 특징어
#! 0    = 이 문서에 아예 없거나(TF=0), 모든 문서에 있어서 흔함(IDF=0)



#== 7. sklearn — CountVectorizer

# --8<-- [start:sklearn_count]
from sklearn.feature_extraction.text import CountVectorizer

count_vect = CountVectorizer()

# fit(어휘 학습) + transform(벡터 변환) 을 한 번에
BoW = count_vect.fit_transform(docs)

# 가나다순으로 정렬됨. 직접 만든 word2id 의 첫 등장 순서와 다름
count_vect.get_feature_names_out()
# ['동물원에서' '바나나를' '봤어' '오늘' '원숭이를' '원숭이에게' '줬어' '코끼리를']

BoW.toarray()
# fit_transform 은 sparse matrix 를 돌려줌. 배열로 보려면 toarray()
# [[1 0 1 1 1 0 0 0]
#  [1 0 2 1 0 0 0 1]
#  [1 2 0 0 0 1 1 0]]
# --8<-- [end:sklearn_count]

#! 값이 직접 구현과 달라 보이는 건 `열 순서만` 다르기 때문임.

# --8<-- [start:sklearn_token_trap]
# \w 가 두 번. `2글자 이상`만 토큰으로 인정한다는 뜻
count_vect.token_pattern      # '(?u)\\b\\w\\w+\\b'

# 1글자인 나·는·밥·을·먹 이 전부 사라짐 -> ['는다' '오늘']
CountVectorizer().fit(["나 는 밥 을 먹 는다 오늘"]).get_feature_names_out()

# \w 를 하나로 줄이면 1글자도 살아남음 -> ['나' '는' '는다' '먹' '밥' '오늘' '을']
CountVectorizer(token_pattern=r"(?u)\b\w+\b").fit(
    ["나 는 밥 을 먹 는다 오늘"]).get_feature_names_out()
# --8<-- [end:sklearn_token_trap]


#! CountVectorizer 는 기본으로 `1글자 토큰을 통째로 버림`.
#! 영어는 a·I 정도라 손해가 적은데, 한국어는 `나·는·밥·꽃·물` 이 전부 날아감.
#! 예전 노트에서 Kiwi 로 형태소 분석하면 `읽`·`쓰` 같은 1글자 어근이 나왔음.
#! 그걸 CountVectorizer 에 그대로 넣으면 전부 사라짐. 두 도구를 이어 쓸 때 반드시 봐야 함.
#! 해결은 `token_pattern` 을 바꾸거나 `tokenizer=` 로 함수를 직접 넘기는 것.


#== 8. sklearn — TfidfVectorizer 는 공식이 다름

# --8<-- [start:sklearn_tfidf]
from sklearn.feature_extraction.text import TfidfVectorizer, TfidfTransformer

tfidf_vect = TfidfVectorizer()
sk_tfidf = tfidf_vect.fit_transform(docs)

np.linalg.norm(sk_tfidf.toarray(), axis=1)   # [1. 1. 1.]


tfidf_vect.smooth_idf    # True
tfidf_vect.norm          # 'l2'

# CountVectorizer + TfidfTransformer 조합도 결과가 같음
tfidf_trans = TfidfTransformer()
np.allclose(tfidf_trans.fit_transform(BoW).toarray(), sk_tfidf.toarray())   # True
#(2)> TfidfVectorizer = CountVectorizer + TfidfTransformer 를 붙인 것
# --8<-- [end:sklearn_tfidf]

#! sklearn 값이 직접 구현과 아예 다른 이유가 세 개임.
#! 1. 로그 밑이 다름 — sklearn 은 자연로그(ln), 직접 구현은 log10
#! 2. smoothing — sklearn 은 `ln((1+N)/(1+df)) + 1`
#! 3. L2 정규화 — 행마다 길이를 1로 맞춤. 직접 구현에는 이 단계가 없음

# --8<-- [start:sklearn_idf_formula]
import math

# 열마다 0보다 큰 값의 개수 = 등장한 문서 수
df = (BoW.toarray() > 0).sum(axis=0)   # [3 1 2 2 1 1 1 1]

n = len(docs)
[round(math.log((1 + n) / (1 + d)) + 1, 6) for d in df]
# [1.0, 1.693147, 1.287682, 1.287682, 1.693147, 1.693147, 1.693147, 1.693147]

# 수식으로 손계산한 값과 sklearn 의 idf_ 가 정확히 일치
# [1.       1.693147 1.287682 1.287682 1.693147 1.693147 1.693147 1.693147]
tfidf_trans.idf_
# --8<-- [end:sklearn_idf_formula]


#== 비교 정리

# --8<-- [start:compare]
  구분          직접 구현                    sklearn
  어휘 순서      첫 등장순 (Counter 순회)     가나다·알파벳 정렬
  1글자 토큰     그대로 살림                  기본으로 버림 (\w\w+)
  반환 타입      numpy 배열                  sparse matrix (.toarray() 필요)
  IDF 로그      log10                        자연로그 ln
  IDF 공식      log10(N/df)                  ln((1+N)/(1+df)) + 1
  df=N 일 때    0 이 되어 단어가 죽음           1.0 으로 살아남음
  정규화         없음                         행마다 L2 (길이 1)
  BoW           DTM 을 직접 채움             CountVectorizer
  TF-IDF        computeTFIDF                 TfidfVectorizer
# --8<-- [end:compare]

#! 직접 구현을 먼저 해보는 이유 → sklearn 값이 왜 다른지 알려면 공식을 알아야 해서.
#! 실무에서는 sklearn 을 쓰되 `기본값이 뭘 하는지` 는 알고 써야 함.
#! 특히 한국어에서는 1글자 토큰 버리는 게 치명적임.


#== 정리

#! 흐름  문서 → split → Counter → word2id → DTM → TF · IDF → TF-IDF
#! BoW  문서 안 원-핫을 전부 더한 것. 길이는 어휘 크기
#! BoW 는 단어 순서를 못 담음. 양념/후라이드를 바꿔도 벡터가 같음
#! DTM vs TDM  이름 순서가 곧 (행, 열) 순서. 서로 전치 관계라 정보는 동일
#! Counter 순회  빈도순이 아니라 첫 등장순. 빈도순은 most_common()
#! TF  그 단어 횟수 / 그 문서 전체 토큰 수. 문서 길이를 맞추는 것
#! IDF  count_nonzero 로 `등장한 문서 수(df)` 를 셈. 횟수가 아님
#! df = 전체 문서 수면 idf 가 0. 흔한 단어를 수식이 알아서 죽임
#! TF-IDF  `tf * idf` 한 줄이면 됨. 브로드캐스팅이 알아서 맞춰줌
#! CountVectorizer 는 1글자 토큰을 기본으로 버림. 한국어에서 치명적
#! sklearn TF-IDF  자연로그 + smoothing + L2 정규화라 직접 계산과 값이 다름
