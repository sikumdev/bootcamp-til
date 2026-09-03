---
title: OCR 개념 — PDF를 그림으로 만들어 읽고, 구조까지 되살리기
date: 2026-09-03
tags: [ocr]
---

# OCR 개념 — PDF를 그림으로 만들어 읽고, 구조까지 되살리기

> 원본 코드: [`04_OCR.py`](04_OCR.py)

## 왜 OCR 이 필요한가부터

PDF 에는 두 종류의 글자가 있음. 하나는 `데이터로 들어있는 글자`, 하나는 `그림으로 그려진 글자`.<br>둘은 화면에서 똑같이 보이는데, 코드로 읽으면 결과가 완전히 다름.

<div class="til-code" markdown>
```python
# PDF 안에 글자가 저장되는 두 가지 방식
 ① 텍스트 레이어  "이 위치에 '매출' 이라는 글자를 이 폰트로 그려라"  ← 글자가 데이터로 남음
 ② 이미지          [픽셀 픽셀 픽셀 픽셀 ...]                        ← 글자 모양만 남음

 - ①은 PyPDFLoader 가 그냥 꺼내 읽으면 됨 (복사·붙여넣기 되는 PDF)
 - ②는 꺼낼 게 없음. 사람이 눈으로 읽듯이 `모양을 보고 알아맞혀야` 함 ← 이게 OCR
```
</div>

!!! info "OCR 은 추측임"
    OCR = Optical Character Recognition, `광학 문자 인식`.  
    이름 그대로 `빛(그림)으로 된 문자를 알아보는 것`임. 핵심은 `추측`이라는 점.  
    텍스트 레이어는 정답을 그대로 꺼내는 거고, OCR 은 모양 보고 맞히는 거라 `틀릴 수 있음`.

1순위 텍스트 레이어(PyPDFLoader) — 정확하고 빠름. 있으면 무조건 이걸 씀<br>2순위 OCR — 텍스트 레이어가 없거나 비어 있을 때만 쓰는 `보완책`

!!! question "그런데 왜 굳이 OCR 을?"
    그럼 텍스트 레이어가 있는데 왜 OCR 을 굳이 돌려봤냐 →  
    → 텍스트 레이어가 못 살리는 게  `표의 행·열 구조`임.

## 전체 흐름 — 파이프라인

단계마다 `무엇이 들어가서 무엇이 나오는지`만 잡으면 나머지는 도구 이름일 뿐임.

<div class="til-code" markdown>
```python
 PDF ─① PyPDFLoader ───────→ 글자        (텍스트 레이어가 있으면 여기서 끝)
     │
     └─② PyMuPDF ─→ PNG 이미지 ─③ OCR 엔진 ─→ 글자
                          │
                          └─④ DocLayout-YOLO ─→ 영역 박스들
                                                    │
                                                    ├─ 본문 영역 → OCR
                                                    └─ 표 영역  → ⑤ Table2HTML → 격자 구조
                                                                       │
                                                                       ▼
                                                          ⑥ LangChain Document
```
</div>

!!! info "각 단계가 하는 일"
    OCR 은 `이미지`만 읽음.  
    그래서 ②번(렌더링)이 반드시 앞에 있어야 함. PDF 를 그림 파일로 한번 바꿔주는 단계임.  
    ④번 레이아웃 탐지는 `글자를 읽는 게 아님`. `여기는 제목, 여기는 표` 하고 영역만 나눠줌.  
    내용은 하나도 안 알려줌. 그래서 반드시 OCR 이나 표 파서와 짝을 지어 써야 함.

## 작은 흐름

<div class="til-code" markdown>
```python
PDF → (PyMuPDF) → 이미지 → [ OCR 엔진 ] → 텍스트 → RAG에 넣을 문서 
                            ↑ 여기 자리에 들어갈 수 있는 것
                                - EasyOCR 
                                - pytesseract
                                - PaddleOCR 등
```
</div>

## 렌더링 — PDF를 그림으로 바꾸기

