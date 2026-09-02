---
title: 문서 로딩 — PDF · 웹 · JSON · CSV 로더
date: 2026-09-02
tags: [rag]
---
 
# 문서 로딩 — PDF · 웹 · JSON · CSV 로더
 
> 원본 코드: [`03_loaders.py`](03_loaders.py)
 
## 로더는 전부 같은 모양임
 
원천이 뭐든 `로더 객체를 만들고 → load()` 두 줄이고, 결과는 항상 `list[Document]` 임.<br>형식마다 달라지는 건 `Document 하나가 무엇이냐`와 `metadata 에 뭐가 남느냐` 뿐임.
 
## load() 와 lazy_load()
 
`load()` 는 전부 리스트로, `lazy_load()` 는 하나씩 꺼내는 제너레이터로 줌
 
<div class="til-code" markdown>
```python hl_lines="16"
from langchain_community.document_loaders import CSVLoader
csv_loader = CSVLoader("articles.csv", encoding="utf-8")
 
# load() 는 파일 전체를 메모리에 올림
all_documents = csv_loader.load()
print(type(all_documents).__name__, len(all_documents))     # list 5
 
# lazy_load() 는 아직 아무것도 안 읽음. `next()` 를 부를 때마다 한 개씩 만듦
csv_iterator = csv_loader.lazy_load()
print(type(csv_iterator).__name__)                          # generator
 
first_document = next(csv_iterator)
second_document = next(csv_iterator)
remaining = list(csv_iterator)
print(len(remaining), remaining[0].metadata["row"])         # 3 2
```
<div class="til-note" data-til-line="16" hidden>이미 2개를 꺼냈으므로 남은 건 3개, 그리고 `row` 는 `2` 부터 시작함</div>
</div>
 
## PyPDFLoader — Document 하나 = PDF 1장
 
<div class="til-code" markdown>
```python hl_lines="16"
import os
os.environ["USER_AGENT"] = "rag-lecture/1.0"
 
from langchain_community.document_loaders import PyPDFLoader
 
PDF_PATH = "SPRi_AI_Brief_8월호.pdf"
pdf_docs = PyPDFLoader(PDF_PATH).load()
 
# 점검 ① 개수 — PDF 장수와 같아야 함
print(len(pdf_docs))                                    # 29
 
# 점검 ② 본문 — 글자가 실제로 뽑혔는지 눈으로 봄
sample_document = pdf_docs[4]
print(sample_document.page_content[:300].replace("\n", " "))
 
print({k: sample_document.metadata[k] for k in ("source", "page")})
 
# 점검 ③ 메타데이터 — 내부 `page` 는 0부터라 사람에게 보여줄 땐 `+1`
print(sample_document.metadata["page"] + 1)             # 5
```
<div class="til-note" data-til-line="16" hidden>실행 결과 {'source': 'SPRi_AI_Brief_8월호.pdf', 'page': 4}</div>
</div>
## WebBaseLoader — 페이지 하나 = Document 하나
 
URL 을 주면 HTML 껍데기를 걷어내고 본문 텍스트만 남겨줌.
 
<div class="til-code" markdown>
```python hl_lines="6 9"
from langchain_community.document_loaders import WebBaseLoader
WEB_URL = "https://spri.kr/posts?code=AI-Brief"
web_docs = WebBaseLoader(WEB_URL).load()
 
# URL 1개 = Document 1개. 
print(len(web_docs))            # 1
 
# 실행 결과 keys → source, title, description, language
print(web_docs[0].metadata)
 
body = " ".join(web_docs[0].page_content.split())
 
print(body[:120])
```
<div class="til-note" data-til-line="6" hidden>페이지가 아무리 길어도 안 쪼개짐</div>
<div class="til-note" data-til-line="9" hidden>`source` 에 요청한 URL 이 그대로 들어감</div>
</div>
 
## JSONLoader — jq 로 원하는 필드만 골라 담기
 
`jq_schema` 가 고른 결과 하나가 `Document` 하나가 됨.
 
