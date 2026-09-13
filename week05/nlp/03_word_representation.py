"""
title: 단어 표현 — 토큰화 · 어휘 인덱스 · 원-핫 · UNK
tags: [nlp]
"""

#== 단어를 숫자로 바꾸는 흐름
#> 텍스트 → 토큰 → 어휘 인덱스 → 벡터. 앞 단계가 틀리면 뒤가 전부 어긋남.

#! 이전 전처리 노트(Kiwi·NLTK)의 주제는 `어떤 단어를 남길지` 였음.
#! 이번 주제는 남긴 단어를 `어떻게 숫자로 바꿀지` 임.

#! 모델은 문자열을 못 받음. `사과` 라는 글자를 넣을 수가 없어서
#! 어휘표에서 번호를 매기고, 그 번호를 벡터로 펴는 것. 이 노트는 그 과정임.


#== np.set_printoptions — 값이 아니라 화면 표시만 바꿈

# --8<-- [start:printopts]
import numpy as np

# precision=3 은 소수 셋째 자리까지, suppress=True 는 1.23e-06 같은 과학적 표기법을 끔
np.set_printoptions(precision=3, suppress=True)

display_values = np.array([1.234567, 0.00000123])
print(display_values)              # [1.235 0.   ]
print(float(display_values[0]))    # 1.234567
print(float(display_values[1]))    # 1.23e-06
# --8<-- [end:printopts]

#! 두 번째 값이 `0.` 으로 보이지만 실제 값은 `1.23e-06` 임. 
#! `numpy 가 배열을 출력할 때만` 반올림하는 것이고 배열 안의 값은 그대로임.
#! 그래서 값이 이상할 땐 `float()` 로 원소를 꺼내서 봐야 함.


#== 1. 토큰화 — 정규식 한 줄로 끝내기
#> 문장을 단어 리스트로 자르는 단계. 여기 결과가 어휘의 재료가 됨.

# --8<-- [start:tokenize]
import re

# 소문자로 바꾼 뒤 한글·영문·숫자가 붙어 있는 덩어리만 골라냄
def tokenize(text):
    return re.findall(r"[가-힣A-Za-z0-9]+", text.lower())

tokenize("사과, 바나나! 사과?")       # ['사과', '바나나', '사과']
tokenize("원숭이-코끼리_바나나")      # ['원숭이', '코끼리', '바나나']
# --8<-- [end:tokenize]

#! `re.findall` 은 `패턴에 맞는 부분만` 뽑아 리스트로 줌. 안 맞는 문자는 알아서 버려짐.
#! 이전 노트에서 `re.sub` 로 기호를 공백으로 바꾸고 다시 공백을 정리했던 것과 방향이 반대임.
#! `re.sub` 는 `버릴 것을 지우는` 방식, `re.findall` 은 `남길 것만 줍는` 방식.


# --8<-- [start:tokenize_fail]
tokenize("NLP Model과 DATA 2026")   # ['nlp', 'model과', 'data', '2026']

tokenize("don't stop")              # ['don', 't', 'stop']
tokenize("3.88달러")                # ['3', '88달러']
tokenize("ㅋㅋㅋ 웃김")             # ['웃김']
# --8<-- [end:tokenize_fail]

#! ★ `가-힣` 은 완성형 음절만 잡음. `ㅋ`·`ㅜ` 같은 자모 낱글자는 범위 밖이라 통째로 사라짐.
#! `ㅋㅋㅋ` 이 흔적도 없이 없어지는 게 실제 채팅 데이터에서는 문제가 될 수 있음.
#! `don't` 가 `don` + `t` 로 깨짐.
#! 정규식 한 줄로는 축약형·소수점을 못 살림. 원리를 볼 땐 충분하지만 실전에서는 전용 토크나이저를 씀.


#== 2. 어휘(vocabulary)와 인덱스
#> `단어 → 정수` 표를 먼저 만들어야 벡터를 만들 수 있음.

# --8<-- [start:vocab]
words = ["원숭이", "바나나", "사과", "사과", "코끼리"]

# ['원숭이', '바나나', '사과', '코끼리'] — 중복을 없애면서 첫 등장 순서를 유지
vocabulary = list(dict.fromkeys(words))

# {'원숭이': 0, '바나나': 1, '사과': 2, '코끼리': 3}
word_to_index = {word: index for index, word in enumerate(vocabulary)}

word_to_index["사과"]    # 2
# --8<-- [end:vocab]