<div class="til-code" markdown>
```python hl_lines="14"
import pymupdf
from pathlib import Path

PDF_PATH = Path("SPRi_AI_Brief_8월호.pdf")
PAGE_NUMBER = 3
OCR_IMAGE_PATH = Path("ocr_page_3.png")

# # PDF 열기 -> pymupdf.Document 클래스
pdf_document = pymupdf.open(str(PDF_PATH))

# 페이지 선택 -> pymupdf.Page 클래스
pdf_page = pdf_document[PAGE_NUMBER - 1]

# get_pixmap() = PDF 페이지(그리기 명령)를 실제 픽셀 이미지로 그리는 것.
pixmap = pdf_page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

# 저장
pixmap.save(str(OCR_IMAGE_PATH))

pdf_document.close()

print(pixmap.width, pixmap.height)      # 1191 1684
print(pdf_page.rect)                    # Rect(0.0, 0.0, 595.27, 841.88)
print(round(OCR_IMAGE_PATH.stat().st_size / 1024, 1))   # 236.6 (KB)
# 배율 대신 DPI 로 줘도 결과가 같음 (PDF 기본이 72 DPI 라서 72 x 2 = 144)
same_pixmap = pdf_page.get_pixmap(dpi=144)
print(same_pixmap.width, same_pixmap.height)    # 1191 1684 — Matrix(2, 2) 와 동일
```
<div class="til-note" data-til-line="14" hidden>`Matrix(2, 2)` 는 가로 해상도 2배, 세로 해상도 2배.</div>
</div>

## OCR 엔진 - pytesseract

`pip install pytesseract` 만으로는 안 돌아감. → 따로 설치 해야함

<div class="til-code" markdown>
```python hl_lines="10 11 12 13 14 15"
import shutil

import pytesseract
from PIL import Image

# shutil.which 는 이 명령어가 컴퓨터에 설치돼 있나 를 찾아주는 함수
tesseract_available = shutil.which("tesseract") is not None


tesseract_text = ""
if tesseract_available:
    tesseract_text = pytesseract.image_to_string(
        Image.open(OCR_IMAGE_PATH),
        lang="kor+eng",
    )

print(len(tesseract_text.strip()))      # 1634
```
<div class="til-note" data-til-line="15" hidden>`image_to_string` = `이미지를 문자열로`. 이름 그대로임<br>`Image.open` 은 PIL 로 이미지를 여는 것. 경로 문자열을 바로 줘도 됨<br>`lang` 은 `어느 나라 글자 모양을 알고 있는 데이터를 쓸지`. `+` 로 합칠 수 있음</div>
</div>

!!! warning "pytesseract 는 심부름꾼임"
    `pytesseract` 는 실제로 글자를 읽지 않음. 컴퓨터에 설치된 `tesseract.exe` 를  
    대신 실행해주고 결과 문자열을 받아오는 심부름꾼일 뿐임.

## OCR 엔진 - EasyOCR

OCR은 사실 `찾기(탐지)` 와 `읽기(인식)` 이렇게 두 단계로 이루어져 있음<br>`찾기(탐지)` 와 `읽기(인식)` 가 따로 돎.

!!! info "탐지와 인식, 2단계"
    1단계 탐지(detection) — 이미지를 훑어서 `여기 글자 있는 것 같다` 싶은 곳을 네모로 표시함.  
    이때는 무슨 글자인지 `전혀 모름`. 글자처럼 생긴 픽셀 덩어리를 감싸기만 함.  
    2단계 인식(recognition) — 그 네모를 하나씩 잘라내서 안의 글자를 읽음.  
    `이건 아마 '매출' 인 것 같고 확신은 0.87` 이런 식으로 나옴. 이 확신이 `confidence`.

<div class="til-code" markdown>
```python hl_lines="7 10 18"
import warnings
warnings.filterwarnings("ignore")


import easyocr

# Reader 를 만드는 순간 딥러닝 모델이 메모리에 올라감. 무거운 작업임
ocr_reader = easyocr.Reader(["ko", "en"], gpu=False, verbose=False)

# ocr_details` 의 개수는 찾아낸 네모의 개수(bbox)임.
ocr_details = ocr_reader.readtext(str(OCR_IMAGE_PATH), detail=1)

for box, text, confidence in ocr_details[:3]:
    print(f"{confidence:.3f} | {text}")

ocr_lines = [text for _, text, _ in ocr_details]

