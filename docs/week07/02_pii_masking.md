---
title: 개인정보 보호 RAG — 정규식으로 PII 탐지·마스킹하고 안전한 Document 만들기
date: 2026-09-08
tags: [regex]
---

# 개인정보 보호 RAG — 정규식으로 PII 탐지·마스킹하고 안전한 Document 만들기

> 원본 코드: [`02_pii.py`](02_pii.py)

## PII 가 뭔지부터

PII = Personally Identifiable Information(개인식별정보).<br>즉, 어떤 사람이 누구인지 특정할 수 있는 정보를 의미함.

<div class="til-code" markdown>
```python
- 정형 PII: 이메일·전화번호·주민등록번호·계좌번호처럼 형식이 정해져 있음 → 정규식으로 패턴 매칭해서 찾음.
- 비정형 PII: 사람 이름·주소처럼 형식이 없음 → 정규식으론 "김민지"가 이름인지 그냥 단어인지 구분 못 함. 
            그래서 필드 이름(키) 자체를 민감 정보로 취급해서 걸러내는 방식을 씀.
```
</div>

!!! info "정형과 비정형은 처리 방법이 다름"
    처음엔 정규식 하나로 다 잡을 수 있는 줄 알았는데, 비정형 PII(사람 이름 등)는 애초에 정규식 대상이 아니라는 걸 알게 됨.  
    그래서 아래에서 본문(정형 PII)은 정규식으로, metadata(이름 등 비정형 PII)는 키 이름으로 따로 처리함.

## Document 안에는 PII 가 두 군데 숨어있음

RAG에서 쓰는 Document 는 page_content(본문) 와 metadata(출처·속성) 를 같이 들고 있음.<br>**본문만 마스킹하고 metadata 를 그대로 두면** 검색 결과 카드에 metadata 가 그대로 노출돼서 다시 새는 구조임.

<div class="til-code" markdown>
```python hl_lines="15 16"
import re
from copy import deepcopy
from langchain_core.documents import Document

raw_documents = [
    Document(
        page_content=(
            "배송 지연 문의입니다. 회신은 minji.kim@example.com 또는 "
            "010-1234-5678로 부탁드립니다. 주민등록번호는 900101-2345678이며 "
            "환불 계좌는 110-245-987654입니다."
        ),
        metadata={
            "source": "synthetic-support-1",
            "category": "배송",
            "customer_name": "김민지",
            "contact_email": "minji.kim@example.com",
            "contact_phone": "010-1234-5678",
        },
    ),
]

# 결과 -> synthetic-support-1 ['category', 'contact_email', 'contact_phone', 'customer_name', 'source']
for document in raw_documents:
    print(document.metadata["source"], sorted(document.metadata))
```
<div class="til-note" data-til-line="15" hidden>`metadata 안에` 고객 이름이 평문으로 들어있음 → 본문을 아무리 마스킹해도 여기서 샘.</div>
<div class="til-note" data-til-line="16" hidden>이메일도 마찬가지로 본문(page_content)과 metadata 양쪽에 중복으로 존재함.</div>
</div>

## 정형 PII 는 정규식으로 탐지

이메일·전화번호·주민등록번호·계좌번호처럼 **형식이 정해진 값**은 정규식으로 잡을 수 있음.<br>사람 이름·주소처럼 자유 서술형인 건 정규식만으로는 못 잡음 → 그래서 metadata 는 키 기반으로 따로 처리함.

