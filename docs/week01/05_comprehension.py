"""
title: 컴프리헨션 — 자료구조 안에 제어문 넣기
tags: [python, comprehension, 1주차]
"""

#== 기본 형태
# --8<-- [start]
# [ 원소 for i in range(n) ] — 대괄호 안에 결과와 제어문을 한 줄로 쓴다.
# 맨 앞은 "리스트에 넣을 값", 뒤는 원래 for 문을 쓰던 순서 그대로.

nums = [i+1 for i in range(6)]
# nums = [1, 2, 3, 4, 5]
# --8<-- [end]


#== if 의 자리 — else 유무로 갈린다

# --8<-- [start:if]
# else 있음 → 맨 앞 (넣을 값을 고르는 것)
vars = ['x2' if i % 2 == 0 else 'oth' for i in range(1, 10)]
#(1)> 값 if 조건 else 값 — 항상 뭔가는 넣으니 개수가 안 줄어든다

# else 없음 → for 뒤 (넣을지 말지 거르는 것)
evens = [i for i in range(1, 10) if i % 2 == 0]
#(2)> 조건에 맞는 것만 남아서 개수가 줄어든다
# --8<-- [end:if]

#! else 가 있으면 앞, 없으면 for문 순서 그대로 쓰면 된다.
#! 앞의 if 는 "무엇을 넣을까"(선택), 뒤의 if 는 "넣을까 말까"(필터).


#== elif 는 else 뒤에 다시 삼항으로

# --8<-- [start:elif]
# for i in range(1, 100):
#     if i % 2 == 0:    vars.append('x2')
#     elif i % 3 == 0:  vars.append('x3')
#     else:             vars.append('oth')

vars = ['x2' if i % 2 == 0 else 'x3' if i % 3 == 0 else 'oth' for i in range(1, 100)]
#(1)> else 자리에 또 하나의 삼항식을 끼워 넣는 방식으로 앞 조건부터 순서대로 검사한다 (2의 배수가 먼저)
print(vars)
# --8<-- [end:elif]


#== 이중 for문 — 바깥 for문을 먼저 

# --8<-- [start:nested]
# for i in range(2):
#     for j in range(3):
#         num.append(i if i % 2 == 0 else j)

num = [i if i % 2 == 0 else j for i in range(2) for j in range(3)]
print(num)   # [0, 0, 0, 0, 1, 2]
#(1)> for 두 개를 쓰던 순서 그대로 왼쪽부터 나열한다
# --8<-- [end:nested]


#== for + 필터 if + for

# --8<-- [start:mix]
# for i in range(10):
#     if i % 2 == 0:
#         for j in range(5):
#             num.append(i * j)

nums = [i * j for i in range(10) if i % 2 == 0 for j in range(5)]
#(1)> else 가 없으니 if 가 뒤로 가서 원래 코드의 for → if → for 순서를 그대로 옮겨 적은 것 
print(nums)
# --8<-- [end:mix]


#== 딕셔너리 컴프리헨션

# --8<-- [start:dict]
# { 키: 값 for ... } — 제어문 순서는 리스트와 완전히 같고, 앞부분만 키:값 쌍이 된다.
# for idx, name in enumerate(movies):
#     info[name] = idx

movies = ['괴물', '인사이드아웃', '추격자', '어벤저스', '토이스토리']
info = {name: idx for idx, name in enumerate(movies)}
print(info)
# {'괴물': 0, '인사이드아웃': 1, ...}
# --8<-- [end:dict]
