---
title: 자료구조
date: 2026-08-02
tags: [python, 자료구조, 1주차]
---

# 자료구조

> 원본 코드: [`03_data_structure.py`](03_data_structure.py)

## 리스트 추가 (append · extend · insert)

<div class="til-code" markdown>
```python hl_lines="8 10"
# .append(값)      → 원소 1개를 맨 끝에 추가
# .extend(리스트)  → 여러 개를 맨 끝에 풀어서 추가
# .insert(i, 값)   → 원소 1개를 i번째 자리에 추가

nuts = ['아몬드', '호두', '땅콩', '마카다미아']

nuts.insert(2, '피스타치오')
nuts.extend(['캐슈넛', '피칸'])

nuts.append(['밤', '도토리'])

print(nuts)
# ['아몬드', '호두', '피스타치오', '땅콩', '마카다미아', '캐슈넛', '피칸', ['밤', '도토리']]
```
<div class="til-note" data-til-line="8" hidden>리스트를 풀어서 원소 2개가 각각 들어간다</div>
<div class="til-note" data-til-line="10" hidden>리스트 자체가 원소 1개로 통째로 들어간다</div>
</div>

!!! warning
    extend 는 리스트로 추가, append 는 리스트가 추가.

## 리스트 삭제 (remove · pop · del · clear)

<div class="til-code" markdown>
```python hl_lines="9"
# .remove(값)  → 값을 명시. 같은 값이 여러 개면 가장 앞 1개만
# .pop(i)      → 인덱스를 명시. 삭제가 아니라 뽑아서 반환. 비우면 -1
# del 리스트[i]      → 해당 원소 삭제. del 리스트 는 변수 자체를 삭제
# .clear()     → 안의 데이터만 비움

nuts = ['아몬드', '호두', '피스타치오', '땅콩', '마카다미아']

popped = nuts.pop(2)
print(popped)   # 피스타치오
```
<div class="til-note" data-til-line="9" hidden>pop 만 반환값이 있다. 꺼내서 쓸 값이면 pop, 그냥 지울 거면 remove/del</div>
</div>

## 정렬 (sort · sorted)

<div class="til-code" markdown>
```python hl_lines="11"
# 리스트.sort()   → 원본을 바꿈. 반환값 없음
# sorted(자료구조) → 원본 그대로. 정렬된 새 리스트를 반환
# reverse=True 로 역순, key= 로 정렬 기준 지정

fitness = ['스쿼트', '데드리프트', '벤치프레스', '바벨로우']

fit_sort = sorted(fitness)
print('origin:', fitness)   # 원본 그대로
print('sorted:', fit_sort)  # 가나다순

fit_sort2 = sorted(fitness, key=len)
print('sorted_by_len:', fit_sort2)
# ['스쿼트', '바벨로우', '데드리프트', '벤치프레스']
```
<div class="til-note" data-til-line="11" hidden>key 에 함수를 넘기면 그 결과를 기준으로 정렬<br>길이가 같으면 원래 순서가 유지된다</div>
</div>

!!! warning
    원본을 바꾸는 sort()/reverse() 와 새로 만드는 sorted()/reversed() 를 구분.  
    reversed() 는 리스트가 아니라 이터레이터를 반환한다. list() 로 감싸야 보인다.

## 조회 · 연산

<div class="til-code" markdown>
```python
# len(자료구조)        → 길이
# 자료구조.index(값)   → 값의 인덱스
# 자료구조.count(값)   → 값의 개수
# 값 in 자료구조       → 포함 여부 (bool)
# '기준'.join(자료구조) → 원소들을 하나의 문자열로

list_num = [1, 2, 3, 4, 5]
print(len(list_num))
print(list_num.index(3))
print(list_num.count(3))
print(3 in list_num)
print('1-2-3-4-5'.join(list_num))
```
</div>

## 덧셈 · 곱셈

덧셈은 병합, 곱셈은 원소 복제.

## 튜플

<div class="til-code" markdown>
```python
# ( ) 로 만들고 바뀌면 안 되는 값이나, 함수가 여러 값을 한 번에 돌려줄 때 쓴다 (divmod 처럼).
tup = (1, 2, 3)
```
</div>

## 세트

중복 불허 + 순서 없음. 리스트 중복 제거에 자주 쓴다 (list → set → list).

<div class="til-code" markdown>
```python hl_lines="12"
# add(값)      → 1개 추가 
# update(집합)  → 여러 개 추가
# remove(값)   → 없으면 KeyError
# discard(값)  → 없어도 에러 없음

comp = {'네이버', '카카오', '쿠팡', '배민'}

comp.add('당근')
comp.update({'라인', '토스'})

comp.remove('라인')
comp.discard('라인')
```
<div class="til-note" data-til-line="12" hidden>이미 지워진 뒤라 remove 였다면 KeyError, 있는지 확신 없으면 discard</div>
</div>

!!! warning
    순서가 없어서 인덱싱(comp[0])이 안 된다.

## 딕셔너리

<div class="til-code" markdown>
```python hl_lines="8 11"
# 키-값 쌍. 키 중복 불허.
# 딕셔너리[키] = 값 (수정과 추가 문법이 같다 (없는 키면 추가))

fruits = {'귤': 300, "오렌지": 900, '사과': 1000}

print(fruits.keys())    # dict_keys(['귤', '오렌지', '사과'])
print(fruits.values())  # dict_values([300, 900, 1000])
print(fruits.items())   # dict_items([('귤', 300), ('오렌지', 900), ('사과', 1000)])


print(fruits.popitem())  # ('사과', 1000)
print(fruits)            # {'귤': 300, '오렌지': 900}
```
<div class="til-note" data-til-line="8" hidden>리스트가 아니라 dict_keys 같은 뷰 객체로 인덱싱하려면 list() 로 감싸야 한다</div>
<div class="til-note" data-til-line="11" hidden>마지막 쌍을 꺼내서 반환. 원본에서는 사라진다</div>
</div>