# 글자 목록을 줄바꿈으로 이어붙여 문자열 하나로 만듦. 
ocr_text = "\n".join(ocr_lines)

# 확신도가 낮은 것만 골라냄. 
low_confidence_lines = [
    (text, confidence)
    for _, text, confidence in ocr_details
    if confidence < 0.5
]

print(len(ocr_lines), len(ocr_text), len(low_confidence_lines))   # 115 1335 13
```
<div class="til-note" data-til-line="7" hidden>그래서 `한 번 만들어서 계속 재사용`해야 함. 반복문 안에서 만들면 안 됨</div>
<div class="til-note" data-til-line="10" hidden>`detail=1` → `(위치(bbox), 텍스트(text), 신뢰도(confidence))` 튜플 목록<br>`detail=0` → 글자 문자열만 든 목록. 좌표·확신도가 필요 없으면 이게 편함</div>
<div class="til-note" data-til-line="18" hidden>Document 에 넣으려면 문자열이어야 함</div>
</div>

!!! example "실행 결과"
    실행 결과 → 네모박스 `115개`, 이어붙인 글자 `1335자`, 확신도 0.5 미만이 `13개`.  
    낮은 것들을 보니 `정`, `벌`, `겁`, `삼` 처럼 한 글자짜리가 많았음.  
    원본을 보면 그 자리는 글자가 아니라 `아이콘·기호`였음. 글자처럼 생겨서 잘못 잡은 것.

<div class="til-code" markdown>
```python hl_lines="4 5"
sensitive_results = ocr_reader.readtext(
    str(OCR_IMAGE_PATH),
    detail=1,
    text_threshold=0.6,  # 기본값 0.7
    low_text=0.3,        # 기본값 0.4
)

# 박스 갯수가 105 개에서 103 개로 오히려 줄었음 
print(len(ocr_details), len(sensitive_results))

 
confidences = [confidence for _, _, confidence in sensitive_results]
sensitive_average_confidence = sum(confidences) / len(confidences)
print(round(sensitive_average_confidence, 3))       # 0.758
```
<div class="til-note" data-til-line="4" hidden>`text_threshold` → 텍스트로 인정할 `강한 픽셀`의 기준</div>
<div class="til-note" data-til-line="5" hidden>`low_text` → 주변의 `약한 후보`까지 끌어다 이어붙일 때 쓰는 기준</div>
</div>

!!! question "기준을 낮췄는데 왜 개수가 줄었나"
    기준을 `낮췄는데` 탐지 개수가 `105 → 103` 으로 줄었음.  
    `low_text` → 글자 확률 지도를 흑백으로 자르는 문턱임. 낮추면 글자로 치는 영역이 `넓어`짐.  
    넓어진 덩어리들이 서로 붙어버려서 박스가 `합쳐`짐 → 개수 `감소`  
    `text_threshold` → 덩어리 중 확률 낮은 걸 `버리는` 문턱임. 낮추면 더 `살아남`음 → 개수 `증가`  
    이번엔 `합쳐지는 효과`가 `살아남는 효과`보다 커서 순수하게 2개가 줄어든 것임.  
    박스가 합쳐지면 개수는 줄지만 한 박스에 담기는 글자는 늘어남.  
    개수 대신 `총 글자 수`와 `평균 확신도`를 같이 봐야 함.  
    `paragraph=True` 도 비슷하게 가까운 박스들을 문단으로 묶어줌.  
    다만 `묶는 순서가 실제 읽기 순서와 항상 같지는 않음`.

## OCR 엔진 - OCPaddleOCR

같은 모델을 CPU와 GPU에서 돌려보기<br>엔진을 바꾸는 실험이 아니라, `똑같은 걸 어디서 계산하느냐`만 바꾸는 실험임.

<div class="til-code" markdown>
```python hl_lines="16"
import time

from paddleocr import PaddleOCR

PADDLE_COMMON_OPTIONS = {
    "lang": "korean",
    "use_textline_orientation": False,
    "use_doc_orientation_classify": False,
    "use_doc_unwarping": False,
    "text_detection_model_name": "PP-OCRv5_mobile_det",
    "text_recognition_model_name": "korean_PP-OCRv5_mobile_rec",
}


