"""
title: 경사 하강법 — 딥러닝이 학습하는 흐름만
tags: [nlp]
"""

#== 딥러닝 학습 흐름

#! 직선을 아무 데나 그어놓고 → 얼마나 틀렸는지 재고 → 조금 옮기고 → 반복.
#! 이걸 100번 하면 점들을 잘 가르는 직선이 나옴. `경사 하강법` 이 이 반복임.


#== 전체 흐름 5단계

# --8<-- [start:flow]
  1. 예측    직선에 점을 넣어 `클래스 1일 확률` 을 뽑음       output_formula
  2. 오차    정답과 얼마나 다른지 숫자 하나로 잼             error_formula
  3. 갱신    오차가 줄어드는 방향으로 직선을 조금 움직임       update_weights
  4. 반복    점 100개 전부에 대해 1~3 을 함 = 1 에포크
  5. 종료    에포크 100번 돌리고 최종 직선을 씀             train
# --8<-- [end:flow]

#! 여기는 파라미터가 3개(가중치 2 + 편향 1), GPT 는 수천억 개.

#== 1. 예측 — sigmoid 로 확률 만들기

# --8<-- [start:sigmoid]
import numpy as np

def sigmoid(value):
    value = np.clip(value, -500, 500)
    return 1 / (1 + np.exp(-value))

def output_formula(features, weights, bias):
    # `inputs @ weights + bias` 와 똑같은 계산임
    linear_score = np.dot(features, weights) + bias
    return sigmoid(linear_score)

sigmoid(0)     # 0.5
sigmoid(2)     # 0.8807970779778823
sigmoid(-2)    # 0.11920292202211755
sigmoid(5)     # 0.9933071490757153
# --8<-- [end:sigmoid]

#!  sigmoid 가 하는 일 하나 → `아무 실수나 받아서 0~1 사이로 눌러줌`.
#! `np.dot(...) + bias` 는 -100 도 나오고 +50 도 나오는데, 확률로 쓰려면 0~1 이어야 해서.

#! 값 읽는 법
#! 0 을 넣으면 정확히 0.5 → `모르겠음`
#! 양수를 넣으면 0.5 보다 큼 → `클래스 1 쪽`
#! 음수를 넣으면 0.5 보다 작음 → `클래스 0 쪽`


#== 2. 오차 — 틀린 확신에 큰 벌점

# --8<-- [start:error]
def error_formula(target, output):
    output = np.clip(output, 1e-12, 1 - 1e-12)
    return -target * np.log(output) - (1 - target) * np.log(1 - output)

error_formula(1, 0.9)   # 0.105   정답 1인데 0.9 로 예측. 거의 안 틀림
error_formula(1, 0.5)   # 0.693   반반. 중간 벌점
error_formula(1, 0.1)   # 2.303   정답 1인데 0.1 로 예측. 큰 벌점
error_formula(0, 0.9)   # 2.303   정답 0인데 0.9 로 확신. 역시 큰 벌점
# --8<-- [end:error]

#! 핵심은 `틀린 정도가 아니라 틀린 확신에 벌점을 준다` 는 것.
#! 0.9 를 0.5 로 바꾸면 오차가 0.105 → 0.693 으로 6배 넘게 뜀. 선형이 아님.
#! log 를 쓰기 때문임. 확률이 0에 가까워질수록 벌점이 무한대로 감.

#! 이름은 `이진 교차 엔트로피(binary cross-entropy)`. BCE 라고 줄여 부름.
#! `분류 문제의 표준 손실 함수` 라는 것만 알면 됨.


#== 3. 갱신 — 왜 빼는 게 아니라 더하나

# --8<-- [start:update]
def update_weights(features, target, weights, bias, learnrate):
    output = output_formula(features, weights, bias)
    prediction_error = target - output
    # `정답 - 예측`. 예측이 작으면 양수, 크면 음수가 나옴

    weights += learnrate * prediction_error * features
    bias += learnrate * prediction_error
    return weights, bias

#! 예측이 정답보다 작으면 → 오차가 양수 → 가중치를 키움 → 다음엔 더 크게 예측
#! 예측이 정답보다 크면 → 오차가 음수 → 가중치를 줄임
#! `틀린 방향의 반대로 조금씩 민다` 가 학습의 전부임.
#! `learnrate` 는 `한 번에 얼마나 밀지`. 보통 0.01 같은 작은 값.

# --8<-- [end:update]