#! `dict.fromkeys(words)` 의 결과는 `{'원숭이': None, '바나나': None, ...}` 임.
#! 키만 쓰고 값은 전부 None. 그래서 `list()` 로 감싸면 키 목록만 남음.
#! dict 는 파이썬 3.7+ 부터 `삽입 순서를 보장`해서 이렇게 중복 제거에 쓸 수 있음.

#== 어휘 순서 — set 을 그대로 쓰면 안 되는 이유

# --8<-- [start:vocab_order]
order_words = ["원숭이", "바나나", "사과", "바나나"]

sorted(set(order_words))            # ['바나나', '사과', '원숭이']  가나다순
list(dict.fromkeys(order_words))    # ['원숭이', '바나나', '사과']  첫 등장순
# --8<-- [end:vocab_order]

#! 직접 확인한 것 → `list(set(...))` 는 실행할 때마다 순서가 달라짐.
#! 그래서 어휘는 `sorted(set(...))` 또는 `list(dict.fromkeys(...))` 중 하나로 순서를 고정해야 함.
#! 순서가 흔들리면 인덱스가 바뀌고, 어제 저장한 벡터와 오늘 만든 벡터가 서로 다른 단어를 가리키게 됨.


#== 인덱스를 0부터 시작하는 이유

# --8<-- [start:index_base]
first_seen = ["원숭이", "바나나", "사과"]

{w: i for i, w in enumerate(first_seen)}            # {'원숭이': 0, '바나나': 1, '사과': 2}
{w: i for i, w in enumerate(first_seen, start=1)}   # {'원숭이': 1, '바나나': 2, '사과': 3}
# --8<-- [end:index_base]

#! 벡터로 쓸 거면 `0부터`. 인덱스가 곧 `배열의 몇 번째 행` 이라서 그대로 맞아떨어짐.
#! 1부터 시작하면 크기 3 어휘에서 인덱스 3 이 나와서 `IndexError` 가 남.


#== 3. 원-핫 벡터 — np.eye 로 한 번에

# --8<-- [start:one_hot]
vocabulary_with_unk = ["<UNK>", "원숭이", "바나나", "사과"]
index_with_unk = {word: index for index, word in enumerate(vocabulary_with_unk)}

identity = np.eye(len(vocabulary_with_unk), dtype=int)
#(1)> 대각선만 1인 단위행렬. i 번째 행이 그대로 i 번 단어의 원-핫 벡터가 됨
#(1)> dtype 을 안 주면 float64 라 `[1. 0. 0.]` 처럼 나옴. int 를 주면 `[1 0 0]`

query_indices = [3, 0, 2]
# 3행·0행·2행을 그 순서대로 뽑아서 쌓음 → shape (3, 4)
query_one_hot = identity[query_indices]
# --8<-- [end:one_hot]

#! `단위행렬을 미리 만들어 두고 필요한 행을 인덱스로 뽑는` 방식임.
#! 어휘 크기가 곧 벡터의 차원임. 어휘가 1만 개면 단어 하나가 1만 차원짜리 벡터가 됨.

# --8<-- [start:one_hot_check]
query_one_hot.shape            # (3, 4)   단어 3개 × 어휘 4개
query_one_hot.sum(axis=1)      # [1 1 1]
#(1)> 각 행에 1이 정확히 하나 → 원-핫이 맞다는 확인
#(1)> 열이 사라진다고 생각하면 [[1],[1],[1]] 이라고 생각 할 수 있지만 여기서 차원수도 줄어들기에 [1 1 1]임
query_one_hot.argmax(axis=1)   # [3 0 2]
#(2)> 1이 있는 위치가 곧 원래 인덱스. 벡터에서 단어를 되찾는 방법

query_one_hot.sum(axis=0)      # [1 0 1 1]
#(3)> axis=0 은 세로로 더한 것. 어휘의 각 단어가 몇 번 쓰였는지가 나옴
#(3)> 행이 사라진다고 하면 [1 0 1 1]
# --8<-- [end:one_hot_check]

#! `axis=1` 은 `가로로 접는다`, `axis=0` 은 `세로로 접는다` 는 뜻.
#! (3, 4) 행렬에서 axis=1 이면 결과 shape 가 `(3,)`, axis=0 이면 `(4,)` 임.

#== NumPy 인덱싱 — 대괄호 안에 콤마가 있느냐