<div class="til-code" markdown>
```python hl_lines="5 6 7"
PII_PATTERNS = {
    "email": re.compile(
        r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9_%+-])"
    ),
    "phone": re.compile(r"(?<!\d)01[016789]-\d{3,4}-\d{4}(?!\d)"),
    "resident_number": re.compile(r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)"),
    "account": re.compile(r"(?<!\d)\d{3,6}-\d{3,6}-\d{5,8}(?!\d)"),
}


def detect_pii_types(text):
    detected = {}
    for pii_type, pattern in PII_PATTERNS.items():
        count = len(pattern.findall(text))
        if count:
            detected[pii_type] = count
    return detected


# 결과 -> {'email': 1, 'phone': 1, 'resident_number': 1, 'account': 1}
print(detect_pii_types(raw_documents[0].page_content))
```
<div class="til-note" data-til-line="5" hidden>`010-1234-5678` 형태. `<br>01[016789]` 라서 010/011/016/017/018/019 만 잡고, 앞뒤 lookaround 로 더 긴 숫자열의 일부가 잡히는 걸 막음.</div>
<div class="til-note" data-til-line="6" hidden>`900101-2345678` 형태. `\d{6}` 은 자릿수만 검사할 뿐 실제 생년월일인지는 확인 안 함.</div>
<div class="til-note" data-til-line="7" hidden>`123-456-78901` 형태. 은행마다 실제 자릿수가 달라서 모든 계좌번호 형식을 포괄하진 못하는 실습용 패턴.</div>
</div>

!!! warning "\d 는 [0-9]보다 범위가 넓음"
    `(?<!...)` `(?!...)` 는 lookbehind/lookahead 라서 조건만 검사하고 매칭 결과 문자열엔 안 들어감.  
    `\d` 는 파이썬에서 `[0-9]` 보다 범위가 넓음. 아랍 숫자(٣)나 태국 숫자(๙)도 `\d` 로 매치됨.  
    실무에서 한국어 문서라도 유니코드 숫자가 섞여 들어오면 의도치 않게 매치 범위가 넓어질 수 있다는 뜻.  
    필요하면 `re.compile(pattern, re.ASCII)` 로 좁혀야 함.

## 본문 마스킹 — 원문을 토큰으로 치환

마스킹은 원문 문자열을 지우는 게 아니라 `[EMAIL]` 같은 안전 토큰으로 바꿔치기하는 것.<br>마스킹 후엔 원문값이 아예 안 남으니까, 확인할 땐 토큰이랑 detect_pii_types() 결과만 봐야 함.

<div class="til-code" markdown>
```python hl_lines="12 15"
MASK_TOKENS = {
    "email": "[EMAIL]",
    "phone": "[PHONE]",
    "resident_number": "[RRN]",
    "account": "[ACCOUNT]",
}


def mask_text(text):
    masked_text = text
    for pii_type, pattern in PII_PATTERNS.items():
        masked_text = pattern.sub(MASK_TOKENS[pii_type], masked_text)
    return masked_text

# 결과
masked_example = mask_text(raw_documents[0].page_content)
print(masked_example)
assert detect_pii_types(masked_example) == {}
```
<div class="til-note" data-til-line="12" hidden>`PII_PATTERNS` 삽입 순서(email→phone→resident_number→account) 대로 masked_text 를 계속 덮어씀.<br>앞 패턴이 치환한 결과 위에 다음 패턴이 또 치환하는 구조.</div>
<div class="til-note" data-til-line="15" hidden>배송 지연 문의입니다. 회신은 [EMAIL] 또는 [PHONE]로 부탁드립니다.<br>주민등록번호는 [RRN]이며 환불 계좌는 [ACCOUNT]입니다.</div>
</div>

!!! example "치환 순서를 직접 테스트해봄"
    순서가 중요할 수도 있겠다 싶어서 직접 테스트해봄: `900101-2345678`(주민번호) 을  
    account 패턴에 바로 돌려보니 매치 `[]` 나옴 → 주민번호는 하이픈이 1개, account 는 하이픈 2개 형식이라  
    애초에 형식이 안 겹쳐서 이 경우엔 순서가 결과에 영향을 안 줌. 근데 패턴을 새로 추가할 땐 이 겹침 여부를 항상 체크해야 할 듯.

## metadata 정리 — 정규식이 아니라 키 이름으로 지움

고객 이름 같은 값은 정규식으로 안정적으로 못 찾음 → "이 키는 무조건 민감하다" 는 블랙리스트 방식으로 처리.<br>값을 지우는 대신 pii_masked_fields 에 어떤 키를 지웠는지 이력만 남김.

