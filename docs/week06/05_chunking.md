---
title: 청킹 
date: 2026-09-03
tags: [rag, chunking]
---

# 청킹 — 분할기 6종 비교와 chunk_overlap 의 실제 동작

> 원본 코드: [`05_chunking.py`](05_chunking.py)

## 청킹이 뭐고, 왜 크기를 고민하는지

청킹은 원본 문서를 검색 단위로 자르는 작업임. RAG 파이프라인에서 검색기가 반환하는 것은<br>문서 전체가 아니라 청크 하나이므로, 청크 경계가 곧 LLM 이 볼 수 있는 근거의 범위가 됨.

!!! info "청킹은 전처리가 아니라 설계 결정임"
    청킹을 "문서를 자르는 전처리" 정도로 봤는데, 실제로는 검색 단위를 정하는 설계 결정이었음.  
    벡터 검색은 `의미가 가까운 청크`를 찾는데, 그 청크 단위를 내가 직접 정해야 함.  
    그래서 인덱스와 달리 "무엇을 한 덩어리로 볼 것인가" 를 먼저 결정해야 함.

## 고정 길이 슬라이싱 — 문장 중간에서 잘림

라이브러리 없이 N글자씩 자르면 청크 길이는 정확히 예측되지만, 분할기가 문서 구조를<br>전혀 보지 않으므로 조항이나 문장이 경계에 걸림.

<div class="til-code" markdown>
```python
import numpy as np
import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import TokenTextSplitter

contract_text = '''제1조 공사 내용
수급인은 설계서에 따라 공사를 수행한다.

제2조 계약 보증금
계약 보증금은 계약 금액의 십 퍼센트로 한다. 보증서는 계약 체결일에 제출한다. 보증 기간은 준공일까지 유지한다.'''

fixed_size = 70
fixed_chunks = []

# 파이썬 슬라이싱은 끝 인덱스가 문자열 길이를 넘어도 에러를 내지 않고 남은 만큼만 반환함
for start in range(0, len(contract_text), fixed_size):
    fixed_chunks.append(contract_text[start:start + fixed_size])

print([len(chunk) for chunk in fixed_chunks])   # [70, 70, 15]

for index in range(len(fixed_chunks) - 1):
    left_tail = fixed_chunks[index][-25:]
    right_head = fixed_chunks[index + 1][:25]
    print(index + 1, repr(left_tail), "|", repr(right_head))
```
</div>

## CharacterTextSplitter — 구분자 하나만 쓰고, 더 작게 후퇴하지 않음

`CharacterTextSplitter` 는 `separator` 로 먼저 텍스트를 조각내고, 그 조각들을<br>`chunk_size` 안에서 다시 합침. 구분자가 하나뿐이라 조각 자체가 상한을 넘으면 그대로 둠.

<div class="til-code" markdown>
```python hl_lines="27"
import numpy as np
import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import CharacterTextSplitter
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_text_splitters import TokenTextSplitter

sample_text = '''앤트로픽이 Claude Opus 5를 출시했다. 새 모델은 에이전트 작업 효율을 높였다.

오픈AI가 GPT-5.6 제품군을 공개했다. 제품군은 Sol, Terra, Luna로 구성된다.

사카나 AI가 여러 모델을 조율하는 멀티 에이전트 시스템을 공개했다.'''

character_splitter = CharacterTextSplitter(
    separator="\n\n",
    chunk_size=100,
    chunk_overlap=0,
)

# 분할기가 문단 3개(49, 53, 38자)로 나눈 뒤 100자 안에서 다시 합침
character_chunks = character_splitter.split_text(sample_text)

# 49 다음에 53 을 붙이면 49+2+53=104 로 100 초과라서 새 청크를 시작하고, 53+2+38=93 은 들어가므로 합침
print([len(chunk) for chunk in character_chunks])   # [49, 93]

# 결과값
for separator in ["\n\n", ". ", " "]:
    splitter = CharacterTextSplitter(separator=separator, chunk_size=80, chunk_overlap=0)
    print(repr(separator), [len(chunk) for chunk in splitter.split_text(sample_text)])
```
<div class="til-note" data-til-line="27" hidden>'\n\n' → [49, 53, 38]<br>'. '   → [74, 68]<br>' '    → [80, 63]</div>
</div>

!!! note "chunk_size 는 상한임"
    `chunk_size` 는 상한이지 목표 길이가 아님. 분할기는 상한을 넘지 않는 선에서 최대한 붙임.

<div class="til-code" markdown>
```python hl_lines="5"
long_paragraph = "한문장이계속이어집니다" * 15   # 165자, 안에 "\n\n" 이 없음

single_separator = CharacterTextSplitter(separator="\n\n", chunk_size=40, chunk_overlap=0)
long_chunks = single_separator.split_text(long_paragraph)
print(len(long_chunks), len(long_chunks[0]))   # 1 165
```
<div class="til-note" data-til-line="5" hidden>chunk_size 가 40 인데 165자 청크가 그대로 나옴</div>
</div>

!!! warning "상한을 넘겨도 그냥 내보냄"
    여기서 헷갈렸던 것 → `chunk_size` 는 `보장이 아니라 요청`임.  
    `CharacterTextSplitter` 는 구분자가 하나라서, 그 구분자로 못 자르는 덩어리는 상한을 넘겨도 그냥 내보냄.

## keep_separator — 구분자를 앞에 붙일지 뒤에 붙일지

`CharacterTextSplitter` 는 `is_separator_regex=True` 로 정규식 구분자를 받을 수 있음.<br>이때 잘라낸 구분자를 어디에 붙일지는 `keep_separator` 가 정함.

