---
title: 정규표현식 — RAG 문서 정리 (findall/sub + 전방·후방탐색)
date: 2026-09-07
tags: [regex]
---

# 정규표현식 — RAG 문서 정리 (findall/sub + 전방·후방탐색)

> 원본 코드: [`01_regexpression.py`](01_regexpression.py)

## 왜 정리하는가

RAG 전처리에서는 PDF 쪽수, OCR 로그, 문서 상태처럼 짧고 형식이 정해진 문자열을 자주 다듬게 됨.<br>`re.findall()` 로 값을 뽑고, `re.sub()` 로 잡음을 정리하고,<br>전방·후방탐색으로 "이 조건일 때만" 골라내는 흐름을 정리함.

<div class="til-code" markdown>
```python
import re

# re.findall(패턴, 문자열) → 패턴에 맞는 부분을 전부 리스트로 반환함
page_text = "PDF 3쪽, PDF 18쪽, PDF 29쪽을 문서로 만들었습니다."

page_labels = re.findall(r"PDF \d+쪽", page_text)   # \d+ = 숫자 1개 이상
print(page_labels)   # 결과: ['PDF 3쪽', 'PDF 18쪽', 'PDF 29쪽']
```
</div>

## PDF 쪽수 — 숫자만 뽑기

`PDF \d+쪽` 은 "PDF 3쪽" 전체를 가져옴. 숫자만 필요하면 한 번 더 findall 하거나,<br>후방·전방탐색으로 처음부터 숫자만 골라낼 수 있음. 두 방법을 비교함.

<div class="til-code" markdown>
```python
# page_labels -> ['PDF 3쪽', 'PDF 18쪽', 'PDF 29쪽']

# re.findall() 결과 리스트를 다시 findall 하는 2단계 방식.
page_numbers = re.findall(r"\d+", " ".join(page_labels))
print(page_numbers)   # 결과: ['3', '18', '29']

report_pages_text = "PDF 5쪽 | PDF 12쪽 | PDF 20쪽"

# 후방탐색 `(?<=PDF )` 과 전방탐색 `(?=쪽)` 을 한 번에 써서 숫자만 바로 뽑음. 
report_page_numbers = re.findall(r"(?<=PDF )\d+(?=쪽)", report_pages_text)
print(report_page_numbers)   # 결과: ['5', '12', '20']
```
</div>

## OCR 공백 정리 — 단순 버전

`\s+` 는 스페이스·탭·줄바꿈을 전부 공백 취급함. 짧은 문장 붙이기엔 편하지만<br>줄바꿈까지 한 칸으로 뭉개버려서 문단 구분이 사라진다는 걸 아래에서 확인함.

<div class="til-code" markdown>
```python
ocr_text = "첫 줄입니다.\n\n두 번째   줄입니다."

# \n\n(빈 줄, 문단 구분)까지 스페이스 한 칸으로 합쳐짐. 문단 정보가 사라짐.
normalized_ocr_text = re.sub(r"\s+", " ", ocr_text)
print(normalized_ocr_text)   # 결과: '첫 줄입니다. 두 번째 줄입니다.'
```
</div>

## OCR 공백 정리 — 문단 보존 버전

가로 공백(스페이스, 탭)과 세로 공백(줄바꿈)을 따로 처리함.<br>1단계: `[ \t]+` 로 가로 공백만 한 칸으로.<br>2단계: `\n{3,}` 로 세 줄 이상 이어진 줄바꿈만 두 줄로 줄임 → 문단 경계(빈 줄 한 개)는 그대로 남김.

