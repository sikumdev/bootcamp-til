---
title: NumPy 기초 — NLP 를 위한 배열 다루기
date: 2026-09-01
tags: [numpy]
---

# NumPy 기초 — NLP 를 위한 배열 다루기

> 원본 코드: [`01_numpy_basic.py`](01_numpy_basic.py)

## 왜 리스트 말고 배열인가

같은 `+` 인데 뜻이 다름. 여기서 출발함.

<div class="til-code" markdown>
```python hl_lines="3"
import numpy as np

np.set_printoptions(precision=3, suppress=True)

left_list, right_list = [1, 2, 3], [10, 20, 30]
left_array = np.array(left_list)
right_array = np.array(right_list)

left_list + right_list      # [1, 2, 3, 10, 20, 30]   ← 이어붙이기
left_array + right_array    # [11 22 33]              ← 같은 자리끼리 더하기

left_list * 2               # [1, 2, 3, 1, 2, 3]      ← 두 번 반복
left_array * 2              # [2 4 6]                 ← 각 값을 두 배
```
<div class="til-note" data-til-line="3" hidden>precision=3 소수점 3자리까지만 표시<br>suppress=True 1e-05 같은 지수 표기 대신 0.00001 로 보여줌<br>화면 표시만 바뀜. 실제 값은 그대로임</div>
</div>

!!! warning
    리스트의 `+` 는 `이어붙이기`, 배열의 `+` 는 `원소끼리 더하기`.  
    리스트의 `*` 는 `반복`, 배열의 `*` 는 `각 값에 곱하기`.

## 배열 만들기와 구조 읽기

<div class="til-code" markdown>
```python
numbers_1d = np.array([10, 20, 30, 40])
numbers_2d = np.array([[10, 20, 30], [40, 50, 60]])

numbers_1d.shape    # (4,)      ← 값 4개짜리 1차원
numbers_2d.shape    # (2, 3)    ← 2행 3열
numbers_2d.ndim     # 2         ← 축이 2개 (행·열)
numbers_2d.size     # 6         ← 전체 값 개수 (2×3)
numbers_2d.dtype    # int64     ← 안에 담긴 숫자의 종류

#
# dtype 을 직접 정할 수 있음. 안 주면 값을 보고 알아서 정함
np.array([1, 2, 3], dtype=np.float32).dtype   
```
</div>

!!! warning
    `shape` — 모양. 튜플로 나옴 `(2, 3)`  
    `ndim`  — 축 개수. 차원  
    `size`  — 전체 값 개수. shape 를 다 곱한 것  
    `dtype` — 담긴 숫자의 종류 (int64 · float32 ...)  
    `shape` 가 `(4,)` 처럼 콤마로 끝나는 이유 → 원소 1개짜리 튜플이라서.  
    2차원부터는 `[행, 열]` 순서. 항상 행이 먼저임.

## 규칙이 있는 배열 — arange 와 linspace

<div class="til-code" markdown>
```python
np.arange(0, 11, 2)     # [ 0  2  4  6  8  10]   시작, 끝, 간격
np.linspace(0, 10, 6)   # [ 0.  2.  4.  6.  8. 10.]   시작, 끝, 개수

np.arange(0, 1, 0.25)   # [0.   0.25 0.5  0.75]        ← 1 이 없음
np.linspace(0, 1, 5)    # [0.   0.25 0.5  0.75 1.  ]   ← 1 이 있음
```
</div>

!!! warning
    `세 번째 인자의 뜻이 완전히 다름.`  
    `arange(시작, 끝, 간격)`  — 몇 개가 나올지는 계산해봐야 앎  
    `linspace(시작, 끝, 개수)` — 몇 개가 나올지 내가 정함  
    `끝 값 포함 여부도 다름`  
    `arange` 는 끝을 `포함 안 함` (파이썬 range 와 같음)  
    `linspace` 는 끝을 `포함함`  
    `반환 dtype 도 다름.`  
    `arange(0,11,2)` → int64   (정수만 넣으면 정수)  
    `linspace(0,10,6)` → float64 (항상 실수)

## 인덱싱과 슬라이싱

<div class="til-code" markdown>
```python hl_lines="6"
tokens = np.array(["나는", "오늘", "NLP를", "배운다"])
tokens[0]       # '나는'      한 개 (값이 나옴)
tokens[-1]      # '배운다'    뒤에서 첫 번째
tokens[1:3]     # ['오늘' 'NLP를']   범위 (배열이 나옴)

table = np.arange(1, 21).reshape(4, 5)
table[1, 2]        # 8  ← [행, 열]. 값 하나
table[1:3, 1:4]    # 2행 3열짜리 부분 배열
table[:, -1]       # [ 5 10 15 20]  ← 모든 행의 마지막 열
```
<div class="til-note" data-til-line="6" hidden>array([[ 1,  2,  3,  4,  5],<br>[ 6,  7,  8,  9, 10],<br>[11, 12, 13, 14, 15],<br>[16, 17, 18, 19, 20]])</div>
</div>