<div class="til-code" markdown>
```python hl_lines="2 4"
sentence_text = "첫 문장입니다. 두 번째 문장입니다! 질문이 있습니까? 마지막 문장입니다."
sentence_regex = r"(?<=[.!?。！？])\s+"

# 결과값
for keep in ["end", "start", True, False]:
    splitter = CharacterTextSplitter(
        separator=sentence_regex,
        is_separator_regex=True,
        keep_separator=keep,
        chunk_size=30,
        chunk_overlap=0,
    )
    print(repr(keep), splitter.split_text(sentence_text))
```
<div class="til-note" data-til-line="2" hidden>(?<=...) 는 문장부호 "바로 뒤 위치" 만 확인하고 그 문자는 소비하지 않음. \s+ 가 실제 구분자임</div>
<div class="til-note" data-til-line="4" hidden>'end'   → ['첫 문장입니다. 두 번째 문장입니다!', '질문이 있습니까? 마지막 문장입니다.']<br>'start' → ['첫 문장입니다. 두 번째 문장입니다! 질문이 있습니까?', '마지막 문장입니다.']<br>True    → 'start' 와 완전히 같음<br>False   → ['첫 문장입니다.두 번째 문장입니다!질문이 있습니까?', '마지막 문장입니다.']</div>
</div>

!!! info "keep_separator 는 청크 개수까지 바꿈"
    `end` 는 분할기가 구분자(\s+)를 `앞 조각 끝에` 붙이고, `start`/`True` 는 **뒤 조각 앞에** 붙이고,  
    `False` 는 버림.  
    결과가 갈리는 이유는 1차 분할이 아니라 **다시 합칠 때**임.  
    `False` 는 공백을 버려서 조각들이 짧아지고, 그래서 30자 안에 3개까지 들어감.  
    `end` 는 공백이 앞 조각에 남아 조각이 길어져서 2개까지만 들어감.  
    즉 `keep_separator` 는 겉모양만 바꾸는 옵션이 아니라 **청크 개수까지 바꿈.**

<div class="til-code" markdown>
```python hl_lines="15"
regex_splitter = CharacterTextSplitter(
    separator=r"(?<=[.!?。！？])\s+",
    is_separator_regex=True,
    keep_separator="end",
    chunk_size=30,
    chunk_overlap=0,
)

# ['버전은 3.14입니다.', '주소는 example.com 입니다. 다음 문장입니다.']
print(regex_splitter.split_text("버전은 3.14입니다. 주소는 example.com 입니다. 다음 문장입니다."))

# ['A.I. 모델을 사용합니다. 다음 문장입니다.']
print(regex_splitter.split_text("A.I. 모델을 사용합니다. 다음 문장입니다."))

# ['첫 문장입니다.다음 문장입니다.']
print(regex_splitter.split_text("첫 문장입니다.다음 문장입니다."))
```
<div class="til-note" data-til-line="15" hidden>문장부호 뒤에 공백이 없으면 \s+ 가 매칭되지 않아 분할기가 경계를 못 찾음</div>
</div>

!!! example "소수점과 약어 사례"
    소수점 사례는 `3.14입니다.` 뒤 공백에서 잘려서 오히려 맞게 나왔고,  
    약어 `A.I.` 는 `A.I. 모델을` 의 공백에서 잘렸어야 하는데 전체가 30자 안이라 한 청크로 합쳐짐.  
    정규식 분할기는 **문장 분석기가 아니라 규칙 매칭기**라서, 문서 형식이 일정할 때만 써야 함.

## RecursiveCharacterTextSplitter — 큰 구분자부터 순서대로 후퇴

구분자 목록을 앞에서부터 시도하다가, 조각이 `chunk_size` 를 넘으면 다음(더 작은) 구분자로<br>내려감. 마지막 `""` 까지 가면 글자 단위로 자름.

<div class="til-code" markdown>
```python hl_lines="3"
print(RecursiveCharacterTextSplitter()._separators)   # ['\n\n', '\n', ' ', '']

# 결과 값
for size in [40, 60, 100]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=0)
    chunks = splitter.split_text(sample_text)
    print(size, len(chunks), [len(chunk) for chunk in chunks])
```
<div class="til-note" data-til-line="3" hidden>40  → 5개 [40, 8, 34, 18, 38]<br>60  → 3개 [49, 53, 38]<br>100 → 2개 [49, 93]</div>
</div>

!!! info "기본 구분자에 문장부호가 없음"
    기본 구분자에 `.` `?` `!` 가 아예 없어서, 분할기는 `문단 → 줄 → 공백 → 글자` 만 봄.  
    `chunk_size=40` 결과의 `[40, 8, ...]` 처럼 8자짜리 꼬리 청크가 생기는 게 그 증거임.  
    한국어 문장 경계를 쓰려면 내가 구분자 목록에 직접 넣어야 함.

<div class="til-code" markdown>
```python hl_lines="3"
text = "첫 문장이다. 두 번째 문장이다. 세 번째 문장이다."

# 결과 값
for keep in [True, "end"]:
    splitter = RecursiveCharacterTextSplitter(
        separators=[". ", ""],
        chunk_size=15,
        chunk_overlap=0,
        keep_separator=keep,
    )
    print(repr(keep), splitter.split_text(text))
```
<div class="til-note" data-til-line="3" hidden>True  → ['첫 문장이다', '. 두 번째 문장이다', '. 세 번째 문장이다.']<br>'end' → ['첫 문장이다.', '두 번째 문장이다.', '세 번째 문장이다.']</div>
</div>

!!! warning "분할기마다 keep_separator 기본값이 다름"
    새로 알게 된 것 → `keep_separator` 기본값이 두 분할기에서 다름.  
    `CharacterTextSplitter` 는 `False`, `RecursiveCharacterTextSplitter` 는 `True`.  
    Recursive 는 기본이 `True`(= `start`) 라서 **마침표가 다음 청크 맨 앞에 붙음.**  
    한국어 구분자를 쓸 땐 분할기에 `keep_separator="end"` 를 명시해야 문장이 마침표로 끝남.