def run_first_and_warmed(pipeline, image_path):
    # 1회차.
    first_started_at = time.perf_counter()
    first_results = list(pipeline.predict(str(image_path)))
    first_seconds = time.perf_counter() - first_started_at

    # 2회차. 똑같은 걸 한 번 더 돌림. 이게 `워밍업 후` 시간
    warmed_started_at = time.perf_counter()
    warmed_results = list(pipeline.predict(str(image_path)))
    warmed_seconds = time.perf_counter() - warmed_started_at

    return {
        "first_results": first_results, "warmed_results": warmed_results,
        "first_seconds": first_seconds, "warmed_seconds": warmed_seconds,
    }
```
<div class="til-note" data-til-line="16" hidden>참고) perf_counter 는 시간 재기 전용 시계.</div>
</div>

!!! info "워밍업 — 왜 두 번 재나"
    왜 두 번 재냐  
    → 1회차에는 `모델 가중치를 장치로 올리는 시간`, `계산 커널 준비` 같은 준비 비용이 섞임.  
    → 2회차는 준비가 끝난 상태라 `순수한 추론 시간`에 가까움. 비교는 2회차로 해야 공평함.  
    `워밍업` 이라는 말이 그래서 나옴. 운동 전 몸 푸는 것과 같은 뜻임.

<div class="til-code" markdown>
```python hl_lines="4 12 13"
cpu_started_at = time.perf_counter()
paddle_cpu_pipeline = PaddleOCR(
    device="cpu",
    enable_mkldnn=False,
    **PADDLE_COMMON_OPTIONS,
)

cpu_initialization_seconds = time.perf_counter() - cpu_started_at

cpu_benchmark = run_first_and_warmed(paddle_cpu_pipeline, OCR_IMAGE_PATH)

paddle_gpu_pipeline = PaddleOCR(device="gpu", **PADDLE_COMMON_OPTIONS)
gpu_benchmark = run_first_and_warmed(paddle_gpu_pipeline, OCR_IMAGE_PATH)

gpu_speedup = cpu_benchmark["warmed_seconds"] / gpu_benchmark["warmed_seconds"]
print(round(gpu_speedup, 2))        # 7.32
```
<div class="til-note" data-til-line="4" hidden>`enable_mkldnn=False` 는 인텔 CPU 가속을 끄는 것. 켜면 CPU 가 빨라져 비교가 흐려짐</div>
<div class="til-note" data-til-line="13" hidden>★ 바뀐 건 `device` 한 글자뿐임. 모델도 이미지도 옵션도 전부 같음</div>
</div>

## 4가지 방법 비교

같은 pdf 3쪽을 아래와 같이 4가지 방법으로 읽어서 글자 수와 앞부분을 나란히 봄.

!!! abstract "방법별 비교"
    | 방법 | 글자 수 | 앞부분 미리보기에서 보이는 특징 |  
    |---|---|---|  
    | PyPDFLoader (텍스트 레이어) | 1459 | 오탈자 0. 대신 `1 정 책 ･ 법 제` 처럼 세로글자가 흩어짐 |  
    | pytesseract | 1634 | `AI` 를 `Al` 로, `비교` 를 `4D` 로 틀림 |  
    | EasyOCR | 1335 | `1.1` 을 `1.7` 로 틀림. 아이콘을 `정`, `벌` 로 잘못 읽음 |  
    | PaddleOCR CPU | 1401 | `AI` 를 `A` 로 틀림. 대신 `정책·법제` 를 제대로 붙여 읽음 |  
    | PaddleOCR GPU | 1400 | CPU 와 사실상 동일 |  
    
    결론은 `텍스트 레이어가 있으면 그냥 그걸 써라`임. 글자 수가 많다고 좋은 게 아님.  
    pytesseract 가 1634자로 제일 많았지만 그건 오탈자와 잡음까지 포함한 숫자임.  
    그래서 OCR 품질은 `글자 수`가 아니라 `확신도 분포`와 `눈으로 대조`로 봐야 함.  
    반대로 텍스트 레이어의 약점도 보였음. `1 정 책 ･ 법 제` 처럼 세로로 배치된 글자가  
    한 글자씩 떨어져 나옴. PaddleOCR 은 같은 부분을 `1 정책·법제` 로 붙여 읽었음.  
    즉 텍스트 레이어는 `글자는 정확한데 배치를 모르고`, OCR 은 `배치는 보는데 글자를 틀림`.

## 레이아웃 탐지 — 페이지 전체를 한 번에 읽으면 안 되는 이유

제목·본문·표를 구분하지 않고 통째로 OCR 하면 순서와 소속이 뒤섞임.

!!! question "왜 영역을 먼저 나누나"
    왜 필요한가?  
    표가 4개나 있는 페이지를 통째로 OCR 하면 글자는 다 나오는데  
    `이 숫자가 어느 표의 것인지`, `이 문장이 제목인지 본문인지`를 알 수 없음.  
    그래서 순서를 바꿈. `영역을 먼저 나누고, 영역마다 따로 처리`함.

## DocLayout-YOLO로 문서 구조 분석

위에서 말했던 레이아웃 탐지를 할 수 있는 모델이 `DocLayout-YOLO`임

<div class="til-code" markdown>
```python hl_lines="8 11 12 17 19 22"
PDF → 이미지 → [레이아웃 분석] → 영역별로 잘라내기 → 영역마다 OCR → 구조 있는 텍스트
                  ↑ 여기가 DocLayout-YOLO
