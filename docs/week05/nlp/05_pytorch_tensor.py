"""
title: PyTorch 텐서 기초 — shape · 축 · 브로드캐스팅 · 행렬곱
tags: [pytorch, nlp]
"""

#== 텐서는 numpy 배열과 거의 같음
#> 앞 노트들에서 numpy 로 하던 걸 그대로 torch 로 옮기는 단계.

#! 결론부터 → `텐서 = numpy 배열 + GPU + 자동미분`.
#! numpy `axis` → torch `dim` (torch 는 `axis` 도 받아줌)
#! numpy `keepdims` → torch `keepdim` (s 없음)
#! numpy `np.array` → torch `torch.tensor`
#! numpy `.reshape` → torch `.reshape` / `.view` (둘이 다름. 뒤에서 정리)


#== 0. 환경과 시드

# --8<-- [start:setup]
import random
import torch

# random 과 torch 는 난수 생성기가 따로임. 둘 다 고정해야 함
SEED = 42
random.seed(SEED)
torch.manual_seed(SEED)

torch.__version__   # '2.13.0+cu130'
# --8<-- [end:setup]

#! 시드를 고정해도 `셀을 다시 돌리면 값이 달라짐`. 직접 확인함.
#! 시드는 `난수 생성기의 시작 위치`를 정하는 거라서, 뽑을 때마다 위치가 앞으로 감.


#== 1. 차원과 shape — NLP 에서 축이 뜻하는 것

# --8<-- [start:dims]
scalar = torch.tensor(7)                      # 0차원
word_vector_1d = torch.tensor([1, 0, 0, 0])   # 1차원 — 단어 하나
sentence_2d = torch.tensor([                  # 2차원 — 문장 하나
    [1, 0, 0, 0],
    [0, 1, 0, 0],
])
mini_batch_3d = torch.tensor([                # 3차원 — 문장 여러 개
    [[1, 0, 0, 0], [0, 1, 0, 0]],
    [[1, 0, 0, 0], [0, 0, 1, 0]],
    [[1, 0, 0, 0], [0, 0, 0, 1]],
])

sentence_2d.ndim      # 2 (축이 몇 개인가)
sentence_2d.shape     # torch.Size([2, 4])   각 축의 길이
sentence_2d.numel()   # 8 (전체 원소 수 = 2 * 4)
# --8<-- [end:dims]

#! `ndim`   축의 개수. shape 의 자릿수
#! `shape`  각 축의 길이. 튜플
#! `numel`  전체 원소 수. shape 를 전부 곱한 값

#! 축 번호는 `shape 의 왼쪽부터 0, 1, 2`. torch 는 축을 `dim` 이라고 부름.

# --8<-- [start:axis_meaning]
  텐서          shape        dim=0        dim=1          dim=2
  단어 하나     (4,)         표현값 4개   -              -
  문장 하나     (2, 4)       단어 2개     표현값 4개     -
  미니배치      (3, 2, 4)    문장 3개     문장별 단어 2개  단어별 표현값 4개
# --8<-- [end:axis_meaning]

#! NLP 에서 축이 늘어나는 순서 → `단어 → 문장 → 미니배치`.
#! 새 축은 항상 `맨 앞`에 붙음. 그래서 배치 축이 dim=0 임.

# --8<-- [start:axis_select]
sentence_2d[0]      # tensor([1, 0, 0, 0])   0번 축에서 하나 → 첫 단어 벡터
sentence_2d[:, 0]   # tensor([1, 0])         1번 축에서 하나 → 모든 단어의 첫 표현값

scalar.shape        # torch.Size([])   0차원은 shape 가 비어 있음
scalar.item()       # 7                파이썬 숫자로 꺼내기
# --8<-- [end:axis_select]

#! `torch.Size` 는 튜플을 상속받은 클래스임. 
#! 그래서 `sentence_2d.shape == (2, 4)` 가 True 로 나옴. 튜플과 그냥 비교하면 됨.
#! 0차원은 `torch.Size([])` 이고 `== ()` 도 True.


#== 2. 텐서 만들기와 dtype

# --8<-- [start:create]
torch.zeros(2, 3)              # 0으로 채운 (2, 3)
torch.ones(2, 3)               # 1로 채운 (2, 3)

# arange 는 `간격`을 주고, linspace 는 `개수`를 줌. linspace 는 끝값을 포함
torch.arange(0, 10, 2)         # tensor([0, 2, 4, 6, 8])   끝값 10 은 제외
torch.linspace(0, 1, steps=5)  # tensor([0.0000, 0.2500, 0.5000, 0.7500, 1.0000])