<div class="til-code" markdown>
```python
import json
from langchain_community.document_loaders import JSONLoader
 
ai_news = [
    {"id": 1, "date": "2026-08-10", "content": "앤트로픽이 Claude Opus 5를 출시했다.",
     "tags": ["기업", "모델"]},
    {"id": 2, "date": "2026-08-10", "content": "오픈AI가 GPT-5.6 제품군을 출시했다.",
     "tags": ["기업", "모델"]},
]
 
with open("ai_news.json", "w", encoding="utf-8") as file:
    json.dump(ai_news, file, ensure_ascii=False, indent=2)
 
# . 전체 배열 → [] 항목 하나씩 → .content 그 안의 본문 필드
json_docs = JSONLoader("ai_news.json", jq_schema=".[].content", text_content=True).load()
 
print(len(json_docs))               # 2
print(json_docs[0].page_content)    # 앤트로픽이 Claude Opus 5를 출시했다.
print(json_docs[0].metadata)        # {'source': '/절대경로/ai_news.json', 'seq_num': 1}
```
</div>
!!! info "seq_num · source 규칙"
    `metadata` 에 `seq_num` 이 자동으로 들어감. `1` 부터 시작하는 순번임.  
    `source` 는 CSV 와 달리 `절대경로`가 들어감.  
    즉 로더마다 `source` 에 담기는 게 다름 → PDF는 준 경로 그대로, JSON은 절대경로, 웹은 URL.  
    두 방식의 차이  
    `.[].content` → 값(문자열)을 고름 → 본문만 남고 나머지는 버려짐  
    `.[]` + `content_key` → 객체를 고름 → 본문과 metadata 를 나눠 담을 수 있음
 
!!! warning "text_content 는 검사만 함"
    `text_content=False` 로 배열을 본문에 넣으면 어떻게 될까?  
    `json.dumps` 로 문자열화되면서 한글이 `\uae30\uc5c5` 처럼 escape 됨.  
    `text_content=True` 의 뜻은 `본문이 문자열인지 검사하겠다` 임. 문자열 변환을 해주는 게 아님.  
    문자열이 아니면 위처럼 `ValueError` 를 내고 멈춤. 일종의 안전장치임.
 
<div class="til-code" markdown>
```python hl_lines="1 2 3 4 8"
def review_metadata(record, metadata):
    metadata["id"] = record["id"]
    metadata["tags"] = record["tags"]
    return metadata
json_full_docs = JSONLoader(
    file_path="ai_news.json",
    jq_schema=".[]",
    content_key="content",
    metadata_func=review_metadata,
    text_content=True,  # json 파일이 문자열로만 이루어져 있는지 여부
).load()
 
# 실행 결과 {'source': ..., 'seq_num': 1, 'id': 1, 'tags': ['기업', '모델']}
print(json_full_docs[0].metadata)
# 배열을 본문으로 만들려고 하면 막힘
try:
    JSONLoader("ai_news.json", jq_schema=".[].tags", text_content=True).load()
except ValueError as error:
    print(error)
 
tag_docs = JSONLoader("ai_news.json", jq_schema=".[].tags", text_content=False).load()
 
# 실행 결과 '["\\uae30\\uc5c5", "\\ubaa8\\ub378"]' — 한글이 escape 되어버림
print(repr(tag_docs[0].page_content))
```
<div class="til-note" data-til-line="4" hidden>record   = jq_schema 로 뽑아낸 항목 하나 (원본 JSON 그대로)<br>{'id': 1, 'date': '2026-08-10', 'content': '앤트로픽이 ...', 'tags': ['기업','모델']}<br>metadata = LangChain 이 이미 만들어둔 기본값<br>{'source': '/절대경로/ai_news.json', 'seq_num': 1}`<br>함수 실행 시 metadata에 `'id': 1, 'tags': ['기업','모델']` 이 추가됨<br>이 함수는 항목 개수만큼 `자동으로` 불림. 내가 부르는 게 아님.<br>Expected page_content is string, got <class 'list'> instead.</div>
<div class="til-note" data-til-line="8" hidden>`.[]` 로 객체 `전체`를 고르고, 그중 본문으로 쓸 키를 `content_key` 로 지정<br>이렇게 해야 본문은 본문대로, 나머지 필드는 metadata 로 살릴 수 있음</div>
</div>
 
## 실제 OpenAPI — 호출과 로딩은 분리해야 함
 
`JSONLoader` 는 URL 을 못 읽음. `API 호출 → 파일 저장 → 로더` 3단계로 나눠야 함.
 
!!! tip "이 예제의 핵심"
    `metadata_func` 에서 `source` 를 덮어쓸 수 있다는 게 이 예제의 핵심임.  
    원본 실행 결과의 source 가 파일 경로가 아니라 dart.fss.or.kr 원문 링크로 바뀌어 있었고,  
    거기에 `seq_num`, `corp_name`, `rcept_no`, `rcept_dt` 가 같이 들어 있었음.  
    이렇게 해두면 나중에 검색 결과에 `원문 보기` 링크를 바로 붙일 수 있음.  
    이 API 가 주는 건 공시 `원문`이 아니라 `목록`임. 본문이 보고서 제목뿐이라 아주 짧음.
 
!!! danger "검사는 두 층"
    `raise_for_status()` 와 `status != "000"` 검사는 서로 다른 층을 봄. 둘 다 필요함.  
    앞은 `HTTP 통신`이 성공했는지, 뒤는 `API 처리`가 성공했는지를 봄.  
    인증키가 틀려도 서버는 HTTP 200 을 주면서 응답 본문에 에러 코드를 담아 보냄.  
    앞 검사만 하면 에러 응답을 정상 데이터로 착각하고 진행하게 됨.
 
<div class="til-code" markdown>
```python
# 복습 시 json 파일아렁 같이 보면 이해하기 쉬워짐
 
