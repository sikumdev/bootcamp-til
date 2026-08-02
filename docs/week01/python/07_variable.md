---
title: 전역변수와 지역변수
date: 2026-08-02
tags: [python, function, 1주차]
---

# 전역변수와 지역변수

> 원본 코드: [`07_variable.py`](07_variable.py)

## 같은 이름 a 로 실험하기

함수 안에서 a 를 부르면 어느 a 가 나오는지 확인한다.

<div class="til-code" markdown>
```python hl_lines="3 4 5 7 8 10 11 12 13"
a = 5           # 전역변수

def fun1():
    a = 1       # 지역변수
    print(a)

def fun2():
    print(a)    # 전역변수

def fun3():
    global a
    a = 4
    print(a)

print(a)   # 5

fun1()     # 1
print(a)   # 5

fun2()     # 5
fun3()     # 4
print(a)   # 4  ← fun3 가 전역 a 를 바꿔놓음
```
<div class="til-note" data-til-line="5" hidden>함수 안에서 새로 만든 변수 a → 전역 변수 a 와 별개</div>
<div class="til-note" data-til-line="8" hidden>안에 변수 a 가 없으니 밖의 전역 변수 a 를 찾아 쓴다</div>
<div class="til-note" data-til-line="13" hidden>global 을 선언하면 밖의 전역 변수 a 를 직접 가리킨다<br>이 줄의 a = 4 는 새로 만드는 게 아니라 전역 변수 a 를 바꾸는 것</div>
</div>

!!! warning
    지역변수가 있으면 함수 안에서는 지역변수가 우선.  
    지역변수가 없으면 밖의 전역변수를 참조  
    값을 읽는 건 그냥 되지만, 바꾸려면 global 이 필요하다.