<div class="til-code" markdown>
```python hl_lines="12"
poor_text = (
    "모델명=alpha-x3;라이선스=상업사용가능;월예산=300만원;"
    "검색범위=계약서와정책문서;평가기준=근거일치율과응답정확도;"
    "담당부서=AI전략팀;갱신주기=월1회"
)

default_case = RecursiveCharacterTextSplitter(
        separators=["\n\n", "\n", ". ", " ", ""], 
        chunk_size=45, 
        chunk_overlap=0)

# ; 가 구분자 목록에 없고 공백·줄바꿈도 없어서 마지막 기준인 "" 까지 후퇴 → "계약서와정책문서" 가 쪼개짐
print(default_case.split_text(poor_text))

format_aware = RecursiveCharacterTextSplitter(
                        separators=[";", "=", "\n\n", "\n", ". ", " ", ""],
                        chunk_size=45, 
                        chunk_overlap=0, 
                        keep_separator="end")

print([len(chunk) for chunk in format_aware.split_text(poor_text)])   # [35, 42, 8]
```
<div class="til-note" data-til-line="12" hidden>['모델명=alpha-x3;...;검색범위=계약서와정', '책문서;평가기준=...;갱신주기=월1회']</div>
</div>

!!! note "Recursive 도 조건부로 좋음"
    Recursive 가 항상 좋은 게 아니라, **내가 준 구분자 목록이 문서 형식과 맞을 때만** 좋은 거였음.  
    형식이 안 맞으면 결국 글자 단위까지 내려가서 고정 길이 슬라이싱과 같아짐.

## TokenTextSplitter — 토큰 위치에서 자르기

`tiktoken` 은 문자열을 토큰 ID 목록으로 바꾸는 로컬 라이브러리임.<br>`TokenTextSplitter` 는 텍스트를 토큰화한 뒤 `chunk_size` 개씩 잘라서 다시 문자열로 복원함.

<div class="til-code" markdown>
```python hl_lines="1 4"
# 결과 값
for name in ["gpt2", "cl100k_base"]:
    encoding = tiktoken.get_encoding(name)
    print(name, len(encoding.encode("안녕하세요.")))
```
<div class="til-note" data-til-line="1" hidden>gpt2        → 15<br>cl100k_base → 6</div>
<div class="til-note" data-til-line="4" hidden>분할기가 아니라 encoding 이 직접 토큰 수를 셈. 규칙이 다르면 결과가 2배 넘게 차이남</div>
</div>

!!! info "cl100k_base 는 모델이 아님"
    `cl100k_base` 는 `토큰 어휘와 병합 규칙의 이름`이고, 모델이 아님. API 호출도 안 함.  
    `안녕하세요.` 의 gpt2 토큰 ID 는  
    `[168, 243, 230, 167, 227, 243, 47991, 246, 168, 226, 116, 168, 248, 242, 13]` 임.  
    한글 한 글자가 3바이트라서 gpt2 에선 글자당 토큰이 여러 개로 쪼개짐.

<div class="til-code" markdown>
```python hl_lines="1 20"
# chunk 결과 값
for name in ["gpt2", "cl100k_base"]:
    splitter = TokenTextSplitter(
        encoding_name=name, 
        chunk_size=35, 
        chunk_overlap=0)
    
    chunks = splitter.split_text(sample_text)

    # 여기 찍히는 숫자는 토큰 수가 아니라 복원된 문자열의 "글자 수" 임
    print(name, [len(chunk) for chunk in chunks])

for name in ["gpt2", "cl100k_base"]:
    splitter = TokenTextSplitter(
        encoding_name=name, 
        chunk_size=20, 
        chunk_overlap=0)
    
    broken = sum(chunk.count("\ufffd") for chunk in splitter.split_text(sample_text))
    print(name, broken)  # gpt2 → 13,  cl100k_base → 3
```
<div class="til-note" data-til-line="1" hidden>gpt2        → [28, 17, 24, 31, 19, 17, 10]<br>cl100k_base → [40, 32, 50, 22]</div>
<div class="til-note" data-til-line="20" hidden>\ufffd 는 대체 문자. 한 글자를 이루는 바이트 중간에서 잘리면 복원이 깨짐</div>
</div>

!!! note "토큰 수 다시 세기 · model_name 매핑"
    토큰 상한을 확인하려면 `len(encoding.encode(chunk))` 로 다시 세야 함.  
    대체 문자 개수가 gpt2 13개 vs cl100k 3개인 이유 → gpt2 는 한글 한 글자를 더 잘게 쪼개서  
    토큰 경계가 글자 중간에 놓일 확률이 훨씬 높음.  
    `TokenTextSplitter` 에는 `encoding_name` 말고 `model_name` 도 줄 수 있음.  
    `model_name` 을 주면 라이브러리가 그 모델에 연결된 인코딩을 대신 찾아줌.  
    `tiktoken.model.encoding_name_for_model()` 로 매핑을 확인하면 아래 표와 같음.  

    | model_name | 연결되는 encoding |  
    |---|---|  
    | `gpt-4o-mini` | `o200k_base` |  
    | `gpt-4` | `cl100k_base` |  
    | `gpt-3.5-turbo` | `cl100k_base` |  
    | `text-embedding-3-small` | `cl100k_base` |

## 직접 토큰 분할 vs token-aware Recursive

`RecursiveCharacterTextSplitter.from_tiktoken_encoder()` 는 구분자로 먼저 나누되<br>길이를 `tiktoken` 으로 잼. 상한은 토큰 기준으로 지키면서 경계는 구조를 따름.