from datetime import date, timedelta
 
import requests
from dotenv import load_dotenv
 
load_dotenv()
dart_api_key = os.getenv("DART_API_KEY")
 
 
response = requests.get(
    "https://opendart.fss.or.kr/api/list.json",
    params={
        "crtfc_key": dart_api_key,
        "bgn_de": (date.today() - timedelta(days=30)).strftime("%Y%m%d"),
        "end_de": date.today().strftime("%Y%m%d"),
        "page_count": 20,
    },
    timeout=30,
)
 
# HTTP 상태가 4xx·5xx 면 여기서 예외를 던짐. 200이면 그냥 지나감
response.raise_for_status()
dart_data = response.json()
 
# HTTP 200 인데도 API 자체는 실패일 수 있음. 응답 안의 status 를 따로 봐야 함
if dart_data.get("status") != "000":
    raise RuntimeError(dart_data.get("message", "DART API 호출 실패"))
 
with open("dart_disclosures.json", "w", encoding="utf-8") as file:
    json.dump(dart_data, file, ensure_ascii=False, indent=2)
 
 
# source 를 덮어써서 파일 경로 대신 원문 링크를 넣음
def add_dart_metadata(record, metadata):
    metadata["corp_name"] = record["corp_name"]
    metadata["rcept_no"] = record["rcept_no"]
    metadata["source"] = (
        f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={record['rcept_no']}"
    )
    return metadata
 
 
dart_docs = JSONLoader(
    file_path="dart_disclosures.json",
    jq_schema=".list[]",
    content_key="report_nm",
    metadata_func=add_dart_metadata,
    text_content=True,
).load()
```
</div>
## CSVLoader — 한 행 = Document 한 개
 
각 행이 `컬럼명: 값` 텍스트가 됨. 어느 열을 본문/출처/필터로 쓸지 지정할 수 있음.
 
<div class="til-code" markdown>
```python hl_lines="16 22 23 28"
# articles.csv
# 제목,분야,쪽
# 앤트로픽 Claude Opus 5 출시,기업·산업,10
# 사카나 AI Fugu 공개,기업·산업,11
# 오픈AI GPT-5.6 출시,기업·산업,13
# 클로드 내부 작업공간 발견,기술·연구,15
# OECD AI 노동시장 분석,인력·교육,24
 
csv_docs = CSVLoader("articles.csv", encoding="utf-8").load()
 
print(len(csv_docs))                    # 5 (행 수와 같음)
 
 
print(repr(csv_docs[2].page_content))   # '제목: 오픈AI GPT-5.6 출시\n분야: 기업·산업\n쪽: 13'
print(csv_docs[2].metadata)             # {'source': 'articles.csv', 'row': 2}
 
# 열의 역할을 나눠서 지정
role_docs = CSVLoader(
    file_path="articles.csv",
    encoding="utf-8",
    source_column="제목",
    metadata_columns=("분야", "쪽"),
).load()
 