<div class="til-code" markdown>
```python hl_lines="13"
noisy_ocr_text = (
    "제1조  계약 목적\n\n\n"
    "수급인은\t설계서에 따라 공사를 수행한다.\n\n"
    "제2조   대금 지급"
)

#[ \t]+ = 스페이스 또는 탭이 1개 이상 연속. 줄바꿈(\n)은 건드리지 않음.
step1 = re.sub(r"[ \t]+", " ", noisy_ocr_text)

# \n{3,} = 줄바꿈이 3개 이상 연속인 부분만 두 줄로 줄임. 문단 사이 빈 줄 1개는 유지됨.
cleaned_ocr_text = re.sub(r"\n{3,}", "\n\n", step1)

print(cleaned_ocr_text)

assert cleaned_ocr_text == (
    "제1조 계약 목적\n\n"
    "수급인은 설계서에 따라 공사를 수행한다.\n\n"
    "제2조 대금 지급"
)
```
<div class="til-note" data-til-line="13" hidden>결과:<br>제1조 계약 목적<br>수급인은 설계서에 따라 공사를 수행한다.<br>제2조 대금 지급</div>
</div>

!!! tip "문단 구조를 살릴지 말지로 고름"
    가로 공백/세로 공백을 나눠서 처리하니까  
    "단어 사이 중복 공백은 정리하되 문단 구분은 남기기" 가 가능해짐.  
    `\s+` 한 방으로 처리 vs `[ \t]+` + `\n{3,}` 2단계로 처리하는 건  
    **"문단 구조를 살릴지 말지"** 로 나눠서 골라 써야 함.

## 긍정형 전방탐색 `(?=...)`

현재 위치 뒤에 조건이 있을 때만 선택함. 조건 문자열 자체는 결과에 안 들어감.<br>결과에 뭘 남길지는 앞부분을 얼마나 넓게 잡느냐로 조절할 수 있음.

<div class="til-code" markdown>
```python
file_statuses = "문서-확정 문서-초안 문서-확정"
confirmed_pattern = r"문서(?=-확정)"

# "문서" 라는 이름만 결과에 남음. 몇 번째 문서인지는 구분이 안 됨.
confirmed_documents = re.findall(confirmed_pattern, file_statuses)
print(confirmed_documents)   # 결과: ['문서', '문서']

report_statuses = "보고서 101호 [승인] | 보고서 205호 [반려] | 보고서 312호 [승인]"

# 앞부분 패턴에 \d+ 를 넣어서 "보고서 101" 처럼 번호까지 결과에 포함시킴.
approved_reports = re.findall(r"보고서 \d+(?=호 \[승인\])", report_statuses)
print(approved_reports)   # 결과: ['보고서 101', '보고서 312']
```
</div>

!!! info "탐색 조건은 버려지고, 앞부분만 남음"
    `문서(?=-확정)` 은 이름만 남고, `보고서 \d+(?=호 \[승인\])` 은 번호까지 남음.  
    즉 탐색 조건은 "버려지는 부분"이고, 탐색 앞쪽은 "내가 결과로 남기고 싶은 만큼" 쓰면 됨.

## 부정형 전방탐색 `(?!...)`

현재 위치 뒤에 조건이 없을 때만 선택함. `OCR-무시` 처럼 제외할 상태를 걸러낼 때 씀.

<div class="til-code" markdown>
```python hl_lines="7"
ocr_log = "OCR-무시 OCR-확인 OCR-재시도"

# 앞부분을 "OCR" 까지만 써서, 어떤 상태인지 구분이 안 되고 개수만 셀 수 있음.
important_ocr_events = re.findall(r"OCR(?!-무시)", ocr_log)
print(important_ocr_events)   # 결과: ['OCR', 'OCR']

important_ocr_with_status = re.findall(r"OCR-(?!무시)\w+", ocr_log)
print(important_ocr_with_status)   # 결과: ['OCR-확인', 'OCR-재시도']
```
<div class="til-note" data-til-line="7" hidden>앞부분에 "-" 까지 넣고 탐색 뒤에 \w+ 를 붙여서 상태 이름까지 결과에 포함시킴.<br>\w+ 는 한글·영문·숫자·밑줄을 한 글자 이상 잡음. 상태 이름을 통째로 가져올 때 씀.</div>
</div>