<div class="til-code" markdown>
```python hl_lines="15 17"
SENSITIVE_METADATA_KEYS = {
    "customer_name",
    "contact_email",
    "contact_phone",
    "resident_number",
    "account_number",
}


def sanitize_metadata(metadata):
    safe_metadata = {}
    masked_fields = []
    for key, value in metadata.items():
        if key in SENSITIVE_METADATA_KEYS:
            masked_fields.append(key)
        else:
            safe_metadata[key] = deepcopy(value)
    safe_metadata["pii_masked_fields"] = sorted(masked_fields)
    return safe_metadata

# 결과
print(sanitize_metadata(raw_documents[0].metadata))
```
<div class="til-note" data-til-line="15" hidden>민감 키는 값을 통째로 버리고 키 이름만 masked_fields 리스트에 적재함. 값 자체는 어디에도 안 남음.<br>{'source': 'synthetic-support-1', 'category': '배송',<br>'pii_masked_fields': ['contact_email', 'contact_phone', 'customer_name']}</div>
<div class="til-note" data-til-line="17" hidden>그냥 대입하면 원본 metadata 의 리스트/딕셔너리 값이 같은 객체를 공유하게 돼서,<br>safe_metadata 쪽을 나중에 수정하면 raw_documents 원본까지 같이 바뀔 위험이 있음.</div>
</div>

!!! tip "정렬해두면 결과가 항상 같아짐"
    sorted(masked_fields) 를 안 쓰고 그냥 리스트로 두면, 딕셔너리 순회 순서(=metadata 를 만들 때 넣은 순서)에 따라  
    결과가 매번 달라 보일 수 있음. 정렬해두면 같은 문서는 항상 같은 결과가 나와서 테스트하기 편함.

## 본문 + metadata 를 한 번에 — 안전한 Document 만들기

<div class="til-code" markdown>
```python
def sanitize_document(document):
    return Document(
        page_content=mask_text(document.page_content),
        metadata=sanitize_metadata(document.metadata),
    )

sanitized_documents = [sanitize_document(document) for document in raw_documents]

for document in sanitized_documents:
    print(document.page_content)
    print(document.metadata)
```
</div>

## 색인 전 안전 검사 — 본문 + metadata 둘 다 검사해야 함

마스킹을 "했다"는 것과 "안전하다"는 건 다른 얘기라서, 색인 직전에 다시 한번 스캔해서 확인하는 단계가 따로 필요함.

<div class="til-code" markdown>
```python hl_lines="9"
def validate_document_safe(document):
    text_pii = detect_pii_types(document.page_content)
    metadata_pii_keys = sorted(
        key for key in document.metadata if key in SENSITIVE_METADATA_KEYS
    )
    return {
        "text_pii": text_pii,
        "metadata_pii_keys": metadata_pii_keys,
        "safe": not text_pii and not metadata_pii_keys,
    }


safety_reports = [validate_document_safe(document) for document in sanitized_documents]
raw_reports = [validate_document_safe(document) for document in raw_documents]

assert all(report["safe"] for report in safety_reports)   # 마스킹 후 → 전부 안전
assert not all(report["safe"] for report in raw_reports)  # 마스킹 전 → 안전하지 않음
```
<div class="til-note" data-til-line="9" hidden>본문에 남은 PII 도 없고(not text_pii) metadata 에 남은 민감 키도 없어야(not metadata_pii_keys)<br>safe = True.</div>
</div>

!!! success "검증이 의도대로 동작함"
    본문만 깨끗해도 metadata 에 민감 키가 남아있으면 safe 가 False 로 떨어지는 걸 raw_reports 로 확인함.

## 정규식 마스킹의 한계 — 누락과 과다

정규식은 "형식"만 봄. 형식이 살짝만 달라도 놓치고(누락), 형식만 같으면 PII 가 아닌 것도 가림(과다).