print(repr(role_docs[0].page_content)) # '제목: 앤트로픽 Claude Opus 5 출시' 
 
# {'source': '앤트로픽 Claude Opus 5 출시', 'row': 0, '분야': '기업·산업', '쪽': '10'}
print(role_docs[0].metadata)
```
<div class="til-note" data-til-line="16" hidden>`row` 는 `0` 부터 시작함. JSON 의 `seq_num` 이 1부터인 것과 다름</div>
<div class="til-note" data-til-line="22" hidden>`source_column` → 그 열의 값이 `metadata["source"]` 가 됨</div>
<div class="til-note" data-til-line="23" hidden>`metadata_columns` → 그 열들은 본문에서 빠지고 metadata 로 감</div>
<div class="til-note" data-til-line="28" hidden>`쪽` 값이 `'10'` 문자열임. CSV 는 타입 정보가 없어서 전부 문자열로 들어옴</div>
</div>
 
!!! note "인자 비교"
    | 인자 | 하는 일 | 본문에서 빠지나 |
    |---|---|---|
    | `content_columns` | 본문에 넣을 열을 `지정` | 나머지가 전부 빠짐 |
    | `metadata_columns` | metadata 로 옮길 열 | 빠짐 |
    | `source_column` | `metadata["source"]` 값으로 쓸 열 | 안 빠짐 |
 
    `source_column="제목"` → source 값만 교체되고 `제목:` 은 본문에 그대로 남음  
    `metadata_columns=("분야","쪽")` → 이 열들은 본문에서 제외됨  
    즉,`source_column` 은 본문에서 안 빼고, `metadata_columns` 는 뺌. 동작이 다름.
 
 
 
## 형식마다 Document 단위가 다르다
 
같은 `load()` 인데 무엇이 문서 하나인지가 형식마다 달라짐.
 
!!! abstract "형식별 정리"
    | 형식 | Document 단위 | 원본 결과 | metadata 키 |
    |---|---|---|---|
    | PDF | 쪽 | 29개 | source, page, page_label, total_pages 등 10개 |
    | 웹 | URL 페이지 | 1개 | source, title, description, language |
    | JSON | jq 로 고른 값 | 3개 | source(절대경로), seq_num |
    | CSV | 행 | 5개 | source, row |
 
    이 표에서 제일 중요한 건 `단위를 내가 정할 수 있는 건 JSON 뿐`이라는 점임.  
    PDF·CSV 는 쪽·행으로 이미 정해져 있고, 웹은 통짜 1개임.  
    JSON 만 `jq_schema` 로 잘게도 크게도 만들 수 있음.  
    그래서 웹 문서는 로딩 후 반드시 분할기를 태워야 하고,  
    CSV 는 행이 이미 짧으니 분할이 필요 없는 경우가 많음. 형식에 따라 다음 단계가 달라짐.
 
## PDF 함정 ① — 화면에는 있는데 안 뽑히는 글자
 
텍스트 레이어가 없는 쪽은 `PyPDFLoader` 가 거의 아무것도 못 읽음.<br>즉, 텍스트가 아닌 그림은 `PyPDFLoader`가 처리하지 못함.<br>핵심 → PDF안에 있는 `이미지를 추출`해서 `저장`하고 `ocr을 활용하여 텍스트를 읽는 것`
 
<div class="til-code" markdown>
```python hl_lines="10"
OCR_PDF_PATH = "자동차보험다이렉트약관.pdf"
ocr_pdf_docs = PyPDFLoader(OCR_PDF_PATH).load()
 
ocr_target_document = ocr_pdf_docs[13]
ocr_target_text = ocr_target_document.page_content.strip()
 
print(len(ocr_pdf_docs))            # 218
print(len(ocr_target_text))         # 18
 
# 실행 결과 'KB다이렉트개인용자동차보험  13' — 바닥글만 나옴
print(repr(ocr_target_text))
```
<div class="til-note" data-til-line="10" hidden>화면에는 `교통사고 처리 절차 안내` 본문이 가득한 쪽인데 본문이 통째로 없음</div>
</div>
!!! warning "글자가 그림으로 들어있음"
    PDF 안에 글자가 `텍스트`가 아니라 `그림`으로 들어있는 것임.  
    스캔본이나 이미지로 붙여넣은 페이지가 이렇게 됨.
 
PDF 안 그림을 추출 후 저장하고 ocr 엔진을 활용하여 텍스트 읽어오기
 
<div class="til-code" markdown>
```python hl_lines="12 21 29"
# == 1. PDF 안 그림 추출해서 저장 ==
import pymupdf
 
