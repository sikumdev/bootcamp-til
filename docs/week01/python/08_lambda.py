"""
title: lambda — 한 줄짜리 함수
tags: [python, 1주차]
"""

#== 문법
# 함수명 = lambda 입력: 출력
# 한 줄로 끝나는 간단한 코드를 함수로 만들 때 쓴다. return 을 쓰지 않고, 식의 결과가 곧 반환값.

# --8<-- [start:basic]
# 함수명 = lambda 입력: 출력
# 한 줄로 끝나는 간단한 코드를 함수로 만들 때 쓴다. return 을 쓰지 않고, 식의 결과가 곧 반환값.

# def double(x):
#     return x * 2
double = lambda x: x * 2
print(double(5))   # 10

add = lambda x, y: x + y
#(2)> 입력이 여러 개면 콤마로 나열
# --8<-- [end:basic]


#== 예제 — 확장자로 파일 거르기

# --8<-- [start:ex]
filenames = ['readme.txt', 'car.jpg', 'airplane.jpg',
             'person.png', 'flower.jpg', 'bicycle.bmp', 'cat.jpg']
extension = 'jpg'

files_with_ext = lambda fnames, ext: [f for f in fnames if f[-3:] == ext]
#(1)> 출력 자리에 리스트 컴프리헨션을 통째로 넣었다


print(files_with_ext(filenames, extension))
# ['car.jpg', 'airplane.jpg', 'flower.jpg', 'cat.jpg']
# --8<-- [end:ex]

#! lambda 는 값을 반환만 하고 출력은 안 한다. 확인하려면 print 로 감싸야 한다.