# --8<-- [start:numpy_index]
# 리스트 하나만 넣으면 `행 선택`
identity[[3, 0, 2]]        # shape (3, 4)   3행·0행·2행
# 콤마로 나뉘면 (행, 열) 좌표 하나
identity[3, 0]             # 0              3행 0열의 값 하나
# 리스트 두 개면 좌표 목록임. 행 2개를 뽑는 게 아님
identity[[3, 0], [0, 2]]   # [0 0]          (3,0) 과 (0,2) 두 곳의 값
# --8<-- [end:numpy_index]
#! 리스트 안에 리스트인 경우를 주의 해야 함
#! 콤마가 없으면 `행 목록`, 콤마가 있으면 `좌표`.
#! 원-핫은 행을 통째로 뽑아야 하니까 `identity[[1, 0, 2]]` 처럼 리스트 하나만 넣는 것.


#== 4. UNK — 어휘에 없는 단어 처리

# --8<-- [start:unk]
# dict.get(키, 기본값) 은 키가 없으면 기본값을 돌려줌. 대괄호는 KeyError 를 냄
index_with_unk.get("코끼리", index_with_unk["<UNK>"])   # 0

query_words = ["사과", "코끼리", "바나나"]
query_indices = [
    index_with_unk.get(word, index_with_unk["<UNK>"])
    for word in query_words
]
query_indices   # [3, 0, 2]
# --8<-- [end:unk]

#! `index_with_unk["코끼리"]` 처럼 대괄호로 찾으면 `KeyError: '코끼리'` 가 남.
#! `<UNK>` 를 어휘 0번에 두는 게 관례임. 어휘를 나중에 늘려도 UNK 자리가 안 밀려서 그럼.

# --8<-- [start:unk_collision]
unknown_examples = ["사과", "코끼리", "기린", "바나나"]
# 코끼리와 기린이 둘 다 0번. 다른 단어인데 완전히 같은 벡터가 됨
unknown_indices = [index_with_unk.get(w, 0) for w in unknown_examples]
unknown_indices    # [3, 0, 0, 2]

identity[unknown_indices]
# [[0 0 0 1]   사과
#  [1 0 0 0]   코끼리
#  [1 0 0 0]   기린    ← 코끼리와 구별이 안 됨
#  [0 0 1 0]]  바나나
# --8<-- [end:unk_collision]

#! 이게 원-핫 + UNK 의 가장 큰 한계임.
#! 어휘에 없는 단어는 전부 한 벡터로 뭉개져서 `코끼리 = 기린` 이 되어버림.
#! 어휘를 키우면 UNK 로 빠지는 단어가 줄지만 그만큼 벡터 차원이 커짐. 트레이드오프임.


#== 원-핫끼리 비교하면 전부 남남

# --8<-- [start:one_hot_sim]
one_hot = identity[[3, 0, 0, 2]]
one_hot @ one_hot.T
#(1)> `@` 는 행렬 곱, `.T` 는 전치(행과 열을 바꾼 것)
#(1)> 결과의 i행 j열 = i번 단어 벡터와 j번 단어 벡터의 내적

# [[1 0 0 0]
#  [0 1 1 0]   ← 코끼리·기린이 둘 다 UNK 라 1이 붙음
#  [0 1 1 0]
#  [0 0 0 1]]
# --8<-- [end:one_hot_sim]

#! 대각선은 항상 1. 자기 자신과의 내적이라서 그럼.
#! 대각선 밖이 전부 0 이라는 게 핵심임.
#! `사과`와 `바나나` 가, `사과`와 `원숭이` 만큼이나 똑같이 남남으로 나옴.
#! 원-핫 벡터는 `이 단어가 어휘의 몇 번인지` 만 담고 뜻은 하나도 못 담음.
#! 위 행렬에서 1 이 대각선 밖에 나온 유일한 자리가 UNK 끼리 만난 곳임.
#! 뜻이 비슷해서가 아니라 `둘 다 모르는 단어` 라서 붙은 것. 유사도가 아니라 사고임.
#! → 그래서 임베딩(단어를 조밀한 실수 벡터로)이 필요해지는 것. 다음 주제로 이어짐.


#== 5. 거리와 유사도 — 계산 방향이 서로 반대
#> 여기부터는 요점만. 핵심은 `작을수록 비슷` vs `클수록 비슷` 이 뒤집혀 있다는 것.

# --8<-- [start:distance_vs_similarity]
# 두 벡터를 뺀 다음 그 길이를 잼. 두 점 사이의 직선 거리
def euclidean_distance(left, right):
    return float(np.linalg.norm(left - right))