ocr_image_path = "auto_policy_page_14.png"
 
# PDF 열기 -> pymupdf.Document 클래스
pdf = pymupdf.open(OCR_PDF_PATH)
 
# 페이지 선택 -> pymupdf.Page 클래스
page = pdf[13]
 
# get_pixmap() = PDF 페이지(그리기 명령)를 실제 픽셀 이미지로 그리는 것.
pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
 
# 저장
pix.save(ocr_image_path)
 
# PDF 닫기
pdf.close()
 
print(pix.width, pix.height, pix.n)
 
 
# == 2. 저장한 이미지를 OCR 엔진을 활용하여 텍스트로 읽기 ==
import easyocr
 
reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)
 
lines = reader.readtext(ocr_image_path, detail=0)
 
print(len(lines))       # 39
```
<div class="til-note" data-til-line="12" hidden>`Matrix(2, 2)` 는 가로·세로 해상도 2배 확대. 글자가 커져야 OCR 인식률이 올라감<br>`alpha=False` 는 투명 채널을 뺌. PDF 배경은 불투명 흰색이라 알파는 정보가 없음</div>
<div class="til-note" data-til-line="21" hidden>채널 수 `n` 은 `alpha=False` 면 3(RGB), `True` 면 4(RGBA)</div>
<div class="til-note" data-til-line="29" hidden>detail=0 → 인식된 문자열 목록만.<br>detail=1 → (위치(bbox), 텍스트(text), 신뢰도(confidence)) 튜플 목록</div>
</div>
 
!!! tip "권장 순서"
    기본은 `PyPDFLoader` → 글자수가 적은 쪽만 골라서 `EasyOCR 보완` → 신뢰도 낮은 항목은 원본 대조.  
    처음부터 전체를 OCR 로 돌리면 느리기만 하고 정확도는 오히려 떨어짐.
 
## PDF 함정 ② — 표가 평문으로 뭉개짐
 
`PyPDFLoader`로 텍스트를 가져와도 `page_content` 는 글자 순서만 남기므로 어느 셀이 같은 행인지 알 수 없게 됨.<br>핵심 → `pdfplumber`를 사용하여 표 복원하기
 
<div class="til-code" markdown>
```python hl_lines="6"
OCR_PDF_PATH = "자동차보험다이렉트약관.pdf"
ocr_pdf_docs = PyPDFLoader(OCR_PDF_PATH).load()
 
table_page_text = ocr_pdf_docs[32].page_content
 
print(table_page_text[:900])
```
<div class="til-note" data-til-line="6" hidden>보장종목 / 보상하는 내용 / 가. 대인배상Ⅰ 자동차사고로 ... 경우에 자동차<br>손해배상보장법에서 정한 한도에서 보상 / 나. 대인배상Ⅱ 자동차사고로 ...<br>줄바꿈으로만 이어져서 둘째 줄이 어느 행 소속인지 코드로는 알 수 없음</div>
</div>
!!! question "헷갈렸던 것"
    여기서 헷갈렸던 것 → 눈으로 보면 읽히니까 문제없어 보임.  
    근데 이걸 청크로 자르면 `가. 대인배상Ⅰ` 과 그 설명이 다른 청크로 갈라질 수 있음.  
    그러면 검색해서 설명만 가져왔을 때 `무엇에 대한 설명인지`가 사라짐.  
    표는 행 자체가 의미 단위라서, 행을 통째로 하나의 Document 로 만들어야 함.
 
PDF 표 복원 - pdfplumber
 
<div class="til-code" markdown>
```python hl_lines="5 8"
import pdfplumber
 
with pdfplumber.open(OCR_PDF_PATH) as pdf:
    simple_table_page = pdf.pages[8]
    simple_table = simple_table_page.extract_table()
 