<div class="til-code" markdown>
```python hl_lines="16"
encoding = tiktoken.get_encoding("cl100k_base")
TOKEN_LIMIT = 20

direct = TokenTextSplitter(
    encoding_name="cl100k_base", 
    chunk_size=TOKEN_LIMIT, 
    chunk_overlap=0)

aware = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name="cl100k_base",
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=TOKEN_LIMIT,
    chunk_overlap=0,
    keep_separator="end",
)
# 결과 값
for label, splitter in [("direct", direct), ("token_aware", aware)]:
    chunks = splitter.split_text(sample_text)
    counts = [len(encoding.encode(chunk)) for chunk in chunks]
    print(label, len(chunks), max(counts), sum(c.count("\ufffd") for c in chunks))
```
<div class="til-note" data-til-line="16" hidden>direct      → 7개, 최대 20토큰, 대체문자 3<br>token_aware → 10개, 최대 18토큰, 대체문자 0</div>
</div>

!!! example "트레이드오프가 숫자로 보임"
    두 방식의 트레이드오프가 숫자로 보임.  
    `direct` 는 상한 20을 꽉 채우지만 글자가 깨짐. `token_aware` 는 안 깨지는 대신  
    구분자 위치에서 끊느라 청크가 더 잘게 나뉘고(7 → 10개) 상한을 다 못 씀(최대 18).  
    분할기가 `토큰 상한을 정확히 맞추는 것`과 `글자·문장을 보존하는 것` 중 무엇을 우선시 해야할지는 상황에 따라 달라짐

## MarkdownHeaderTextSplitter — 제목을 metadata 로 옮김

지정한 Markdown 제목을 기준으로 `Document` 를 만들고, 제목 텍스트를 `metadata` 에 넣음.<br>길이 제한은 하지 않으므로 Recursive 를 뒤에 이어 붙여야 함.

<div class="til-code" markdown>
```python
markdown_text = """# 기업 소식
앤트로픽이 Claude Opus 5를 출시했다.

## 비용
Claude Opus 5는 이전 최고 성능 모델에 가까운 추론 성능을 제공하고 사용 비용을 낮추며 작업 시간을 줄일 수 있다. 실제 비용과 성능은 작업 유형과 입력 길이, 사용하는 도구에 따라 달라지므로 대표 질문으로 품질과 비용을 함께 확인해야 한다.

# 연구 소식
사카나 AI가 멀티 에이전트 시스템을 공개했다."""

header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "H1"), ("##", "H2")])

header_chunks = header_splitter.split_text(markdown_text)

for chunk in header_chunks:
    print(chunk.metadata, len(chunk.page_content))

# {'H1': '기업 소식'} 26
# {'H1': '기업 소식', 'H2': '비용'} 141
# {'H1': '연구 소식'} 26

section_splitter = RecursiveCharacterTextSplitter(chunk_size=45, chunk_overlap=10)

# split_documents 는 원본 Document 의 metadata 를 그대로 복사해서 넘김
section_chunks = section_splitter.split_documents(header_chunks)

for chunk in section_chunks:
    print(len(chunk.page_content), chunk.metadata)

# 26 {'H1': '기업 소식'}
# 43 {'H1': '기업 소식', 'H2': '비용'}   ← 141자 구간이 4개로 쪼개지고
# 42 {'H1': '기업 소식', 'H2': '비용'}   ← 4개 모두 H2 를 유지함
# 42 {'H1': '기업 소식', 'H2': '비용'}
# 36 {'H1': '기업 소식', 'H2': '비용'}
# 26 {'H1': '연구 소식'}
```
</div>

!!! question "왜 여기만 Document 를 돌려주나"
    여기서 헷갈렸던 것 → `MarkdownHeaderTextSplitter`는  `.split_text`로 분할 시  
    다른 분할기와 다르게 반환 값이 list[str] 이 아닌 list[Document]가 나옴  
    애초에 이 분할기의 목적이 `제목을 metadata 로 옮기는 것`이라, 문자열을 돌려주면  
    그 정보를 담을 자리가 없어서 `Document` 로 반환할 수밖에 없음.  
    `split_text` 와 `split_documents` 는 이름이 **입력 타입**을 가리킴(위 예외만 빼고).  
    `split_text(str)` → `list[str]`, metadata 없음.  
    `split_documents(list[Document])` → `list[Document]`, 원본 metadata 를 복사해서 넘김.  
    굳이 문자열로 넘기려면 내가 `[c.page_content for c in header_chunks]` 로 꺼내야 하는데,  
    그러면 `H1`·`H2` 가 통째로 날아감. 구조 분할을 먼저 한 이유가 사라지므로 하면 안 됨.

!!! tip "구조 분할을 먼저 하는 이유"
    {'H1': '기업 소식', 'H2': '비용'} 141자 구간을 Recursive 가 4조각으로 나눴는데  
    `4조각 전부가 `{'H1': '기업 소식', 'H2': '비용'}` 를 그대로 들고 있었음.`  
    그래서 나중에 검색으로 3번째 조각을 가져와도 "이건 기업 소식 -비용 절의 내용" 이라는 걸 알 수 있음.  
    이게 구조 분할을 먼저 하는 이유임. 순서를 반대로 해서 Recursive 를 먼저 돌리면  
    제목 줄이 어느 청크에 붙었느냐에 따라 소속 정보가 사라짐.  
    `strip_headers=False` 를 주면 분할기가 제목 줄을 `metadata` 뿐 아니라  
    `page_content` 에도 남김. 청크만 봐도 어느 절인지 읽히게 하고 싶을 때 씀.

## 의미 기반 분할 — 유사도가 떨어지는 지점을 경계로

문장들을 임베딩 벡터로 바꾸고, 인접한 두 벡터의 코사인 유사도가 낮아지는 곳을 주제 경계로 봄.