!!! warning
    인덱싱과 슬라이싱은 `나오는 게 다름`.  
    `t[1, 2]`   → 값 하나 (0차원)  
    `t[1, 1:3]` → 1차원 배열  
    `t[1:3, 1:3]` → 2차원 배열

<div class="til-code" markdown>
```python hl_lines="1"
x = np.arange(20).reshape(4, 5)
x[1:3, 1:3]        # [[ 6  7]
                   #  [11 12]]      연속된 사각형 영역


# 이건 슬라이싱이 아님. (1,1) 과 (1,2) 두 자리를 콕 집는 것
x[[1,1], [1,2]]    # [6 7]
```
<div class="til-note" data-til-line="1" hidden>array([[ 0,  1,  2,  3,  4],<br>[ 5,  6,  7,  8,  9],<br>[10, 11, 12, 13, 14],<br>[15, 16, 17, 18, 19]])<br>앞 리스트가 행 번호, 뒤 리스트가 열 번호. 짝을 지어 읽음<br>흩어진 위치를 골라올 때 씀. `fancy indexing` 이라고 부름</div>
</div>

## 조건 선택과 where

<div class="til-code" markdown>
```python hl_lines="9"
scores = np.array([55, 72, 88, 91, 64, 100])

# 조건을 걸면 True/False 배열이 나옴. 이걸 `마스크` 라고 함
passing_mask = scores >= 70    # [False True True True False True]  dtype=bool

# 마스크를 인덱스 자리에 넣으면 True 자리의 값만 골라옴
scores[passing_mask]    # [ 72  88  91 100]

# 조건 두 개는 `&` 와 `|`. and · or 는 안 됨
scores[(scores >= 70) & (scores < 90)]   # [72 88]

# where(조건, 참일때, 거짓일때) — 값을 바꿔치기함
np.where(scores >= 70, "통과", "재학습")   # ['재학습' '통과' '통과' '통과' '재학습' '통과']
```
<div class="til-note" data-til-line="9" hidden>그리고 각 조건을 반드시 괄호로 감쌀 것. 우선순위 때문에</div>
</div>

!!! warning
    `마스크로 고르기` 와 `where 로 바꾸기` 는 목적이 다름.  
    마스크 → 조건에 맞는 것만 `추려냄`. 개수가 줄어듦  
    where  → 개수는 그대로 두고 `값만 바꿈`

## np.where 에 인자를 하나만 주면

`np.where` 는 인자 개수에 따라 하는 일이 완전히 달라짐.

!!! warning
    인자 3개 `where(조건, A, B)` → 값을 바꿔치기  
    인자 1개 `where(조건)`       → 조건이 True 인 `위치(인덱스)` 를 돌려줌  
    게다가 튜플로 감싸서 나옴. 축마다 하나씩이라 그럼.  
    `값을 고르고 싶으면 where 가 아니라 마스크 인덱싱`.  
    `배열[조건]` 이 정답임.

## reshape 와 전치

<div class="til-code" markdown>
```python hl_lines="3"
flat = np.arange(1, 13)

# 원소 개수를 유지한 채 모양만 바꿈. 12개니까 3×4 가 됨
matrix = flat.reshape(3, 4)

matrix.shape      # (3, 4)

# T 는 전치. 행과 열이 자리를 바꿈
matrix.T.shape    # (4, 3)
```
<div class="til-note" data-til-line="3" hidden>개수가 안 맞으면 에러. 3×5 는 15개라 안 됨</div>
</div>

!!! warning
    `reshape(-1, 4)` 처럼 `-1` 을 쓰면 그 자리를 알아서 계산해 줌.  
    12개를 4열로 나누면 3행이니까 `reshape(-1, 4)` = `reshape(3, 4)`.

## 배열 결합 — concatenate

<div class="til-code" markdown>
```python
top = np.array([[1, 2], [3, 4]])
bottom = np.array([[5, 6]])
right = np.array([[10], [20]])

# axis=0 이 기본값. 안 적으면 아래로 붙음
np.concatenate([top, bottom], axis=0)   # 아래로 붙임 → (3, 2)
np.concatenate([top, right], axis=1)    # 옆으로 붙임 → (2, 3)
```
</div>