from doclayout_yolo import YOLOv10

# 약 39MB 짜리 모델 파일. 문서 이미지에서 영역을 찾도록 학습된 것
layout_model = YOLOv10("doclayout_yolo_docstructbench_imgsz1024.pt")

# predict()는 이미지를 여러 장 한꺼번에 받을 수 있음 → 결과가 항상 목록임
layout_results = layout_model.predict(
    str(OCR_IMAGE_PATH),
    imgsz=640,
    conf=0.3,
    device="cpu",
)


layout_result = layout_results[0]

print(len(layout_result.boxes))     # 22


# 이 모델이 어떤 걸 구분 할줄 아는지 목록 리스트
print(layout_result.names)      
```
<div class="til-note" data-til-line="8" hidden>model.predict(["a.png", "b.png", "c.png"])   # 결과 3개 → [결과, 결과, 결과]<br>model.predict("a.png")                       # 결과 1개 → [결과]</div>
<div class="til-note" data-til-line="11" hidden>`imgsz=640` → 모델에 넣기 전에 이미지를 640 크기로 맞춤. 키우면 작은 영역을 잘 찾지만 느려짐</div>
<div class="til-note" data-til-line="12" hidden>`conf=0.3` → 확신도 0.3 미만인 후보는 버림. 올리면 확실한 것만 남고 개수가 줄어듦</div>
<div class="til-note" data-til-line="17" hidden>practice_layout_result = practice_layout_results[0]   # 이미지 1장의 결과</div>
<div class="til-note" data-til-line="19" hidden>cls: tensor([5.])<br>xyxy: tensor([[ 92.4996, 315.7383, 777.6818, 573.9485]])<br>conf: tensor([0.9653])</div>
<div class="til-note" data-til-line="22" hidden>{0:'title', 1:'plain text', 2:'abandon', 3:'figure', 4:'figure_caption',<br>5:'table', 6:'table_caption', 7:'table_footnote', 8:'isolate_formula', 9:'formula_caption'}</div>
</div>

!!! note "boxes 에서 꺼내 쓸 3가지"
    `boxes` 하나가 들고 있는 정보 중 알아야 할  3가지  
    `box.xyxy[0]` → 어디에 있나. `[왼쪽x, 위y, 오른쪽x, 아래y]` 네 개 숫자  
    `box.cls[0]` → 무엇인가. 숫자 하나(예: `5.`)  
    `box.conf[0]` → 얼마나 확신하나. 0~1 사이 값  
    `cls` 가 왜 숫자냐 → 모델은 글자를 모르고 번호로만 답함. 그 번호를 이름으로 바꾸는 게  
    그 번호를 이름으로 바꾸는 게 `names` 딕셔너리임.  
    `names[5]`는 값이 `'table'`임.  
    그리고 `box.cls` 는 `tensor([5.])` 라는 목록 비슷한 것이라 `int(box.cls[0])` 로 숫자를 꺼냄.

## 표 구조화 — 격자를 되살리는 이유

표를 통째로 OCR 하면 글자는 다 나오는데 `어느 칸`인지가 사라짐.

<div class="til-code" markdown>
```python
 표를 그냥 OCR 에 넣으면 이렇게 나옴
   ["구분", "2024년", "2025년", "매출", "120", "150", "영업이익", "20", "35"]

 글자는 다 읽었는데 어느 숫자가 어느 칸인지 모름.
 이 상태로 RAG 에 넣으면 "2025년 영업이익이 얼마야?" 에 답할 수 없음.

 그래서 순서를 바꿈 → 구조를 먼저 찾고, 칸마다 따로 OCR 을 돌림

   행 경계:  ─────────      열 경계:  │   │   │
                                        ↓ 교차시키면
                                     ┌─┬─┬─┐
                                     ├─┼─┼─┤     ← 이 칸 하나하나가 `셀`
                                     └─┴─┴─┘
