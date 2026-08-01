---
title: 기본 내장 연산 함수
date: 2026-08-01
tags: [python, 1주차]
---

# 기본 내장 연산 함수

> 원본 코드: [`01_operator.py`](01_operator.py)

## 숫자 관련 내장 함수

파이썬이 기본으로 제공하는 연산 함수들.

<div class="til-code" markdown>
```python
abs(-5)           # 절대값 → 5
round(5.114, 2)   # 반올림 → 5.11
pow(5, 3)         # 제곱 → 125
min(1, 2, 3)      # 최소값 → 1
max(1, 2, 3)      # 최대값 → 3
```
</div>

## divmod() — 몫과 나머지를 한 번에

<div class="til-code" markdown>
```python hl_lines="1"
result = divmod(5, 3)
print(result)        # (1, 2)
print(type(result))  # <class 'tuple'>
```
<div class="til-note" data-til-line="1" hidden>반환값은 값 하나가 아니라 (몫, 나머지) 튜플</div>
</div>

!!! warning
    divmod()의 반환값은 튜플임을 잊지 말자.  
    값이 두 개 묶여서 오기 때문에 그냥 쓰면 (1, 2) 형태 그대로 나온다.

## 튜플 언패킹으로 나눠 받기

<div class="til-code" markdown>
```python hl_lines="1"
a, b = divmod(5, 2)

print(a)  # 2 → 몫
print(b)  # 1 → 나머지
```
<div class="til-note" data-til-line="1" hidden>튜플을 왼쪽 변수 개수에 맞춰 풀어서 받는 것 = 언패킹<br>변수 개수와 튜플 길이가 다르면 ValueError</div>
</div>

!!! warning
    튜플을 반환하는 함수는 a, b = ... 로 바로 나눠 받을 수 있다.