!!! warning
    붙이려면 `붙이는 방향이 아닌 축`의 크기가 같아야 함.  
    아래로(axis=0) 붙이려면 → 열 개수가 같아야 함  
    옆으로(axis=1) 붙이려면 → 행 개수가 같아야 함

## broadcasting — 모양이 다른 배열끼리 계산하기

작은 쪽을 `복사해서 채운 뒤` 같은 모양으로 만들어 계산함.

!!! warning
    핵심은 딱 하나 → `복사해서 채운다`.  
    늘리고 나면 둘 다 같은 shape 가 되니까 그냥 같은 자리끼리 더하면 끝임.

## 실제로 늘어난 모습 보기

np.broadcast_to 로 눈으로 확인할 수 있음.

<div class="til-code" markdown>
```python hl_lines="4 7"
import numpy as np

col = np.array([10, 20, 30])        # shape (3,)   가로로 누움
np.broadcast_to(col, (2, 3))

row = np.array([[100], [200]])      # shape (2,1)  세로로 섬
np.broadcast_to(row, (2, 3))
```
<div class="til-note" data-til-line="4" hidden>[[10 20 30]<br>[10 20 30]]   ← 아래로 복사됨. 두 행이 똑같음</div>
<div class="til-note" data-til-line="7" hidden>[[100 100 100]<br>[200 200 200]]  ← 옆으로 복사됨. 행마다 자기 값</div>
</div>

!!! warning
    `broadcast_to` 는 실제로 늘린 결과를 보여주는 함수임.  
    평소엔 안 쓰고, 이렇게 "어떻게 늘어나는지" 확인할 때만 씀.

<div class="til-code" markdown>
```python hl_lines="6 8"
matrix = np.array([[1, 2, 3], [4, 5, 6]])          # (2, 3)

# [[11 12 13], [14 15 16]]   모든 값에 10
matrix + 10

matrix + np.array([10, 20, 30])                    # (3,)

matrix + np.array([[100], [200]])                  # (2, 1)
```
<div class="til-note" data-til-line="6" hidden>[[11 22 33], [14 25 36]]<br>1행: 1+10, 2+20, 3+30 / 2행: 4+10, 5+20, 6+30<br>두 행이 `같은` [10,20,30] 을 씀 → 열마다 다른 값</div>
<div class="til-note" data-til-line="8" hidden>[[101 102 103], [204 205 206]]<br>1행: 전부 +100 / 2행: 전부 +200<br>행마다 `다른` 값을 씀</div>
</div>

## 규칙 — shape 를 뒤에서부터 맞춰봄

<div class="til-code" markdown>
```python
   (2,3)   vs   (3,)        →  자릿수가 모자라면 앞을 1 로 채움 → (1,3)
                                앞자리 2 와 1  → 한쪽이 1 이라 OK
                                1 인 자리가 늘어남 → 아래로 복사

   (2,3)   vs   (2,1)       →  뒷자리 3 과 1 → 한쪽이 1 이라 OK
                                1 인 자리가 늘어남 → 옆으로 복사

   (2,3)   vs   (2,)        →  뒷자리 3 과 2 → 다르고 1 도 아님 → 에러
```
</div>

!!! warning
    규칙 두 줄로 요약  
    ① 자릿수가 모자라면 `앞을 1 로` 채움  
    ② 각 자리를 비교해서 `같거나 한쪽이 1` 이면 OK. `1 인 쪽이 늘어남`

## 판단 기준 하나만 기억하기

!!! warning
    "이 값을 `행`마다 쓸 건가, `열`마다 쓸 건가?"  
    행마다 다른 값 → `(행수, 1)` 로 `세워야` 함  
    열마다 다른 값 → `(열수,)` 그대로 `누운 채`로 두면 됨  
    `mean` · `sum` 같은 집계는 축을 없애서 항상 누운 채로 나옴.  
    → 행 단위로 쓸 거면 다시 세우거나, `keepdims=True` 로 애초에 안 눕게 할 것.  
    확인 습관 → 빼기 전에 `양쪽 shape 를 찍어볼 것`.  
    (3,3) 과 (3,) 이면 의심. (3,3) 과 (3,1) 이면 안심.  
    실무에서는 `keepdims=True` 를 쓰는 쪽이 많음.  
    나중에 `[:, None]` 을 붙이는 걸 잊어버릴 일이 없어서.

## axis — 집계 방향