```
</div>

!!! tip "구조를 먼저, OCR 은 나중에"
    `구조를 먼저, OCR 은 나중에`.  
    표 전체를 읽으면 글자만 남지만, 격자를 먼저 만들고 칸 안에서만 읽으면  
    `2행 3열은 35` 처럼 `자리를 아는 글자`가 나옴.

<div class="til-code" markdown>
```python hl_lines="21 41 53 77"
import cv2

TABLE_OUTPUT_DIR = Path("result")
TABLE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# OpenCV 로 이미지를 읽음. 결과는 그림이 아니라 숫자 격자(numpy 배열) 임
layout_image = cv2.imread(str(OCR_IMAGE_PATH))
table_image_paths = []

for box in layout_result.boxes:

    # 레이아웃 탐지 결과가 table(표)인 것만 걸러내기
    class_name = layout_result.names[int(box.cls[0])]
    if class_name != "table":
        continue
   
    # 배열을 자를 때 쓰는 인덱스는 정수여야 함. 소수로 자르면 TypeError
    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

    # 여기가 이미지를 오려 내는 부분
    cropped_table = layout_image[y1:y2, x1:x2]

    table_path = TABLE_OUTPUT_DIR / f"table_{len(table_image_paths) + 1}.jpg"
    cv2.imwrite(str(table_path), cropped_table)
    table_image_paths.append(table_path)

print(len(table_image_paths))       # 4
import sys
import subprocess

TABLE2HTML_REPO = Path("table2html")

if not TABLE2HTML_REPO.exists():
    subprocess.run(
        ["git", "clone", "https://github.com/jayll1303/table2html.git",
         str(TABLE2HTML_REPO)],
        check=True,
    )

sys.path.insert(0, str(TABLE2HTML_REPO.resolve()))

import table2html.main as table2html_main
from table2html.source.ocr_engine import OCREngine

# 원본 클래스를 물려받아 `device="cpu"` 로 고정한 새 클래스를 만듦
class CPUOCREngine(OCREngine):
    def __init__(self):
        super().__init__(device="cpu")



table2html_main.OCREngine = CPUOCREngine

# 반드시 패치 `다음`에 import 해야 함. 순서가 바뀌면 원본이 먼저 로딩돼서 소용없음
from table2html import Table2HTML

def make_config(model_name, task=None):
    config = {
        "model_path": str(TABLE2HTML_REPO / f"table2html/models/{model_name}.pt"),
        "confidence_threshold": 0.25,
        "iou_threshold": 0.7,
    }
    if task:
        config["task"] = task
    return config


# 모델이 셋인 게 핵심임. 표 전체 / 행 경계 / 열 경계를 각각 찾음
table_parser = Table2HTML(
    make_config("table_detection"),
    make_config("row_detection", task="detect"),
    make_config("column_detection", task="detect"),
)
first_table_image = cv2.imread(str(table_image_paths[0]))

# 이 한 줄 안에서 `표 탐지 → 행 탐지 → 열 탐지 → 셀마다 OCR` 이 전부 일어남
table_data = table_parser.StructureDetect(first_table_image)

print(type(table_data))         # <class 'dict'>
print(table_data.keys())        # 어떤 키가 있는지부터 확인

