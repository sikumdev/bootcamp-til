---
title: 반복문 — for · enumerate · zip
date: 2026-08-02
tags: [python, loop, 1주차]
---

# 반복문 — for · enumerate · zip

> 원본 코드: [`04_loop.py`](04_loop.py)

## 기본 형태

<div class="til-code" markdown>
```python
for i in range(10):
    print(i)
```
</div>

## 인덱스도 같이 쓰기 — enumerate

<div class="til-code" markdown>
```python hl_lines="4 5"
#enumerate(iterable) → (인덱스, 원소) 를 짝지어 준다.
foods = ['볶음밥', '비빔밥', '돈가스']

for idx, food in enumerate(foods):
    print(idx + 1, food)
# 1 볶음밥 
# 2 비빔밥 
# 3 돈가스
```
<div class="til-note" data-til-line="5" hidden>꺼낼 때마다 (0, '볶음밥') 같은 튜플이 나오고, 그걸 idx·food 로 언패킹<br>enumerate(foods, 1) 처럼 시작 숫자를 지정해도 된다</div>
</div>

## 두 리스트 나란히 — zip

<div class="til-code" markdown>
```python hl_lines="5 6"
# zip(iterable1, iterable2) → 같은 자리끼리 묶어 준다.
foods = ['샤브샤브', '방어', '호떡']
prices = [20000, 90000, 2000]

for food, price in zip(foods, prices):
    print(f'{food}: {price}원')
```
<div class="til-note" data-til-line="6" hidden>앞에서부터 한 칸씩 짝을 지어 ('샤브샤브', 20000) 형태로 꺼낸다<br>만약 길이가 다르면 짧은 쪽에서 멈춘다 (남는 건 버려짐)</div>
</div>

## enumerate + zip 같이 쓰기

<div class="til-code" markdown>
```python hl_lines="4 5"
foods = ['볶음밥', '비빔밥', '돈가스']
drinks = ['아메리카노', '딸기라떼', '버블티']

for idx, (food, drink) in enumerate(zip(foods, drinks)):
    print(f'메뉴{idx + 1}: {food}-{drink}')
# 메뉴1: 볶음밥-아메리카노 ...
```
<div class="til-note" data-til-line="5" hidden>zip 이 만든 튜플을 enumerate 가 다시 감싸서 (0, ('볶음밥', '아메리카노'))<br>그래서 food, drink 를 괄호로 묶어야 한 겹 더 풀린다</div>
</div>

!!! warning
    괄호를 빼고 for idx, food, drink in ... 하면 값 개수가 안 맞아 에러.

## 딕셔너리 순회

<div class="til-code" markdown>
```python hl_lines="7 8 10 11"
# for k, v in 딕셔너리.items() — 키와 값을 한 번에 (가장 많이 씀)
# for k in 딕셔너리.keys() — 키만
# for v in 딕셔너리.values() — 값만

fruits = {'귤': '500원', '사과': '1000원', '배': '1500원', '복숭아': '2000원'}

for k, v in fruits.items():
    print(k, v)

for k in fruits:
    print(k)
```
<div class="til-note" data-til-line="8" hidden>items() 가 ('귤', '500원') 같은 튜플을 주니 k, v 로 언패킹된다</div>
<div class="til-note" data-til-line="11" hidden>딕셔너리를 그냥 돌리면 '키'만 나온다 (keys() 와 같음)</div>
</div>

!!! warning
    keys / values / items 는 리스트가 아니라 뷰 객체  → 인덱싱하려면 list() 로 감싸야 한다  
    .keys() → dict_keys([...]) · .values() → dict_values([...]) · .items() → dict_items([...])  
    keys() 는 키 순회·in 검사·집합 연산, values() 는 sum·max 같은 집계에서 자주 사용됨

## continue · break

continue — 아래 줄을 건너뛰고 다음 반복으로. break — 반복문 자체를 빠져나옴.

<div class="til-code" markdown>
```python hl_lines="2 3"
for price in [20000, 90000, 2000]:
    if price < 5000:
        continue
    print(price)
```
<div class="til-note" data-til-line="3" hidden>5000원 미만이면 print 를 건너뛰고 다음 값으로</div>
</div>