<div class="til-code" markdown>
```python hl_lines="3 4 5 6 9"
quality_cases = {
    "normal_email": "user@example.com",
    "phone_with_spaces": "010 1234 5678",
    "rrn_without_hyphen": "9001012345678",
    "account_like_order_number": "주문번호 2026-1234-567890",
    "order_number": "ORD-2026-0001",
}

# 결과
for label, text in quality_cases.items():
    print(label, detect_pii_types(text), "->", mask_text(text))
```
<div class="til-note" data-til-line="3" hidden>누락(false negative): 하이픈 대신 공백을 쓴 전화번호. 패턴이 하이픈을 요구해서 못 잡음.</div>
<div class="til-note" data-til-line="4" hidden>누락(false negative): 하이픈 없는 주민번호도 같은 이유로 못 잡음.</div>
<div class="til-note" data-til-line="5" hidden>과다(false positive): 주문번호가 우연히 "숫자-숫자-숫자" 형태라서 계좌번호로 오인해 가려짐.</div>
<div class="til-note" data-til-line="6" hidden>정상: 숫자 아닌 문자가 섞여 있어서 계좌 패턴에 안 걸리고 안 가려짐.</div>
<div class="til-note" data-til-line="9" hidden>phone_with_spaces          {} -> 010 1234 5678<br>rrn_without_hyphen         {} -> 9001012345678<br>account_like_order_number  {'account': 1} -> 주문번호 [ACCOUNT]<br>order_number                {} -> ORD-2026-0001</div>
</div>

!!! question "빡빡하게 조이면 되지 않나"
    여기서 헷갈렸던 것 → "패턴을 더 빡빡하게 조이면 과다를 줄일 수 있지 않나?" 싶었는데,  
    빡빡하게 조이면 이번엔 변형된 진짜 PII(공백 전화번호 등)를 더 많이 놓치게 됨. 누락과 과다는 트레이드오프 관계라서  
    정규식 하나로 둘 다 완벽히 잡을 순 없고, 결국 사람 이름처럼 서술형 PII 는 NER 같은 별도 모델이 필요하다는 결론.

## 전화번호 패턴 확장 — 공백 표기 누락을 실제로 메꿔봄

위에서 "phone_with_spaces 는 누락된다"고 확인만 하고 넘어갔는데, 개인실습에서 그 누락을 실제로 고쳐봄.<br>하이픈 자리에 공백도 올 수 있게 문자 클래스를 넓히면 됨. `[ -]` 는 "공백 한 칸 또는 하이픈 한 개" 라는 뜻.

<div class="til-code" markdown>
```python hl_lines="5"
extended_phone_pattern = re.compile(r"(?<!\d)01[016789][ -]\d{3,4}[ -]\d{4}(?!\d)")
 
assert extended_phone_pattern.search("연락처 010-1234-5678")
assert extended_phone_pattern.search("연락처 010 1234 5678")
assert extended_phone_pattern.search("ORD-2026-0001") is None
```
<div class="til-note" data-til-line="5" hidden>주문번호는 여전히 안 잡힘. `01` 로 시작하지 않아서 `01[016789]` 부분부터 매칭이 안 됨 → 오탐 걱정 없이 확장된 것 확인함.</div>
</div>

!!! note "확장은 됐고, account 는 보류"
    `-` 하나만 문자 클래스로 바꿨을 뿐인데 누락 하나가 없어짐. 근데 이 확장을 `PII_PATTERNS["phone"]` 에 바로 반영하면  
    계좌번호 패턴(`account`) 쪽 문자 클래스도 공백 표기까지 넓혀야 하나 고민됨 → 지금은 전화번호만 확장

## 전체 파이프라인으로 묶기