<div class="til-code" markdown>
```python
semantic_sentences = [
    "고양이는 조용한 곳에서 잠을 잔다.",
    "고양이는 장난감을 쫓아다닌다.",
    "고혈압은 정기적인 관리가 필요하다.",
    "저염식은 혈압 관리에 도움이 된다.",
]

# 위의 semantic_sentences를 벡터 값으로 나타낸 값 (임의의 값으로 지정해둠)
semantic_vectors = np.array([[0.98, 0.08], [0.93, 0.12], [0.10, 0.95], [0.06, 0.99]])

def cosine_similarity(left_vector, right_vector):
    numerator = np.dot(left_vector, right_vector) # 내적
    denominator = np.linalg.norm(left_vector) * np.linalg.norm(right_vector)
    return float(numerator / denominator)


# semantic_sentences의 [0],[1]의 유사도 / [1],[2]의 유사도 / [2],[3]의 유사도  
adjacent = [cosine_similarity(semantic_vectors[i], semantic_vectors[i + 1])
            for i in range(len(semantic_vectors) - 1)]

print([round(score, 3) for score in adjacent])   # [0.999, 0.231, 0.999]

# argmin 은 최소값이 있는 위치(1)를 주고, 경계는 "그 다음 문장부터" 이므로 +1 을 함
boundary = int(np.argmin(adjacent)) + 1

print(boundary)   # 2
```
</div>

!!! note "np.argmin 의 축"
    `np.argmin` 은 축을 안 주면 `배열 전체를 1차원으로 편 뒤` 최소값 인덱스를 반환함.

<div class="til-code" markdown>
```python
# "인접 문장쌍 5개의 유사도 점수" 목록임
similarity_scores = [0.93, 0.71, 0.54, 0.76, 0.90]

fixed_threshold = 0.60  # 임계값
mean_score = float(np.mean(similarity_scores))
print(round(mean_score, 3))   # 0.768

print("lowest         ", [int(np.argmin(similarity_scores)) + 1])
print("fixed_threshold", [i + 1 for i, s in enumerate(similarity_scores) if s < fixed_threshold])
print("below_mean     ", [i + 1 for i, s in enumerate(similarity_scores) if s < mean_score])

# lowest          → [3]
# fixed_threshold → [3]
# below_mean      → [2, 3, 4]
```
</div>

## PyPDFLoader — PDF 를 페이지 단위 Document 로 읽기

분할기에 넣기 전에 로더가 PDF 를 페이지별 `Document` 리스트로 바꿈.<br>각 `Document` 에는 `page_content` 와 `metadata` 가 있음.

<div class="til-code" markdown>
```python
from langchain_community.document_loaders import PyPDFLoader
pages = PyPDFLoader("test.pdf").load()

print(len(pages))                            # 3        페이지 수
print(len(pages[0].page_content))            # 584      첫 페이지 글자 수
print(pages[0].metadata["page"] + 1)         # 1        page 는 0부터라 화면 표시할 땐 +1
print(sorted(pages[0].metadata))
# ['author', 'creationdate', 'creator', 'keywords', 'moddate', 'page',
#  'page_label', 'producer', 'source', 'subject', 'title', 'total_pages', 'trapped']

empty = [p.metadata["page"] + 1 for p in pages if not p.page_content.strip()]
print(empty)                                 # []       빈 페이지 없음
```
</div>

!!! warning "page 는 0부터, page_label 은 문자열"
    `metadata["page"]` 가 `0부터`라는 걸 놓치면 안 됨. 검색 결과에 쪽수를 찍을 땐 항상 +1.  
    `page_label` 은 문자열 `'1'` 이고 `page` 는 정수 `0` 임. 둘이 다른 값이라 헷갈리기 쉬움.  
    빈 페이지 검사를 따로 하는 이유 → PDF 가 스캔 이미지면 `page_content` 가 빈 문자열임.  
    이 경우 분할기에 넣어도 청크가 안 나오므로, 로더 단계에서 OCR 이 필요한지 먼저 판단해야 함.

## 같은 PDF·같은 토큰 조건에서 세 분할기 비교

3쪽짜리 예금 상품설명서(584 / 577 / 569자)에 `cl100k_base` 300토큰 상한,<br>30토큰 겹침을 똑같이 주고 결과를 비교함.

<div class="til-code" markdown>
```python
from langchain_community.document_loaders import PyPDFLoader

pages = PyPDFLoader("test.pdf").load()   # 페이지별 Document 리스트, metadata["page"] 는 0부터

encoding = tiktoken.get_encoding("cl100k_base")

strategies = {
    "Character": CharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base", 
        separator="\n\n",
        chunk_size=300, 
        chunk_overlap=30),
    "Recursive": RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
        chunk_size=300, 
        chunk_overlap=30),
    "Token": TokenTextSplitter(
        encoding_name="cl100k_base", 
        chunk_size=300, 
        chunk_overlap=30),
}

for name, splitter in strategies.items():
    documents = splitter.split_documents(pages)
    token_lengths = [len(encoding.encode(d.page_content)) for d in documents]
    print(name, len(documents), max(token_lengths),
          max(len(d.page_content) for d in documents),
          sum(d.page_content.count("\ufffd") for d in documents))
    
# Character → 3개, 최대 548토큰, 584자, 대체문자 0
# Recursive → 7개, 최대 291토큰, 310자, 대체문자 0
# Token     → 6개, 최대 300토큰, 337자, 대체문자 1
```
</div>