print(type(simple_table).__name__, len(simple_table))   # list 17
print(simple_table[0])
```
<div class="til-note" data-til-line="5" hidden>`extract_table()` 은 가장 큰 표 하나를 `행 → 셀` 이중 리스트로 반환함<br>[<br>['① 보상하는 손해\n*본인이 가입한 특약을\n확인하여 가입특약별\n보상하는 손해도\n반드시 확인할 필요', '대인배상Ⅰ', '제3조', 'p. 33', None, None],<br>[None, '대인Ⅱ·대물배상', '제6조', 'p. 33', None, None],<br>[None, '자기신체사고', '제12조', 'p. 37', None, None]<br>]</div>
<div class="til-note" data-til-line="8" hidden>실행 결과 ['① 보상하는 손해\n...', '대인배상Ⅰ', '제3조', 'p. 33', None, None]<br>셀이 비면 `None` 이 들어옴.</div>
</div>
 
!!! info "pdfplumber 의 원리"
    `pdfplumber` 가 `PyPDFLoader` 와 다른 점은 `선의 좌표`를 본다는 것임.  
    글자만 읽는 게 아니라 가로선·세로선이 만드는 격자를 찾아서 셀을 나눔.  
    그래서 선이 그려진 디지털 PDF 에는 잘 맞고, 선이 없는 표나 스캔본에는 안 맞음.  
    `page.lines` 의 각 선은 `x0`, `x1`, `top`, `bottom` 좌표를 가짐  
    이 좌표들로 표의 사각형 영역 `bbox=(x0, top, x1, bottom)` 과 열 경계를 만들 수 있음.  
    표 복원의 결론은 `표의 한 행을 CSV 한 행처럼 만드는 것`임.  
    그래서 최종 형태가 `CSVLoader` 출력과 똑같은 `열이름: 값` 모양이 됨.  
    원본에서 6개 Document 가 나왔고(표 2개 × 3행), `pdf_page` 로 출처 추적도 됨.
 
<div class="til-code" markdown>
```python hl_lines="10 11 19"
from langchain_core.documents import Document
 
recovered_rows = [
    ["보장종목", "보상하는 내용"],
    ["가. ｢대인배상Ⅰ｣", "자동차사고로 다른 사람을 죽게 하거나 다치게 한 경우에 보상"],
]
 
table_docs = []
 
for coverage, description in recovered_rows[1:]:
    clean_coverage = " ".join((coverage or "").split())
    clean_description = " ".join((description or "").split())
 
    table_docs.append(
        Document(
            page_content=(
                f"보장종목: {clean_coverage}\n"
                f"보상하는 내용: {clean_description}"
            ),
            metadata={"source": OCR_PDF_PATH, "pdf_page": 33, "table": "표 1"},
        )
    )
```
<div class="til-note" data-til-line="10" hidden>머리글 행을 `[1:]` 로 건너뜀. 안 하면 '보장종목: 보장종목' 문서가 생김</div>
<div class="til-note" data-til-line="11" hidden>`(값 or "")` 으로 `None` 을 빈 문자열로 바꿈. 셀이 비어 있을 수 있어서 필요함</div>
<div class="til-note" data-til-line="19" hidden>열 이름을 본문에 같이 넣음. CSVLoader 가 하는 것과 똑같은 형태</div>
</div>
## 입력에 따른 로더 선택
 
확장자만 보면 안 되고, PDF 는 텍스트 레이어까지 확인해야 함.
 
<div class="til-code" markdown>
```python hl_lines="4"
def recommend_loader(path_or_url: str) -> str:
    lowered = path_or_url.lower()
 
    if lowered.startswith(("http://", "https://")):
        return "WebBaseLoader"
    if lowered.endswith(".pdf"):
        return "PyPDFLoader (텍스트 레이어 부족하면 EasyOCR 보완)"
    if lowered.endswith(".json"):
        return "JSONLoader"
    if lowered.endswith(".csv"):
        return "CSVLoader"
    return "형식을 확인하세요"
```
<div class="til-note" data-til-line="4" hidden>URL 검사를 `가장 먼저` 함. `https://.../report.pdf` 같은 경우 때문</div>
</div>
 
!!! warning "검사 순서"
    URL 을 먼저 검사하는 순서가 중요함. 확장자를 먼저 보면  
    `https://example.com/report.pdf` 가 `PyPDFLoader` 로 가버림.