torch.manual_seed(42)
torch.rand(2, 3)
# tensor([[0.8823, 0.9150, 0.3829],
#         [0.9593, 0.3904, 0.6009]])
# --8<-- [end:create]

#! ★ `np.zeros((2, 3))` 은 shape 를 튜플로 줬는데 `torch.zeros(2, 3)` 은 그냥 나열함.
#! numpy 는 튜플, torch 는 나열. 헷갈리기 딱 좋으니 주의.

# --8<-- [start:dtype]
torch.tensor([1, 2, 3]).dtype           # torch.int64
torch.tensor([1.0, 2.0, 3.0]).dtype     # torch.float32
torch.tensor([True, False, True]).dtype # torch.bool
torch.zeros(2, 3).dtype                 # torch.float32
#(1)> zeros·ones·rand 는 기본이 float32

# .to() 로 형변환. torch.long 은 torch.int64 와 같은 것
torch.tensor([1, 2, 3]).to(torch.long)
torch.long is torch.int64   # True
# --8<-- [end:dtype]

#! `int64 (long)` — 단어 번호, 정답 클래스. 임베딩 조회에 쓸 id 는 반드시 정수여야 함
#! `float32`      — 입력 벡터, 가중치. 신경망 계산은 전부 실수
#! `bool`         — 마스크. 패딩 위치를 표시할 때 씀


#== 3. 인덱싱 — 임베딩 조회가 사실 이것

# --8<-- [start:indexing]
numbers = torch.tensor([[10, 11, 12, 13],
                        [20, 21, 22, 23],
                        [30, 31, 32, 33]])

numbers[0]        # tensor([10, 11, 12, 13])   0행 전체
numbers[1, 2]     # tensor(22)                 1행 2열. 0차원 텐서로 나옴
numbers[:, -1]    # tensor([13, 23, 33])       모든 행의 마지막 열
numbers[:2, 1:3]  # [[11, 12], [21, 22]]       앞 두 행 · 가운데 두 열
# --8<-- [end:indexing]


# --8<-- [start:embedding_lookup]
embedding_table = torch.tensor([
    [0.1, 0.2, 0.3],   # 단어 0
    [0.4, 0.5, 0.6],   # 단어 1
    [0.7, 0.8, 0.9],   # 단어 2
    [1.0, 1.1, 1.2],   # 단어 3
])
# 2번 행, 0번 행 선택
selected_word_ids = torch.tensor([2, 0])

selected_vectors = embedding_table[selected_word_ids]
# tensor([[0.7000, 0.8000, 0.9000],
#         [0.1000, 0.2000, 0.3000]])

selected_vectors.shape   # torch.Size([2, 3])   조회한 단어 2개 × 표현 차원 3
# --8<-- [end:embedding_lookup]

#! 임베딩은 `원-핫 벡터를 곱하는 게 아니라 표에서 행을 꺼내오는` 것임.
#! 원-핫과 행렬을 곱하면 결과가 그 행 하나인데, 어차피 그럴 거면 곱셈이 낭비라서 그냥 뽑음.
#! 이게 `nn.Embedding` 이 하는 일의 전부임.


#== 4. shape 바꾸기 — reshape

# --8<-- [start:reshape]
values = torch.arange(12)

values.reshape(3, 4)    # 3행 4열
values.reshape(2, 6)    # 2행 6열

# -1 은 `나머지는 알아서 계산해라`. 12 / 4 = 3 이라 3이 들어감
values.reshape(-1, 4)   # torch.Size([3, 4])


# 원소 수가 안 맞으면 실패. 5 * 3 = 15 인데 원소는 12개
# RuntimeError: shape '[5, 3]' is invalid for input of size 12

try:
    values.reshape(5, 3)
except RuntimeError as error:
    print(error)
# --8<-- [end:reshape]

#! reshape 는 `원소 수를 바꾸지 않음`. 담는 상자 모양만 바꾸는 것.
#! 그래서 `numel()` 은 항상 같아야 함. 이게 안 맞으면 무조건 RuntimeError.
#! `-1` 은 한 자리에만 쓸 수 있음. 두 자리를 비우면 계산이 안 됨.

# --8<-- [start:reshape_share]
original = torch.arange(6)
viewed = original.reshape(2, 3)
viewed[0, 0] = 999

# reshape 로 만든 걸 고쳤는데 원본이 같이 바뀜
original          # tensor([999, 1, 2, 3, 4, 5])
original.data_ptr() == viewed.data_ptr()   # True   같은 메모리를 봄