# table_data 구조
```
<div class="til-note" data-til-line="21" hidden>`y 먼저, x 나중` 순서에 주의<br>numpy 배열은 `[행, 열]` = `[세로, 가로]` 순서라서 그럼</div>
<div class="til-note" data-til-line="41" hidden>`sys.path` 는 파이썬이 `import 할 때 뒤지는 폴더 목록`임<br>여기에 내려받은 폴더를 넣어야 `import table2html` 이 됨<br>{<br>'html': '<table><tr><td>구분</td><td>2024년</td><td>2025년</td></tr><tr><td>매출</td>...',<br>'num_rows': 5,<br>'num_cols': 3,<br>'cells': [ {'bbox': [10, 8, 120, 45], 'text': '구분'},<br>{'bbox': [120, 8, 240, 45], 'text': '2024년'},<br>...  ]<br>}</div>
<div class="til-note" data-til-line="53" hidden>라이브러리 안의 이름을 내가 만든 클래스로 갈아끼움. 이걸 `몽키 패칭` 이라고 함</div>
<div class="til-note" data-til-line="77" hidden>셀이 20개면 OCR 을 20번 하는 셈이라 CPU 에서는 수십 초 걸릴 수 있음</div>
</div>

!!! note "StructureDetect 반환값"
    `StructureDetect` 의 반환은 딕셔너리이고 대략 이런 모양임.  

    | 키 | 내용 |  
    |---|---|  
    | `html` | `<table><tr><td>` 형태의 문자열 |  
    | `num_rows` | 복원한 행 개수 |  
    | `num_cols` | 복원한 열 개수 |  
    | `cells` | 셀 정보 목록 (좌표 + 텍스트) |

<div class="til-code" markdown>
```python hl_lines="8 9 10 11"
# 딕셔너리를 통째로 print 하면 한 줄로 쏟아져서 못 읽음. 나눠서 보는 게 나음

# 1단계 — 어떤 키가 있는지만
print(table_data.keys())

# 2단계 — 큰 값은 길이만, 작은 값은 그대로
for key, value in table_data.items():
    if isinstance(value, (list, str)) and len(value) > 100:
        print(f"{key}: {type(value).__name__}, 길이 {len(value)}")
    else:
        print(f"{key}: {value}")

# 3단계 — 셀 하나만 자세히
first_cell = table_data["cells"][0]
print(type(first_cell), first_cell)
if isinstance(first_cell, dict):
    print(first_cell.keys())

# 보기 좋게 출력하기
from pprint import pprint
pprint(table_data["cells"][:3])
```
<div class="til-note" data-til-line="11" hidden>`html` 과 `cells` 는 길어서 화면을 다 잡아먹음. 길이만 보고 넘어감</div>
</div>

!!! tip "모르는 결과를 뜯어보는 3단계"
    ★모르는 라이브러리 결과를 만났을 때 이 3단계가 제일 빠른 것 같음.  
    `type()` → `keys()` → 원소 하나만 자세히.

## OCR 결과를 Document 로 만들기

어떤 방법으로 읽었든 마지막에는 같은 그릇에 담아야 뒤 단계가 공통으로 처리함.

<div class="til-code" markdown>
```python
from langchain_core.documents import Document

ocr_document = Document(
    page_content=ocr_text.strip(),
    metadata={
        "source": str(PDF_PATH),
        "page": PAGE_NUMBER - 1,
        "page_number": PAGE_NUMBER,
        "loader": "EasyOCR",
        "image_path": str(OCR_IMAGE_PATH),
    },
)
```
</div>

!!! info "왜 Document 로 담나"
    왜 굳이 Document 로 바꾸냐 → 분할기·벡터저장소·retriever 가 전부 `Document` 를 주고받게 만들어져 있음.

## 자동 선택 파이프라인

텍스트 레이어가 충분하면 그대로 쓰고, 부족할 때만 OCR 로 넘어가는 함수.

<div class="til-code" markdown>
```python hl_lines="27 28 33"
import numpy as np

from langchain_community.document_loaders import PyPDFLoader