!!! abstract "분할기 3종 결과"
    | 분할기 | 청크 수 | 최대 토큰 | 상한(300) 지킴 | 글자 깨짐 |  
    |---|---|---|---|---|  
    | Character | 3 | 548 | 아니오 | 없음 |  
    | Recursive | 7 | 291 | 예 | 없음 |  
    | Token | 6 | 300 | 예 | 1개 |  

    3장짜리 test.pdf를 PyPDFLoader 통해 load()하면 chunk가 3개인데  
    Character 가 청크를 나누지 않고 그대로 3개만 내뱉은 이유를 찾음.  
    이 PDF 본문에는 빈 줄(`\n\n`)이 하나도 없고 줄바꿈(`\n`)만 있음.  
    그래서 분할기가 페이지 하나를 통째로 조각 1개로 보고 그대로 내보냄 → 청크 = 페이지.  
    548토큰짜리 청크가 나온 게 그 결과임. `문서에 그 구분자가 실제로 있는지 먼저 봐야 함.`  
    Token 만 대체 문자가 1개 나옴. 토큰 ID 를 300개씩 기계적으로 자르니까  
    한글 한 글자를 이루는 바이트 중간에서 끊긴 것임.

## add_start_index — 청크가 원문 어디서 왔는지

`add_start_index=True` 를 주면 분할기가 `Document.metadata` 에 `start_index` 를 넣음.<br>이 값은 `그 페이지 텍스트 안에서의 문자 위치`임(문서 전체 기준이 아님).

<div class="til-code" markdown>
```python hl_lines="9"
indexed = RecursiveCharacterTextSplitter(
            chunk_size=200, 
            chunk_overlap=40, 
            add_start_index=True)

indexed_documents = indexed.split_documents(pages)

for document in indexed_documents[:6]:
    print(document.metadata["page"] + 1, document.metadata["start_index"])

matched = all(
    pages[d.metadata["page"]].page_content[
        d.metadata["start_index"]:d.metadata["start_index"] + len(d.page_content)
    ] == d.page_content
    for d in indexed_documents
)

# 원문에서 그 위치를 잘라오면 청크와 정확히 일치함 → 인용 위치 추적에 쓸 수 있음
print(matched)   # True
```
<div class="til-note" data-til-line="9" hidden>페이지가 바뀌면 start_index 가 0 으로 리셋됨 → 페이지 기준 오프셋임<br>1 0 / 1 132 / 1 260 / 1 438 / 2 0 / 2 179</div>
</div>

!!! info "인용 위치 추적에 쓸 수 있음"
    전 청크에 대해 `matched` 가 `True` 였음.  
    답변에 "몇 쪽 몇 번째 글자" 같은 출처를 붙이려면 이 값이 필요함.  
    단, PDF 추출기나 공백 정규화가 바뀌면 문자 위치가 통째로 달라지므로  
    로더 버전과 원본 파일을 같이 고정해둬야 함.

## 청크 크기 100 / 250 / 500 비교

같은 PDF, 같은 Recursive, 겹침은 각 크기의 18%(18 / 45 / 90)로 두고 크기만 바꿈.

<div class="til-code" markdown>
```python
documents_by_size = {}

for size in [100, 250, 500]:
    overlap = int(size * 0.18)
    splitter = RecursiveCharacterTextSplitter(chunk_size=size, chunk_overlap=overlap)
    documents = splitter.split_documents(pages)
    documents_by_size[size] = documents
    

    lengths = [len(d.page_content) for d in documents]
    print(size, overlap, len(lengths), min(lengths), max(lengths),
          round(sum(lengths) / len(lengths), 1))
    
# 100 18 → 24개, 50~98자, 평균 74.0
# 250 45 →  9개, 115~243자, 평균 198.1
# 500 90 →  6개, 146~489자, 평균 321.5
```
</div>

!!! info "상한 = 평균이 아님 · 검색 해상도"
    평균 길이가 상한보다 한참 낮음(250 상한에 평균 198). 분할기가 상한을 채우는 게 아니라  
    `구분자 위치에서 끊고 남은 만큼만` 담기 때문임. 상한 = 평균이 아님.  
    페이지당 청크 밀도로 보면 100자 → 8개, 250자 → 3개, 500자 → 2개임.  
    이게 "검색 해상도" 임. 잘게 자를수록 검색 후보가 많아지지만 청크 하나가 담는 근거는 줄어듦.

## chunk_overlap 은 글자 단위가 아니라 조각 단위임

`chunk_overlap=50` 을 줘도 실제 겹침이 0자가 될 수 있음.

<div class="til-code" markdown>
```python hl_lines="16 19"
# 줄 하나가 정확히 30자인 텍스트를 만듦

splits = [
  "A"*30,        # 길이 30  (맨 앞 조각이라 \n 없음)
  "\n" + "B"*30, # 길이 31  (\n + B)
  "\n" + "C"*30, # 길이 31
  "\n" + "D"*30, # 길이 31
]

병합 과정 (chunk_size=70)
A(30) + B(31) = 61 ≤ 70 → 합쳐서 첫 청크 확정: "A~B" (61자)
여기에 C(31)를 더하면 92 > 70 → 더 못 넣음 → 청크1 확정, 이제 겹침용으로 얼마나 남길지 결정

lines = ["A" * 30, "B" * 30, "C" * 30, "D" * 30]

# text
text = "\n".join(lines)

# sperator 기준은 문단이 없으니 "\n" 기준으로 먼저 분할됨

for overlap in [20, 30, 31, 40]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=70, chunk_overlap=overlap)
    chunks = splitter.split_text(text)
    print(overlap, len(chunks), [c[:1] + "~" + c[-1:] for c in chunks])

# 20 → 2개 ['A~B', 'C~D']       겹침 없음
# 30 → 2개 ['A~B', 'C~D']       겹침 없음
# 31 → 3개 ['A~B', 'B~C', 'C~D'] 겹침 생김
# 40 → 3개 ['A~B', 'B~C', 'C~D'] 겹침 생김
```
<div class="til-note" data-til-line="16" hidden>AAAAAA....<br>BBBBBB....<br>CCCCCC....<br>DDDDDD....</div>
<div class="til-note" data-til-line="19" hidden>keep_separator=True라서, \n으로 나눌 때 구분자가 다음 조각의 맨 앞에 붙어서 남음<br>"A"*30,        # 길이 30  (맨 앞 조각이라 \n 없음)<br>"\n" + "B"*30, # 길이 31  (\n + B)<br>"\n" + "C"*30, # 길이 31<br>"\n" + "D"*30, # 길이 31<br>병합과정에서는 chunk_1(30+31) 확정 된 후<br>겹칩(overlap)을 만드는 데 만드는 방식이 확정된 청크에서 조각을 하나씩 통째로 빼면서<br>남은 길이가 chunk_overlap보다 작거나 같아질 때 까지 반복함<br>겹침이 생기는 문턱이 30 과 31 사이임 — 줄 길이 30 + 구분자 1자 = 31</div>
</div>