safe = torch.arange(6)

# 원본을 지키려면 .clone() 으로 복사해야 함
copied = safe.reshape(2, 3).clone()
copied[0, 0] = 999
safe              # tensor([0, 1, 2, 3, 4, 5])   원본 그대로
# --8<-- [end:reshape_share]

#! `reshape` 는 값을 복사하는 게 아니라 `같은 메모리를 다른 모양으로 보는` 것임.
#! 새 변수에 담았다고 안심하면 안 됨.

# --8<-- [start:view_vs_reshape]
x = torch.arange(12).reshape(3, 4)
transposed = x.t()

# 전치하면 값 순서가 메모리 순서와 어긋남
transposed.is_contiguous()   # False

# view 는 메모리가 연속일 때만 됨
# RuntimeError: view size is not compatible with input tensor's size and stride ...
try:
    transposed.view(12)
except RuntimeError as error:
    print(error)

transposed.reshape(12)   # tensor([0, 4, 8, 1, 5, 9, 2, 6, 10, 3, 7, 11])
#(2)> reshape 는 필요하면 알아서 복사해서 성공시킴
# --8<-- [end:view_vs_reshape]

#! `view` 와 `reshape` 의 차이 → 실패했을 때 어떻게 하느냐.
#! `view`    항상 메모리 공유. 안 되면 그냥 에러
#! `reshape` 되면 공유, 안 되면 복사해서라도 성공


#== unsqueeze / squeeze — 길이 1인 축 넣고 빼기

# --8<-- [start:unsqueeze]
sentence_vectors = torch.arange(12, dtype=torch.float32).reshape(3, 4)

# 인자는 `새 축의 크기`가 아니라 `넣을 위치`임. 새 축 크기는 항상 1
sentence_vectors.unsqueeze(0).shape    # (1, 3, 4)   맨 앞에 배치 축
sentence_vectors.unsqueeze(1).shape    # (3, 1, 4)   가운데
sentence_vectors.unsqueeze(2).shape    # (3, 4, 1)   맨 뒤
sentence_vectors.unsqueeze(-1).shape   # (3, 4, 1)   -1 은 맨 뒤. (2) 와 같음

# 2차원이라 쓸 수 있는 범위가 -3 ~ 2 임
try:
    sentence_vectors.unsqueeze(3)
except IndexError as error:
    print(error)
# IndexError: Dimension out of range (expected to be in range of [-3, 2], but got 3)
# --8<-- [end:unsqueeze]

#! 음수도 됨. `unsqueeze(-3)` → `(1, 3, 4)` 로 `unsqueeze(0)` 과 같음. 직접 확인함.
#! 범위가 `[-3, 2]` 인 이유가 이것임. 앞에서 세면 0~2, 뒤에서 세면 -1~-3.

#! NLP 에서 거의 항상 `unsqueeze(0)` 을 씀.
#! 모델은 `(배치, 문장길이, 표현차원)` 3차원을 기대하는데
#! 문장 하나만 넣고 싶으면 `(문장길이, 표현차원)` 앞에 배치 축 1을 붙여야 해서.

# --8<-- [start:squeeze]
batch_vectors = sentence_vectors.unsqueeze(0)
batch_vectors.squeeze(0).shape    # (3, 4)   넣었던 축을 다시 뺌

messy = torch.zeros(1, 3, 1, 4, 1)

# 인자 없이 쓰면 길이 1인 축을 `전부` 지움
messy.squeeze().shape    # (3, 4)
messy.squeeze(0).shape   # (3, 1, 4, 1)   0번 축만 지움

# 지정한 축의 길이가 1이 아니면 아무 일도 안 일어남. 에러도 안 남
messy.squeeze(1).shape   # (1, 3, 1, 4, 1)
# --8<-- [end:squeeze]


#! `squeeze()` 를 인자 없이 쓰면 `배치 크기가 1일 때 배치 축까지 같이 날아감`.
#! → 항상 `squeeze(0)` 처럼 축을 지정할 것. 이게 규칙.



#== flatten — 여러 축을 한 줄로

# --8<-- [start:flatten]
context_embeddings = torch.arange(24, dtype=torch.float32).reshape(2, 3, 4)

# start_dim=1 은 `1번 축부터 뒤를 전부 합쳐라`. 3 * 4 = 12
context_embeddings.flatten(start_dim=1).shape   # (2, 12)

# 인자 없이 쓰면 전부 한 줄. 배치 축까지 사라짐
context_embeddings.flatten().shape              # (24,)