<div class="til-code" markdown>
```python hl_lines="6"
def prepare_documents_for_index(documents):
    safe_documents = []
    for document in documents:
        sanitized_document = sanitize_document(document)
        if not validate_document_safe(sanitized_document)["safe"]:
            raise ValueError("PII가 남은 문서는 색인할 수 없습니다.")
        safe_documents.append(sanitized_document)
    return safe_documents


index_ready_documents = prepare_documents_for_index(raw_documents)
assert len(index_ready_documents) == len(raw_documents)
```
<div class="til-note" data-til-line="6" hidden>정리(sanitize) → 검증(validate) → 통과 못 하면 예외.<br>이 함수의 반환값만 다음 단계(청킹·임베딩)로 넘어감.</div>
</div>

## 미션 — 마스킹 결과 리포트 만들기

원문 값 노출 없이 출처 / 제거한 필드 / 색인 가능 여부 / 남은 PII 만 뽑아내는 리포트 함수.<br>직접 짜본 함수, mission_documents 3건 다 통과하는 것까지 확인함.

<div class="til-code" markdown>
```python hl_lines="45"
mission_documents = [
    Document(
        page_content=(
            "교육비 환급 문의입니다. 회신은 training.user@example.org 또는 "
            "010-2468-1357로 부탁드립니다."
        ),
        metadata={
            "source": "synthetic-mission-1",
            "category": "교육비",
            "customer_name": "최유진",
            "contact_email": "training.user@example.org",
        },
    ),
    Document(
        page_content="계약 해지 환급 계좌는 333-4567-123456입니다.",
        metadata={
            "source": "synthetic-mission-2",
            "category": "계약 해지",
            "account_number": "333-4567-123456",
        },
    ),
    # 본문엔 PII 가 없고 metadata 에만 있는 케이스
    Document(
        page_content="서비스 이용 시간 변경 문의입니다.",
        metadata={
            "source": "synthetic-mission-3",
            "category": "일반 문의",
            "customer_name": "이현수",
            "contact_phone": "010-7777-8888",
        },
        
    ),
]


def build_masking_report(documents):
    report_rows = []
    for document in documents:
        sanitized = sanitize_document(document)
        validation = validate_document_safe(sanitized)
        report_rows.append({
            "source": sanitized.metadata["source"],
            "masked_fields": sanitized.metadata["pii_masked_fields"],
            "index_ready": validation["safe"],
            "remaining_text_pii": sorted(validation["text_pii"]),
        })
    return report_rows


masking_report = build_masking_report(mission_documents)
assert len(masking_report) == 3
assert all(row["index_ready"] for row in masking_report)
assert masking_report[0]["masked_fields"] == ["contact_email", "customer_name"]
assert masking_report[1]["masked_fields"] == ["account_number"]
assert masking_report[2]["masked_fields"] == ["contact_phone", "customer_name"]
```
<div class="til-note" data-til-line="45" hidden>validation["text_pii"] 는 {'email': 1, ...} 같은 딕셔너리라서, sorted() 로 키만 뽑아 정렬된 리스트로 바꿈.</div>
</div>

!!! note "딕셔너리 대신 정렬된 리스트로"
    리포트 함수를 짤 때 처음엔 remaining_text_pii 에 validation["text_pii"] (딕셔너리)를 그대로 넣으려다가,  
    과제 요구사항이 "정렬한 목록" 이라길래 sorted(validation["text_pii"]) 로 키만 뽑아서 리스트로 바꿈.

## 색인 문서 + 운영 보고서를 한 번에 — safe_index_pipeline

prepare_documents_for_index() 는 "색인해도 되는 Document 리스트"만 주고,<br>build_masking_report() 는 "뭘 지웠는지 보고서"만 줌. 실제로 파이프라인에 넣을 땐 이 둘을 같이 써야 하는 경우가 많아서<br>두 함수를 그대로 재사용해서 하나로 묶는 함수를 개인실습에서 만들어봄.

<div class="til-code" markdown>
```python hl_lines="4"
def safe_index_pipeline(documents):
    return {
        "documents": prepare_documents_for_index(documents),
        "report": build_masking_report(documents),
    }
 
pipeline_result = safe_index_pipeline(raw_documents)
```
<div class="til-note" data-til-line="4" hidden>보고서는 원본 documents 를 다시 받아서 별도로 만듦</div>
</div>