!!! danger "겹침은 글자 단위가 아니라 조각 단위임"
    처음엔 `chunk_overlap` 을 주면 분할기가 앞 청크 끝 N글자를 잘라서  
    다음 청크 앞에 복사해준다고 생각했는데 완전히 틀렸음.  
    분할기는 청크를 하나 내보낸 뒤, 앞에서부터 조각을 `버리는 반복문`을 도는데  
    조건이 `while toral > chunk_overlap` 임.  
    즉 남은 조각들의 길이 합이 `chunk_overlap` **이하가 될 때까지 통째로 버림.**  
    `청크에서 조각 들을 한개 씩 빼면서 나머지 조각들의 합`` <= `chunk_overlap` 이 될때까지  
    조각 하나가 `chunk_overlap` 보다 길면 그 조각도 버려져서 `겹침이 0` 이 됨.  
    정리하면 → 겹침이 실제로 남으려면 `마지막 조각 길이 <= chunk_overlap` 이어야 함.  
    글자를 잘라서 채우는 게 아니라 `줄·문장 같은 조각을 통째로 넘기거나 안 넘기거나` 둘 중 하나임.

<div class="til-code" markdown>
```python hl_lines="3"
page1 = pages[0].page_content

# [22, 8, 49, 49, 5, 8, 59, 52, 30, 8, 48, 30, 9, 47, 33, 8, 50, 45, 6]
print([len(line) for line in page1.split("\n")])


def longest_shared_boundary(left_text, right_text, limit=400):
    for width in range(min(len(left_text), len(right_text), limit), 0, -1):
        if left_text[-width:] == right_text[:width]:
            return left_text[-width:]
    return ""


for overlap in [45, 50, 80]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=overlap)
    chunks = splitter.split_text(page1)
    shared = [len(longest_shared_boundary(chunks[i], chunks[i + 1]))
              for i in range(len(chunks) - 1)]
    print(overlap, len(chunks), shared)

# 45 → 3개, 실제 겹침 [0, 0]
# 50 → 3개, 실제 겹침 [0, 47]
# 80 → 4개, 실제 겹침 [74, 79, 59]
```
<div class="til-note" data-til-line="3" hidden>본문 줄이 대부분 45~59자임. 이게 조각 하나의 길이가 됨</div>
</div>

!!! example "실제 겹친 글자를 재봄"
    `chunk_overlap=45` 를 줬는데 `실제 겹친 글자는 0` 이었음.  
    본문 줄이 전부 45자보다 길어서 마지막 줄이 통째로 버려진 것임.  
    50 으로 올리니 47자짜리 줄 하나가 살아남아서 한 경계에만 겹침이 생겼고,  
    80 으로 올리니 세 경계 전부에 겹침이 생겼음.  
    실무 규칙으로 적어두면 → `chunk_overlap` 은 **문서의 평균 줄 길이(또는 문장 길이)보다 크게** 줘야  
    의미가 있음. 이 PDF 기준으로는 최소 60 이상.

## 겹침을 줘도 청크 수가 안 늘어나는 경우

겹침이 무시되면 청크 수도 그대로임. 겹침을 켰는데 결과가 안 바뀌면 이걸 의심해야 함.

<div class="til-code" markdown>
```python hl_lines="4 12"
for overlap in [0, 10, 20]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=60, chunk_overlap=overlap)
    chunks = splitter.split_text(sample_text)
    print(overlap, len(chunks), [len(c) for c in chunks], repr(chunks[1][:12]))

# 0  → 3개 [49, 53, 38] '오픈AI가 GPT-5.'
# 10 → 3개 [49, 53, 38] '오픈AI가 GPT-5.'
# 20 → 3개 [49, 53, 38] '오픈AI가 GPT-5.'

for overlap in [0, 20, 50, 80]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=250, chunk_overlap=overlap)
    print(overlap, len(splitter.split_documents(pages)))

# 0 → 9,  20 → 9,  50 → 9,  80 → 10
```
<div class="til-note" data-til-line="4" hidden>겹침을 0 → 20 으로 올려도 청크가 글자 하나 안 바뀜</div>
<div class="til-note" data-til-line="12" hidden>PDF 에서도 80 이 되어서야 청크가 하나 늘어남</div>
</div>

!!! note "위 규칙의 직접적인 증거"
    `sample_text` 는 문단 하나가 49~53자라서  
    겹침 20 으로는 문단 하나도 못 넘김 → 결과가 완전히 동일함.  
    위 `chunk_overlap` 규칙의 직접적인 증거임.

## 검색 결과와 RAG 답변으로 크기 고르기

여기부터는 OpenAI 임베딩·LLM 을 호출하는 구간임. 나는 API 키가 없어서 재현 못 했고,<br>아래 수치와 답변은 **원본 노트북 실행 결과를 그대로 옮긴 것**임.

<div class="til-code" markdown>
```python
from uuid import uuid4
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
store = Chroma.from_documents(
    documents=documents_by_size[250],
    embedding=embedding,
    collection_name=f"chunking_{uuid4().hex}",
)
retriever = store.as_retriever(search_kwargs={"k": 3})