#reshape(2, -1) 로도 같은 결과. -1 이 나머지를 계산해 줌
torch.equal(context_embeddings.flatten(start_dim=1),
            context_embeddings.reshape(2, -1))  # True
# --8<-- [end:flatten]

#! 왜 쓰냐 → `Linear` 층은 2차원 `(배치, 특징수)` 만 받아서.
#! 단어 3개짜리 문장의 임베딩 `(3, 4)` 를 그대로 못 넣으니 `(12,)` 로 펴서 넣음.
#! `start_dim=1` 을 꼭 줘야 함. 안 주면 배치까지 뭉개져서 문서 구분이 사라짐.


#== 5. 브로드캐스팅

# --8<-- [start:broadcast]
batch = torch.tensor([[1., 2., 3.],
                      [4., 5., 6.]])
bias = torch.tensor([0.1, 0.2, 0.3])

# (2, 3) + (3,) → bias 가 두 줄로 복사되어 더해짐
batch + bias
# tensor([[1.1000, 2.2000, 3.3000],
#         [4.1000, 5.2000, 6.3000]])

# (2, 3) + (2, 1) → column 이 세 칸으로 복사됨
column = torch.tensor([[10.], [20.]])
batch + column
# tensor([[11., 12., 13.],
#         [24., 25., 26.]])

# (2, 3) + (2,) 는 실패. 뒤에서부터 맞춰보면 3 과 2 라서
try:
    batch + torch.tensor([1., 2.])
except RuntimeError as error:
    print(error)
# RuntimeError: The size of tensor a (3) must match the size of tensor b (2)
#              at non-singleton dimension 1
# --8<-- [end:broadcast]

#! 규칙은 `뒤에서부터 축을 맞춰보고, 같거나 한쪽이 1이면 늘린다` 임.
#! `(2,3)` 과 `(3,)` → 뒤부터 3 vs 3 통과, 앞은 없으니 늘림 → OK
#! `(2,3)` 과 `(2,)` → 뒤부터 3 vs 2 → 실패
#! 앞에서 맞추는 게 아니라 `뒤에서` 맞춤. 이게 핵심임.

# --8<-- [start:keepdim]
# shape (2, 1). 접은 축을 없애는 대신 길이 1로 남김
batch.sum(dim=1)                  # tensor([ 6., 15.])   shape (2,)
batch.sum(dim=1, keepdim=True)
# tensor([[ 6.],
#         [15.]])

# (2,3) / (2,1) → 뒤부터 3 vs 1 이라 1이 늘어남. 행마다 비율이 나옴
batch / batch.sum(dim=1, keepdim=True)
# tensor([[0.1667, 0.3333, 0.5000],
#         [0.2667, 0.3333, 0.4000]])

# --8<-- [end:keepdim]

#== 6. 행렬곱 — 신경망 한 층

# --8<-- [start:matmul]
inputs = torch.tensor([[1., 2., 3.],
                       [4., 5., 6.]])
weights = torch.tensor([[0.1, 0.2],
                        [0.3, 0.4],
                        [0.5, 0.6]])
bias = torch.tensor([0.5, -0.5])

linear_output = inputs @ weights + bias
# tensor([[2.7000, 2.3000],
#         [5.4000, 5.9000]])
linear_output.shape   # torch.Size([2, 2])
#(1)> (2, 3) @ (3, 2) → (2, 2). 안쪽 3이 사라지고 바깥 2, 2 가 남음
# --8<-- [end:matmul]

#! shape 규칙 → `(a, b) @ (b, c) = (a, c)`. 안쪽 b 가 맞아야 하고 계산 후 사라짐.
#! NLP 로 읽으면 `(배치, 입력차원) @ (입력차원, 출력차원) = (배치, 출력차원)`.
#! 가중치의 첫 자리가 `입력 차원`, 둘째 자리가 `출력 차원` 임.

# --8<-- [start:matmul_traps]
a = torch.tensor([[1., 2.], [3., 4.]])
b = torch.tensor([[10., 20.], [30., 40.]])

# `*` 와 `@` 는 완전히 다름. `*` 는 같은 자리끼리, `@` 는 행 × 열
a * b     # [[10., 40.], [90., 160.]]     원소별 곱
a @ b     # [[70., 100.], [150., 220.]]   행렬곱

# 안쪽 숫자가 안 맞으면 실패
# RuntimeError: mat1 and mat2 shapes cannot be multiplied (2x3 and 2x3)
try:
    torch.rand(2, 3) @ torch.rand(2, 3)
except RuntimeError as error:
    print(error)