#! 원래 경사하강 공식은 `w = w - 학습률 * 기울기` 이고
#! BCE 의 기울기는 `(예측 - 정답) * x` 임.
#! 그래서 `w - lr * (예측 - 정답) * x` = `w + lr * (정답 - 예측) * x` 로 같음.
#! 즉 `prediction_error = target - output` 이 이미 마이너스를 흡수한 것.

#== 4. 학습 루프 — 에포크

# --8<-- [start:train_loop]
import pandas as pd

SEED, EPOCHS, LEARNRATE = 44, 100, 0.01

data = pd.read_csv("data.csv", header=None, names=["f1", "f2", "target"])
X = data[["f1", "f2"]].to_numpy(dtype=float)
y = data["target"].to_numpy(dtype=int)

# 시작 직선은 무작위.
np.random.seed(SEED)
weights = np.random.normal(scale=1 / np.sqrt(2), size=2)
bias = 0.0

# 바깥 반복 = 에포크, 안쪽 반복 = 샘플 하나씩
for epoch in range(EPOCHS):
    for sample, target in zip(X, y):
        weights, bias = update_weights(sample, target, weights, bias, LEARNRATE)
# --8<-- [end:train_loop]

#! `에포크(epoch)` = 데이터 전체를 한 번 다 본 것. 여기선 점 100개를 한 바퀴.
#! `SGD(확률적 경사 하강법)` = 샘플 하나 볼 때마다 바로 갱신하는 방식.


#== 5. 실제 돌린 결과

# --8<-- [start:result]
# Epoch   0 | loss=0.713585 | accuracy=0.400
# Epoch  20 | loss=0.554874 | accuracy=0.740
# Epoch  50 | loss=0.425255 | accuracy=0.930
# Epoch  90 | loss=0.337927 | accuracy=0.940
#
# 학습된 가중치: [-3.67329516 -3.02049558]
# 학습된 편향: 3.2803545886233767
# 최종 손실: 0.324899   (초기 0.713585)
# 최종 정확도: 0.940
# --8<-- [end:result]

#! 데이터를 직접 받아서 100 에포크 전부 돌린 실제 값임.

#! 시작 정확도가 `0.400` 임. 
#! 무작위 직선으로 시작하니 당연한 것. 여기서 0.940 까지 올라간 게 학습의 결과임.

#! 초기 가중치는 `[-0.53, 0.93]` 인데 학습 후 `[-3.67, -3.02]` 로 부호까지 바뀜.
#! 값이 커진 건 sigmoid 를 0/1 쪽으로 확실히 밀기 위해서임.

#! 손실이 100 에포크 내내 한 번도 안 올랐음. 
#! 손실이 계속 내려가면 학습이 잘 되는 중. 


#== 학습률과 에포크를 바꿔보면

# --8<-- [start:hyperparams]
#  학습률(lr)   최종 손실   정확도
#  0.001        0.6266      0.690    ← 너무 작아서 100번으로 못 감
#  0.01         0.3249      0.940    ← 교재 기본값
#  0.1          0.1617      0.930
#  1.0          0.2556      0.930
#  10.0         2.1200      0.800    ← 너무 커서 튕겨나감

#  에포크       최종 손실   정확도
#  10           0.6302      0.570
#  100          0.3249      0.940
#  1000         0.1562      0.920
#  5000         0.1368      0.920    ← 손실은 줄어도 정확도는 안 오름
# --8<-- [end:hyperparams]


#! 학습률은 `너무 작으면 못 가고 너무 크면 튕겨나감`. 중간값을 찾아야 함.
#! 이런 걸 `하이퍼파라미터` 라고 부름. 모델이 배우는 게 아니라 내가 정해주는 값.
#! 에포크 1000·5000 에서 손실은 줄었는데 정확도는 오히려 0.94 → 0.92 로 떨어짐.
#! 손실이 낮다고 항상 좋은 게 아니라는 뜻임. 이게 나중에 나올 `과적합` 이야기의 씨앗.




#== 정리

#! 흐름  예측 → 오차 → 갱신 → 반복. 딥러닝 학습은 전부 이 네 단계임
#! sigmoid  아무 실수나 0~1 로 눌러줌. 0 을 넣으면 0.5
#! 오차(BCE)  틀린 `확신` 에 큰 벌점. log 라서 확률이 0에 가까우면 벌점이 폭증
#! 갱신식이 `+=` 인 이유  `정답 - 예측` 순서로 써서 마이너스를 이미 흡수함
#! 에포크  데이터 전체를 한 번 다 본 것. SGD 는 샘플마다 바로 갱신
#! 학습률  너무 작으면 못 가고 너무 크면 튕김. 내가 정하는 하이퍼파라미터
#! 손실 곡선이 내려가고 있는가. 이거 하나면 됨