prompt = PromptTemplate.from_template(
    "다음 문맥만 사용하여 질문에 답하세요.\n"
    "문맥에 답의 근거가 없으면 '제공된 문서에서 근거를 찾지 못했습니다.'라고 답하세요.\n\n"
    "문맥:\n{context}\n\n질문: {question}\n답변:"
)

def format_docs(documents):
    return "\n\n".join(d.page_content for d in documents)

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
    | StrOutputParser()
)
print(chain.invoke("우대 금리는 어떤 조건에서 적용되나요?"))
```
</div>

!!! abstract "크기별 검색·답변 결과"
    같은 질문 `우대 금리는 어떤 조건에서 적용되나요?` 를 크기별 벡터 저장소에 `k=1` 로 던졌을 때  
    
    | 청크 크기 | 색인 청크 수 | 검색된 위치 | 청크 길이 | RAG 답변 |  
    |---|---|---|---|---|  
    | 100 | 24 | 1쪽 | 92자 | 근거를 찾지 못했습니다 |  
    | 250 | 9 | 2쪽 | 243자 | 조건 2개와 각각의 금리를 정확히 답함 |  
    | 500 | 6 | 2쪽 | 489자 | 조건 2개를 답함 (재예치·세금 내용도 같이 딸려옴) | 

    100자 청크가 실패한 이유가 중요함. 검색기는 `우대 금리가 추가 적용됩니다...` 라는  
    **그럴듯한 청크를 실제로 찾아냄.** 그런데 그 청크에는 "무슨 조건에서" 가 안 들어있었음.  
    조건(급여 이체, 마케팅 동의)은 2쪽의 다른 청크로 잘려 있었음.  
    즉 검색이 틀린 게 아니라 `청크가 답을 담기엔 너무 작았던 것`임.  
    500자는 답은 맞췄지만 청크에 `7. 이자 지급`, `8. 세금 및 비용` 까지 딸려옴.  
    관련 없는 내용이 문맥에 섞이면 토큰을 더 쓰고 LLM 이 헷갈릴 여지가 생김.  
    이 문서에서는 250 이 균형점이었음.

## 출발 설정을 제안하는 함수

평균 페이지 길이로 시작값을 고르는 함수. 정답이 아니라 실험 시작점임.

<div class="til-code" markdown>
```python hl_lines="20"
def suggest_starting_setting(documents, has_structure=False):
    page_lengths = [len(document.page_content) for document in documents]
    average_page_length = sum(page_lengths) / len(page_lengths)

    if average_page_length < 200:
        size = 100
    elif average_page_length < 500:
        size = 250
    else:
        size = 500

    return {
        "strategy": "structure-first" if has_structure else "recursive",
        "size": size,
        "overlap": int(size * 0.2),
        "average_page_length": round(average_page_length, 1),
    }


print(suggest_starting_setting(pages))
# {'strategy': 'recursive', 'size': 500, 'overlap': 100, 'average_page_length': 576.7}
```
<div class="til-note" data-til-line="20" hidden>평균 576.7자라서 함수가 500 을 제안함</div>
</div>

!!! question "함수는 500 인데 실제로는 250 이 좋았음"
    ★ 여기서 걸린 것 → 이 함수는 `500 을 제안하는데, 실제로 검색해보니 250 이 더 좋았음.`  
    함수가 틀린 게 아니라, 함수가 볼 수 없는 정보로 결정되는 값이라는 뜻임.  
    `overlap` 도 함수는 20% (=100) 를 주는데, 위에서 확인한 대로  
    이 문서의 줄 길이가 45~59자니까 100 이면 겹침이 실제로 잘 남음. 이건 타당한 값이었음.

## 전략 선택 정리

여섯 가지 분할 방식의 기준과 쓸 자리.

!!! abstract "전략 선택과 결정 순서"
    | 방식 | 경계 기준 | 상한 보장 | 쓸 자리 |  
    |---|---|---|---|  
    | 고정 길이 슬라이싱 | 글자 수만 | 예 | 구조가 아예 없는 텍스트 |  
    | Character | 구분자 1개 | **아니오** | 구분자가 문서 전체에 일정할 때 |  
    | Recursive | 구분자 목록을 순서대로 후퇴 | 예 | 일반 본문의 기본값 |  
    | Token | 토큰 위치 | 예 (글자 깨짐) | 모델 입력 토큰을 꽉 맞춰야 할 때 |  
    | Markdown 제목 | 제목 계층 | **아니오** | 제목 구조가 있는 문서, Recursive 와 연결 |  
    | Semantic | 인접 문장 임베딩 유사도 | 아니오 | 주제가 섞인 긴 글, 비용 발생 |  

    결정 순서로 적어두면:  
    1. 문서에 제목 구조가 있나 → 있으면 `MarkdownHeaderTextSplitter` 로 먼저 나누고 metadata 를 챙김  
    2. 그 다음 길이 제한은 `RecursiveCharacterTextSplitter` 로 함  
    3. 구분자 목록에 문서 형식에 맞는 기호를 넣고 `keep_separator="end"` 를 줌  
    4. 모델 토큰 상한을 정확히 맞춰야 하면 `from_tiktoken_encoder()` 로 길이 함수를 바꿈  
    5. `chunk_overlap` 은 문서의 줄·문장 길이보다 크게 줌  
    6. 실제 질문 3개 이상으로 검색 결과를 보고 크기를 조정함