<div class="til-code" markdown>
```python
matrix = np.array([[1, 2, 3], [4, 5, 6]])   # (2, 3)

matrix.sum(axis=0)    # [5 7 9]      열별 합 → 결과 (3,)
matrix.sum(axis=1)    # [ 6 15]      행별 합 → 결과 (2,)
matrix.mean(axis=1)   # [2. 5.]      행별 평균
```
</div>

!!! warning
    ★ `axis=N` 은 "N번 축을 없앤다" 는 뜻.  
    axis=0 → 0번 축(행)이 사라짐 → 열마다 하나씩 남음 → `열별` 결과  
    axis=1 → 1번 축(열)이 사라짐 → 행마다 하나씩 남음 → `행별` 결과  
    shape 로 확인하는 게 제일 확실함  
    (2,3) 에서 axis=0 → (3,) 남음. 3은 열 개수  
    (2,3) 에서 axis=1 → (2,) 남음. 2는 행 개수

## 난수 만들기

<div class="til-code" markdown>
```python
# seed 를 고정하면 매번 같은 난수가 나옴. 실습·테스트에 필수
np.random.seed(42)

# rand 는 0~1 사이 실수. 인자로 shape 를 그냥 나열함
np.random.rand(2, 2)

# randint 는 정수. size 를 안 주면 숫자 하나만 나옴
np.random.randint(1, 10)                # 7        0차원 (그냥 숫자)
np.random.randint(1, 10, size=(2,))     # [7 8]    1차원
np.random.randint(1, 10, size=(2, 2))   # 2차원

# 주어진 목록에서 골라서 그 shape 로 채움
np.random.choice([1, 2, 3, 4, 5], size=(2, 2))
```
</div>

!!! warning
    rand   → 인자로 그냥 나열 `rand(2, 2)`  
    randint → `size=` 키워드로 `randint(1, 10, size=(2,2))`

## NLP 문서-단어 행렬

행이 문서, 열이 단어. NumPy 를 배운 이유가 여기 있음.

<div class="til-code" markdown>
```python hl_lines="11 19"
terms = np.array(["data", "model", "agent", "tool"])
counts = np.array([
    [3, 1, 2, 0],    # 문서 1 — data 3번, model 1번, agent 2번, tool 0번
    [0, 2, 1, 4],    # 문서 2
    [2, 0, 5, 1],    # 문서 3
])

counts.sum(axis=1)    # [6 7 8]        문서별 길이 (행별 합)
counts.sum(axis=0)    # [5 3 8 5]      단어별 전체 빈도 (열별 합)

# argmax = 가장 큰 값의 `위치`. max 는 값, argmax 는 인덱스
top_indices = counts.argmax(axis=1)    # [0 3 2]

terms[top_indices]    # ['data' 'tool' 'agent']


term_weights = np.array([1.0, 0.5, 2.0, 1.5])

# 문서마다 "빈도 × 가중치" 를 다 더한 점수가 나옴
counts @ term_weights    # [ 7.5  9.  13.5]
```
<div class="til-note" data-til-line="11" hidden>1행 최댓값 3 → 0번, 2행 최댓값 4 → 3번, 3행 최댓값 5 → 2번</div>
<div class="til-note" data-til-line="19" hidden>@ 는 행렬곱. (3,4) @ (4,) → (3,)</div>
</div>

!!! warning
    `argmax` 와 `max` 를 헷갈리지 말 것.  
    `max(axis=1)`    → 각 행의 최댓값 `값`  
    `argmax(axis=1)` → 각 행의 최댓값 `위치`  
    `terms[counts.argmax(axis=1)]` 이 오늘 배운 것의 총합임.  
    ① argmax 로 위치를 구하고 ② 그 위치로 단어 배열을 인덱싱.  
    위치를 이름으로 바꾸는 이 패턴은 계속 나옴.

## 정리

!!! warning
    배열     — 리스트와 달리 `+` 가 원소끼리 더하기  
    shape · ndim · size · dtype — 모양 · 축 개수 · 값 개수 · 자료형  
    arange(시작,끝,간격) 끝 제외 / linspace(시작,끝,개수) 끝 포함  
    인덱싱 `[행, 열]` — 숫자를 쓰면 축이 사라지고 슬라이스를 쓰면 남음  
    마스크 `배열[조건]` 로 고르기 / `np.where(조건, A, B)` 로 바꾸기  
    reshape 는 개수 유지 · `.T` 는 전치 · concatenate 는 axis 로 방향 지정  
    broadcasting — 1차원은 `가로줄`. 세로로 쓰려면 `[:, None]`  
    `axis=N` = "N번 축을 없앤다" → axis=0 은 열별, axis=1 은 행별 결과  
    argmax 로 위치를 구해 다른 배열을 인덱싱하는 패턴이 핵심