def load_pdf_with_ocr(pdf_path, reader, minimum_chars_per_page):
    loaded_pages = PyPDFLoader(str(pdf_path)).load()
    page_lengths = [len(page.page_content.strip()) for page in loaded_pages]

    # 먼저 텍스트 레이어로 읽어보고 페이지당 평균 글자 수를 구함
    average_characters = sum(page_lengths) / len(page_lengths)
    
    # 기준을 넘으면 OCR 을 아예 안 하고 끝냄. 느린 작업을 건너뛰는 게 목적임
    if average_characters >= minimum_chars_per_page:
        return {"documents": loaded_pages, "mode": "text"}

    pdf_document = pymupdf.open(str(pdf_path))
    ocr_documents = []

    try:
        for page_index, pdf_page in enumerate(pdf_document):
            page_pixmap = pdf_page.get_pixmap(matrix=pymupdf.Matrix(2, 2))

            # 파일로 저장하지 않고 `PNG 파일의 내용 자체`를 바이트로 받음
            image_bytes = page_pixmap.tobytes("png")

            image_array = np.frombuffer(image_bytes, dtype=np.uint8)
            rendered_image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

            ocr_paragraphs = reader.readtext(
                rendered_image,
                detail=0,
                paragraph=True,   # 가까운 네모들을 문단으로 묶어줌
            )
            

            ocr_documents.append(
                Document(
                    page_content="\n".join(ocr_paragraphs),
                    metadata={
                        "source": str(pdf_path),
                        "page": page_index,
                        "page_number": page_index + 1,
                        "loader": "EasyOCR",
                    },
                )
            )
    finally:
        pdf_document.close()


    return {"documents": ocr_documents, "mode": "ocr"}
```
<div class="til-note" data-til-line="27" hidden>바이트를 numpy 배열로. 아직은 1차원으로 쭉 늘어선 상태</div>
<div class="til-note" data-til-line="28" hidden>★ 그 바이트를 해석해서 `(세로, 가로, 색)` 3차원 이미지로 복원</div>
<div class="til-note" data-til-line="33" hidden>안 묶으면 한 문장이 여러 조각으로 쪼개져서 검색에 불리함</div>
</div>

!!! example "3단 변환을 직접 찍어봄"
    `tobytes → frombuffer → imdecode` 3단 변환이 뭘 하는 건지 직접 찍어서 확인함.  
    1) `tobytes("png")` → `bytes` 277277바이트. PNG 파일에 들어갈 내용 그 자체임  
    2) `np.frombuffer` → `(277277,)` 1차원 배열. 아직 그냥 숫자 나열임  
    3) `cv2.imdecode` → `(1684, 1191, 3)`. 드디어 세로x가로x색 3차원 이미지가 됨  
    그럼 왜 파일을 안 거치냐 → 29쪽짜리면 PNG 파일 29개가 디스크에 쌓임.  
    메모리에서 바로 넘기면 그 과정이 없음. `디스크를 안 건드린다`는 게 유일한 차이임.

!!! warning "reader 는 밖에서 만들어 넘길 것"
    `reader` 를 인자로 받는 게 중요함. 함수 안에서 `easyocr.Reader(...)` 를 만들면  
    호출할 때마다 딥러닝 모델을 다시 로드함. 밖에서 한 번 만들어 넘겨야 함.

## 한 장 정리

도구 이름 말고 `언제 무엇을 쓰는지`만 남기면 됨.

!!! abstract "언제 무엇을 쓸까"
    | 상황 | 쓸 것 | 이유 |  
    |---|---|---|  
    | 복사·붙여넣기 되는 PDF | PyPDFLoader | 정확하고 빠름. 1순위 |  
    | 스캔본·이미지 PDF | PyMuPDF 렌더링 → OCR | 텍스트 레이어가 없어서 |  
    | 빠른 기준선이 필요할 때 | pytesseract | 가볍지만 OS 설치가 따로 필요 |  
    | 좌표·확신도가 필요할 때 | EasyOCR | 네모·글자·확신도를 같이 줌 |  
    | 한국어를 대량으로 | PaddleOCR + GPU | 워밍업 기준 7배 이상 빨랐음 |  
    | 제목·본문·표를 나눠야 할 때 | DocLayout-YOLO | 영역만 찾아줌, 글자는 안 읽음 |  
    | 표의 행·열을 살려야 할 때 | Table2HTML | 구조를 먼저 찾고 칸마다 OCR |