# dtype 이 다르면 실패. int 와 float 를 섞을 수 없음
# RuntimeError: expected m1 and m2 to have the same dtype, but got: long int != float
try:
    torch.tensor([[1, 2], [3, 4]]) @ torch.tensor([[1., 2.], [3., 4.]])
except RuntimeError as error:
    print(error)
# --8<-- [end:matmul_traps]


#! `*` 는 브로드캐스팅이 되고 `@` 는 안 됨. 규칙이 아예 다름.
#! `*` 는 `뒤에서부터 맞춰보고 1이면 늘림`, `@` 는 `안쪽 숫자가 정확히 같아야 함`.


# --8<-- [start:batch_matmul]
batch_3d = torch.arange(24, dtype=torch.float32).reshape(2, 3, 4)
layer_weight = torch.arange(8, dtype=torch.float32).reshape(4, 2)

# (2, 3, 4) @ (4, 2) → 앞의 배치 축 2는 그대로 두고 뒤 두 축만 곱함
(batch_3d @ layer_weight).shape   # torch.Size([2, 3, 2])
# --8<-- [end:batch_matmul]

#!  3차원 @ 2차원이 되는 게 중요함. 배치를 반복문으로 돌 필요가 없음.
#! `@` 는 `마지막 두 축만 행렬곱하고 앞 축은 배치로 취급` 함.
#! 문장 여러 개를 한 번에 층에 통과시키는 게 이래서 가능함.


#== numpy 와 오가기

# --8<-- [start:numpy_bridge]
import numpy as np

arr = np.array([[1, 2], [3, 4]])
tensor = torch.from_numpy(arr)
tensor[0, 0] = 999

# from_numpy 는 메모리를 공유함. 텐서를 고치면 numpy 배열도 바뀜
arr[0, 0]   # 999

# .numpy() 로 되돌릴 때도 공유
np.shares_memory(tensor.numpy(), arr)   # True
# --8<-- [end:numpy_bridge]

#! `torch.from_numpy` 는 공유, `torch.tensor` 는 복사. 이름으로는 구분이 안 되니 외워야 함.


#== 이름 대응표 — numpy vs torch

# --8<-- [start:numpy_vs_torch]
#  하는 일           numpy                    torch
#  배열 만들기       np.array([1,2])          torch.tensor([1,2])
#  0으로 채우기      np.zeros((2,3))          torch.zeros(2, 3)      ← 괄호 차이
#  범위              np.arange(0,10,2)        torch.arange(0,10,2)
#  난수              np.random.rand(2,3)      torch.rand(2, 3)
#  축                axis                     dim  (axis 도 받아줌)
#  축 유지           keepdims                 keepdim (keepdims 도 받아줌)
#  모양 바꾸기       .reshape(3,4)            .reshape(3,4) / .view(3,4)
#  축 추가           np.expand_dims(a, 0)     .unsqueeze(0)
#  축 제거           np.squeeze(a)            .squeeze(0)
#  전치              .T                       .t()  또는 .transpose(0,1)
#  행렬곱            @  또는 np.dot           @  또는 torch.matmul
#  원소 수           .size                    .numel()
#  차원 수           .ndim                    .ndim
#  복사              .copy()                  .clone()
# --8<-- [end:numpy_vs_torch]


#! numpy `.size` 는 `원소 수`(정수), torch `.size()` 는 `shape`(튜플) 임. 뜻이 다름.
#! torch 에서 원소 수는 `.numel()`.


#== 정리

#! 텐서  numpy 배열 + GPU + 자동미분. shape·축·브로드캐스팅은 numpy 와 같음
#! 축    ndim(개수) · shape(각 축 길이) · numel(전체 원소 수)
#! NLP 축  (배치, 문장길이, 표현차원). 새 축은 항상 맨 앞에 붙음
#! dtype  단어 id 는 int64, 입력·가중치는 float32. 소수점 하나로 갈림
#! reshape  원소 수 유지. -1 은 나머지 자동 계산. ★ 원본과 메모리 공유
#! unsqueeze  인자는 크기가 아니라 `넣을 위치`. 새 축 크기는 항상 1
#! squeeze() · flatten()  인자 없이 쓰면 배치 축까지 없앰. 항상 축을 지정할 것
#! keepdim  접은 축을 길이 1로 남김. 
#! 행렬곱  (a,b) @ (b,c) = (a,c). 안쪽이 맞아야 하고 계산 후 사라짐
#! `*` 는 원소별, `@` 는 행렬곱. 순서를 바꿔도 통과할 수 있어서 shape 를 꼭 확인