!!! warning "같아 보이는데 결과가 다름"
    `OCR(?!-무시)` 랑 `OCR-(?!무시)\w+` 는 같은 걸 걸러내는 것 같아도 결과가 다름.  
    앞엣것은 "OCR-무시가 아닌 자리"만 확인하고 "OCR" 만 남기고,  
    뒤엣것은 "무시가 아닌 상태 이름 전체"를 남김.  
    **개수만 셀 건지, 어떤 상태인지 알아야 하는지에 따라 앞부분 패턴 범위를 다르게 잡아야 함.**

## 긍정형 후방탐색 `(?<=...)`

현재 위치 앞에 조건이 있을 때만 선택함. `(?<=PDF )\d+` 는 "PDF " 뒤 숫자만 반환함.

<div class="til-code" markdown>
```python
contract_numbers_text = "계약 18호 | 계약 31호 | 계약 44호"

# 후방탐색(앞 문맥 "계약 ")과 전방탐색(뒤 문맥 "호")을 같이 써서 숫자만 뽑음.
contract_numbers = re.findall(r"(?<=계약 )\d+(?=호)", contract_numbers_text)
print(contract_numbers)   # 결과: ['18', '31', '44']
```
</div>

## 부정형 후방탐색 `(?<!...)`

현재 위치 앞에 조건이 없을 때만 선택함. `재처리됨` 처럼 접두어가 붙은 건 제외할 때 씀.

<div class="til-code" markdown>
```python
processing_text = "재처리됨-재실행 처리됨-일반 처리됨-보류"

# "처리됨" 바로 앞이 "재" 인 경우만 제외함. "재처리됨-재실행" 은 통째로 빠짐.
normal_processing_statuses = re.findall(r"(?<!재)처리됨-\w+", processing_text)
print(normal_processing_statuses)   # 결과: ['처리됨-일반', '처리됨-보류']

approval_text = "재승인됨-재검토 승인됨-1차 승인됨-최종"

# 같은 구조를 "승인됨" 에도 그대로 적용함. 패턴 형태가 재사용 가능함을 확인함.
normal_approval_statuses = re.findall(r"(?<!재)승인됨-\w+", approval_text)
print(normal_approval_statuses)   # 결과: ['승인됨-1차', '승인됨-최종']
```
</div>

## 종합 — 확정 문서 번호만 뽑기

문서 상태 문자열에서 "확정" 상태인 문서 번호만 골라 metadata 후보로 만듦.<br>대괄호 `[`, `]` 는 정규식 특수문자라서 문자 그대로 찾으려면 `\[`, `\]` 로 이스케이프해야 함.

<div class="til-code" markdown>
```python hl_lines="2"
def extract_confirmed_document_numbers(text):
    pattern = r"(?<=문서 )\d+(?=번 \[확정\])"
    return re.findall(pattern, text)


document_status_text = (
    "문서 3번 [확정] | 문서 4번 [초안] | "
    "문서 9번 [확정] | 문서 12번 [보류]"
)

confirmed_document_numbers = extract_confirmed_document_numbers(document_status_text)
print(confirmed_document_numbers)   # 결과: ['3', '9']
assert confirmed_document_numbers == ["3", "9"]
```
<div class="til-note" data-til-line="2" hidden>\[ \] 는 이스케이프 안 하면 "문자 집합"으로 해석돼서 의도한 대괄호를 못 찾음.</div>
</div>

## 정리

!!! abstract "정리"
    `re.findall()` 은 값을 모아서 리스트로, `re.sub()` 은 문자열 일부를 바꿀 때 씀.  
    전방탐색 `(?=...)`/`(?!...)` 은 뒤 조건, 후방탐색 `(?<=...)`/`(?<!...)` 은 앞 조건을 확인함.  
    탐색 조건 자체는 결과에 안 남지만, **탐색 앞뒤로 내가 잡는 패턴 범위에 따라 "이름만 남길지, 값까지 남길지"가 달라짐**  
    OCR 공백 정리는 `\s+` 로 한 방에 할지, `[ \t]+` + `\n{3,}` 로 문단을 살릴지 텍스트 성격(문단이 있는 문서인지 아닌지) 보고 골라야 함.