# 내적을 두 벡터 길이의 곱으로 나눔. 길이가 나눠져서 각도만 남음
def cosine_similarity(left, right):
    denominator = np.linalg.norm(left) * np.linalg.norm(right)
    return float(np.dot(left, right) / denominator)

apple = np.array([0.9, 0.2])
banana = np.array([0.8, 0.3])

euclidean_distance(apple, banana)   # 0.1414...   작을수록 비슷
cosine_similarity(apple, banana)    # 0.9902...   클수록 비슷
# --8<-- [end:distance_vs_similarity]

#! 이름에 `distance` 가 들어가면 작은 게 좋고, `similarity` 가 들어가면 큰 게 좋음.
#! `np.array` 는 항상 새 배열을 복사하고, `np.asarray` 는 이미 배열이면 그대로 씀.

# --8<-- [start:dist_sim_table]
    항목         유클리드 거리              코사인 유사도
-  재는 것      두 점이 떨어진 정도        두 벡터가 이루는 각
-  좋은 값      작을수록 비슷 (최소 0)     클수록 비슷 (최대 1)
-  범위         0 ~ 무한대                 -1 ~ 1
-  벡터 크기    그대로 반영함                  무시함
-  0벡터        그냥 계산됨             분모가 0이라 정의 불가
-  쓰는 곳      좌표·위치 비교             텍스트 벡터 비교
# --8<-- [end:dist_sim_table]

# --8<-- [start:scale_effect]
base = np.array([1.0, 2.0])
scaled = np.array([2.0, 4.0])     # 방향 같고 크기만 두 배
nearby = np.array([2.0, 3.0])     # 방향이 살짝 다름

# 같은 한 쌍인데 거리는 `멀다`, 코사인은 `동일하다` 로 정반대
euclidean_distance(base, scaled)   # 2.236   멀다고 판정
cosine_similarity(base, scaled)    # 1.0     똑같다고 판정

euclidean_distance(base, nearby)   # 1.414   더 가깝다고 판정
cosine_similarity(base, nearby)    # 0.992   살짝 어긋났다고 판정
# --8<-- [end:scale_effect]

#! 텍스트에서 코사인을 쓰는 이유가 이 예시임.
#! 긴 문서는 단어가 많아서 벡터가 통째로 커짐. 거리로 재면 `길다` 는 이유만으로 안 비슷하다고 나옴.
#! 코사인은 길이를 나눠버려서 `무슨 단어가 어떤 비율로 들었는지` 만 봄.

# --8<-- [start:cosine_range]
right_angle = np.array([0.0, 2.0])
opposite = np.array([-2.0, 0.0])
same_way = np.array([3.0, 0.0])

cosine_similarity(np.array([1.0, 0.0]), same_way)      # 1.0    같은 방향
cosine_similarity(np.array([1.0, 0.0]), right_angle)   # 0.0    직각
cosine_similarity(np.array([1.0, 0.0]), opposite)      # -1.0   정반대 방향
# --8<-- [end:cosine_range]

#! 코사인의 `0` 은 `안 비슷함` 이 아니라 `아무 관계 없음` 임. `-1` 이 정반대.
#! 원-핫은 원소가 0 아니면 1 이라 음수가 안 나옴. 그래서 코사인이 0~1 사이만 나옴.
#! 원-핫끼리는 길이가 1 이라 `코사인 = 내적` 이 됨. 같으면 1, 다르면 0. 중간값이 없음.


#== 정리

#! 흐름  텍스트 → tokenize → 어휘(중복 제거) → 인덱스 dict → np.eye 로 원-핫
#! 어휘  `list(dict.fromkeys(x))` 는 첫 등장순, `sorted(set(x))` 는 가나다순
#! `list(set(x))` 는 실행마다 순서가 바뀜. 어휘에 절대 쓰면 안 됨
#! 인덱스  0부터. 인덱스가 곧 행 번호라서 그대로 배열에 꽂힘
#! 원-핫  `np.eye(어휘크기, dtype=int)[인덱스리스트]` 
#! 인덱싱  가장 바깥 대괄호 안 콤마 없으면 `행 목록`, 있으면 `좌표`
#! UNK  `dict.get(단어, UNK인덱스)`. 모르는 단어끼리 전부 같은 벡터가 되는 게 한계
#! 검증  `sum(axis=1)` 전부 1, `argmax(axis=1)` 이 원래 인덱스와 같으면 정상
#! 거리 vs 유사도  거리는 작을수록·유사도는 클수록 비슷. 방향이 반대
