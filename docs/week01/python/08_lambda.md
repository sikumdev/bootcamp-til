---
title: lambda — 한 줄짜리 함수
date: 2026-08-02
tags: [python, function, 1주차]
---

# lambda — 한 줄짜리 함수

> 원본 코드: [`08_lambda.py`](08_lambda.py)

## 문법

<div class="til-code" markdown>
```python hl_lines="9"
# 함수명 = lambda 입력: 출력
# 한 줄로 끝나는 간단한 코드를 함수로 만들 때 쓴다. return 을 쓰지 않고, 식의 결과가 곧 반환값.

# def double(x):
#     return x * 2
double = lambda x: x * 2
print(double(5))   # 10

add = lambda x, y: x + y
```
<div class="til-note" data-til-line="9" hidden>입력이 여러 개면 콤마로 나열</div>
</div>

## 예제 — 확장자로 파일 거르기

<div class="til-code" markdown>
```python hl_lines="5"
filenames = ['readme.txt', 'car.jpg', 'airplane.jpg',
             'person.png', 'flower.jpg', 'bicycle.bmp', 'cat.jpg']
extension = 'jpg'

files_with_ext = lambda fnames, ext: [f for f in fnames if f[-3:] == ext]


print(files_with_ext(filenames, extension))
# ['car.jpg', 'airplane.jpg', 'flower.jpg', 'cat.jpg']
```
<div class="til-note" data-til-line="5" hidden>출력 자리에 리스트 컴프리헨션을 통째로 넣었다</div>
</div>

!!! warning
    lambda 는 값을 반환만 하고 출력은 안 한다. 확인하려면 print 로 감싸야 한다.
