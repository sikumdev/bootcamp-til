"""
title: 문자열 슬라이싱과 내장 함수
tags: [python, 1주차]
"""

#== 슬라이싱
#> 문자열[시작:끝:간격] — 위치는 "그 인덱스 앞에서 자른다"고 생각한다.

# --8<-- [start]
var4 = '1-2-3-4-5-6-7-8-9'
print(var4[::2])            # 123456789
#(1)> 시작·끝 비우면 전체, 간격 2 → 인덱스 0,2,4... 만 남아 '-' 가 빠짐

# 음수 인덱싱
filename = 'apple.jpg'
ext = '.png'
print(filename[:-4] + ext)  # apple.png
#(1)> 음수는 뒤에서부터. [:-4] = 뒤 4글자 뺀 나머지
# --8<-- [end]

#! 끝 인덱스는 포함 안 된다. 1:5 → 인덱스 1 앞 ~ 인덱스 5 앞.


#== 덧셈 · 곱셈
#> 덧셈은 병합, 곱셈은 복제.

# --8<-- [start]
a, b, c = "파", '이', '썬'
print((a + b + c) * 3)      # 파이썬파이썬파이썬
#(1)> 괄호 없으면 c 에만 곱해져서 '파이썬썬썬'
# --8<-- [end]


#== 내장 함수

# --8<-- [start]
txt = '정치 경제 사회 문화'

# len(문자열) → 길이
print(len(txt))                     # 11 (공백 포함)

# 문자열.split(기준) → 리스트
splitted = txt.split()              # ['정치', '경제', '사회', '문화']
#(1)> 인자 비우면 공백 기준 + 반환값이 문자열이 아니라 리스트[]

# '기준'.join(리스트) → 문자열
joined = '-'.join(splitted)         # 정치-경제-사회-문화

# 문자열.strip(제거할것) → 양쪽 끝만 제거
print('###---문화-####-'.strip('#-'))   # 문화
#(3)> '#-' 는 "# 또는 -" 라는 글자 목록. 덩어리가 아님
#(3)> lstrip() 왼쪽만 · rstrip() 오른쪽만

# 문자열.replace(old, new) → 전체 치환
print('###경제###사회###문화###'.replace('#', ''))   # 경제사회문화
# --8<-- [end]

#! 문자열.split() 은 리스트를 반환한다.
#! 문자열.strip() 은 양쪽 '끝'만, 문자열.replace(old, new) 는 문자열 '전체'.


#== 판별 함수 (반환값 bool)

# --8<-- [start]
txt = '정치.경제.사회.문화'
print('정치' in txt)        # True — 값 in 문자열

# 문자열.isalpha()  문자만 
# 문자열.isdigit()  숫자만
# 문자열.isalnum()  문자+숫자만
# 문자열.isupper()  대문자만
# 문자열.islower()  소문자만
# --8<-- [end]


#== 대소문자 변환

# --8<-- [start]
# 문자열.upper()  대문자로
# 문자열.lower()  소문자로
# --8<-- [end]


#== 연습문제

# --8<-- [start:practice]
# 1) '아이스카라멜마끼야또'
txt = '__아 이 스 카 라 멜 마 끼 야 또__'
print(txt.strip('_').replace(' ', ''))
#(1)> 양끝 _ 은 strip, 사이 공백은 replace

# 2) 'No meat,No life'
txt = 'No pain,No gain'
print(txt.replace(txt[3:7], 'meat').replace(txt[-4:], 'life'))
#(2)> 두 슬라이스 모두 원본 txt 기준으로 먼저 계산된 뒤 실행

# 3) 'SIMPLE IS THE BEST'
txt = "<<<<Simple is the best>>>>"
print(txt.strip('<>').upper())
#(3)> 새 문자열을 반환하니 점으로 이어 쓸 수 있음
# --8<-- [end:practice]

#! 문자열 메서드는 원본을 안 바꾸고 새 문자열을 반환한다 → 체이닝 가능.
