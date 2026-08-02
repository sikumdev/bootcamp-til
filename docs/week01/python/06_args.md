---
title: 가변인자 — * 와 **
date: 2026-08-02
tags: [python, function, 1주차]
---

# 가변인자 — * 와 **

> 원본 코드: [`06_args.py`](06_args.py)

## 정의에서의 * — 모으기 (packing)

<div class="til-code" markdown>
```python hl_lines="7 9 11"
# def func(*a) — 넘어온 위치 인자를 전부 a 라는 튜플 하나에 담는다.
# 개수가 정해지지 않은 인자를 받을 때 쓴다.

def func(*a):
    print(a)

func()           # ()

func(1, 2, 3)    # (1, 2, 3)

func([1, 2, 3])  # ([1, 2, 3],)
```
<div class="til-note" data-til-line="7" hidden>아무것도 안 넘기면 빈 튜플</div>
<div class="til-note" data-til-line="9" hidden>값 3개가 튜플 하나로 묶여서 a 에 들어간다</div>
<div class="til-note" data-til-line="11" hidden>리스트 1개를 넘긴 것 → 원소가 하나뿐인 튜플</div>
</div>

!!! warning
    가변인자의 타입은 tuple.  
    func(1, 2, 3) 과 func([1, 2, 3]) 은 전혀 다르다. 앞은 인자 3개, 뒤는 인자 1개.

## 호출에서의 * — 펼치기 (unpacking)

같은 `*`` 인데 방향이 반대임 iterable 을 풀어서 각각의 인자로 넘긴다.

<div class="til-code" markdown>
```python hl_lines="4"
data = [1, 2, 3]

func(data)   # ([1, 2, 3],)  ← 리스트 통째로 1개
func(*data)  # (1, 2, 3)     ← 풀어서 3개
```
<div class="til-note" data-til-line="4" hidden>* 를 붙이면 func(1, 2, 3) 이라고 쓴 것과 같아진다</div>
</div>

!!! warning
    함수 정의의 `*` 는 모으기, 함수 호출의 `*` 는 펼치기.  
    `def func(*a)` — 여러 인자 → 튜플 하나로 패킹  
    `func(*data)` — iterable 하나 → 여러 인자를 언패킹  
    `def g(**kw)` — 여러 키워드 인자 → 딕셔너리 하나 패킹  
    `g(**d)` — 딕셔너리 하나 → 여러 키워드 인자 언패킹

## 리스트 안에서의 * — 역시 펼치기

<div class="til-code" markdown>
```python hl_lines="3 6"
a = [1, 2]
b = [3, 4]
print([*a, *b])   # [1, 2, 3, 4]

fruits = {'귤': 300, '사과': 1000}
print([*fruits.keys()])   # fruits.keys() → *('귤','사과) → ['귤', '사과']
```
<div class="til-note" data-til-line="3" hidden>리스트를 풀어서 새 리스트에 이어 붙인다</div>
<div class="til-note" data-til-line="6" hidden>dict_keys 같은 뷰 객체를 리스트로 만들 때도 쓴다 (list() 와 같은 결과)</div>
</div>

## ** — 키워드 인자 버전

`*` 가 위치 인자를 다룬다면, `**`` 는 키워드 인자를 딕셔너리로 다룬다.

<div class="til-code" markdown>
```python hl_lines="4"
def g(**kw):
    print(kw)

g(a=1, b=2)          # {'a': 1, 'b': 2}

g(**{'a': 1, 'b': 2})  # {'a': 1, 'b': 2}
```
<div class="til-note" data-til-line="4" hidden>정의의 ** → 키워드 인자들을 딕셔너리 하나로 모은다<br>호출의 ** → 딕셔너리를 풀어서 a=1, b=2 로 넘긴다</div>
</div>

## 실제로 쓰이는 곳 — print()

print 도 값을 몇 개든 받는다. 안쪽이 가변인자로 되어 있기 때문.

<div class="til-code" markdown>
```python hl_lines="1"
print(5, 4, 3, 2, 1, sep=',')   # 5,4,3,2,1

print()   # 빈 줄
```
<div class="til-note" data-til-line="1" hidden>값들은 가변인자로 모이고, sep·end 는 키워드 인자로 따로 받는다<br>sep 기본값은 공백, end 기본값은 줄바꿈(\n)</div>
</div>
