"""
title: PDF 보고서 RAG 
tags: [rag]
"""

#==  PyPDFLoader — PDF 1장 = Document 1개
#> 로더가 페이지마다 `Document` 객체를 하나씩 만들고, 본문(page_content)과 출처 정보(metadata)를 같이 넣어줌.

# --8<-- [start:loader]
from langchain_community.document_loaders import PyPDFLoader

# 반환은 `list[Document]`. 29쪽짜리 PDF 면 원소가 29개
loader = PyPDFLoader(str(PDF_PATH))
pages = loader.load()

print(len(pages))                       # 29

# 메타 데이터는 딕셔너리 형태이고 그 안에 키 값 확인 하기
#(1)> author, creationdate, creator, moddate, page, page_label,
#(1)> producer, source, title, total_pages
print(sorted(pages[0].metadata.keys()))

print(pages[0].metadata["page"])        # 0 -> 페이지는 0부터 시작
print(pages[0].metadata["page_label"])  # '1'
print(pages[0].metadata["total_pages"]) # 29
# --8<-- [end:loader]


#== 분할 — 페이지 경계에서는 겹침이 절대 안 생김
#> `split_documents(pages)` 는 페이지 `Document` 를 하나씩 따로 자름. 

# --8<-- [start:split]
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 분할기가 문단 → 줄 → 공백 → 글자 순으로 자를 자리를 찾음
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=150,
)
docs = splitter.split_documents(pages)

print(len(pages), len(docs))            # 29 73

# 원본 페이지·출처가 청크마다 그대로 복사됨. 이게 유지돼야 출처 표시가 가능함
print(docs[30].metadata["page"] + 1)    # 13
print(Path(docs[30].metadata["source"]).name)
# --8<-- [end:split]

#! `chunk_overlap=150` 을 줬는데 `overlap_docs[30]` 끝과 `[31]` 시작이 하나도 안 겹쳤음.
#! 확인 해보니 두 청크가 `서로 다른 페이지`에서 나온 것이었음.
#! 겹치지 않았던 이유는 `split_documents` 가 `Document` 를 하나씩 독립적으로 자르기 때문임.
#! 앞 페이지의 꼬리를 다음 페이지 청크에 붙일 방법 자체가 없음.
#! 그래서 문장이 페이지를 넘어가면 그 문맥은 `chunk_overlap` 으로는 못 살림.


#== Chroma 두 가지 생성법과 `ids` 의 진짜 쓸모
#> 생성자로 빈 저장소를 만들고 `add_documents` 로 넣는 방식. `ids` 를 주면 재실행이 안전해짐.

# --8<-- [start:store]
vectorstore = Chroma(
    collection_name="ai_brief_minimal_rag",
    embedding_function=embedding,
)

# `chunk-0000`, `chunk-0001` ... 형태. 자리수를 맞춰야 정렬이 어긋나지 않음
chunk_ids = [f"chunk-{index:04d}" for index in range(len(docs))]

# 같은 ids 로 다시 넣으면 '추가' 가 아니라 '덮어쓰기'가 됨
vectorstore.add_documents(docs, ids=chunk_ids)

print(len(docs), vectorstore._collection.count())   # 73 73
# --8<-- [end:store]


#! `add_documents(docs, ids=ids)` 두 번 → count `5` → `5` (안 늘어남, upsert)
#! `add_documents(docs)` (ids 없이) 두 번 → count `5` → `10` (그대로 누적됨)

#!  `생성자 VS 클래스 메서드`
#! `Chroma(collection_name=..., embedding_function=...)` — 생성자
#! `Chroma.from_documents(documents, embedding=..., ids=..., collection_name=...)` — 클래스 메서드


#== 검색 — 거리를 같이 봐야 문서 밖 질문이 보임
#> `similarity_search` 는 문서만, `similarity_search_with_score` 는 거리까지 같이 줌.

# --8<-- [start:search]
query = "앤트로픽이 새로 출시한 Claude Opus 5는 어떤 모델인가요?"

# 반환은 `(Document, 거리)` 튜플의 목록. 거리는 `float`
hits_with_score = vectorstore.similarity_search_with_score(query, k=3)

# 거리는 작을 수록 질문 벡터에 가까움
for rank, (hit, distance) in enumerate(hits_with_score, start=1):
    print(f"{rank}위 | 거리 {distance:.4f} | PDF {hit.metadata['page'] + 1}쪽")


# 거리로 문서 밖 질문을 걸러내고 싶으면 threshold retriever 를 쓰면 됨
#(3)> 기준 미달이면 결과 수가 `k` 보다 적게 나옴. 아예 0개일 수도 있음
threshold_retriever = vectorstore.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"k": 3, "score_threshold": 0.5},
)
# --8<-- [end:search]


#==  답변 생성 — system 에 규칙, human 에 질문
#> `from_messages` 로 역할을 나눠서 프롬프트를 만듦. 출처 표기 규칙은 system 에 넣음.

# --8<-- [start:prompt]
from langchain_core.prompts import ChatPromptTemplate

rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "제공된 문서만 사용해 한국어로 답하세요. "
        "답변의 각 핵심 내용 뒤에 [PDF n쪽] 형식으로 출처를 표시하세요. "
        "문서에서 근거를 찾지 못하면 '문서에서 찾을 수 없습니다'라고 답하세요.\n\n"
        "[문서]\n{context}",
    ),
    ("human", "{question}"),
])


messages = rag_prompt.format_messages(context="근거", question="질문")
print(len(messages), [type(m).__name__ for m in messages])
#(2)> 실측 → `2 ['SystemMessage', 'HumanMessage']`
print(sorted(rag_prompt.input_variables))   # ['context', 'question']
#(3)> ★ 변수명이 `input` 이 아니라 `question` 임. 앞 노트의 체인 방식과 다름
# --8<-- [end:prompt]

#! `from_template` 은 `HumanMessage` 하나만 만들고, `from_messages` 는 역할별로 여러 개를 만듦.
#! `from_messages` 로 system+human 을 주니 메시지가 `2개` 나왔음.
#! 출처 표기 같은 `지시`는 system 에, 사용자가 실제로 물은 것은 human 에 넣는 게 맞음.


#== 검색·문맥·생성을 함수 3개로 쪼개기
#> 체인을 안 쓰고 직접 조립함. 쪼개놔야 어디서 틀렸는지 짚을 수 있음.

# --8<-- [start:pipeline]
def retrieve(question: str, k: int = 3):
    return vectorstore.similarity_search(question, k=k)
    


def format_context(documents) -> str:
    sections = []
    for document in documents:
        pdf_page = document.metadata["page"] + 1
        # 본문 앞에 `[PDF n쪽]` 을 직접 붙임. 이걸 해야 LLM 이 출처를 따라 쓸 수 있음
        sections.append(f"[PDF {pdf_page}쪽]\n{document.page_content}")
    return "\n\n".join(sections)


def answer_with_sources(question: str, k: int = 3) -> dict:
    documents = retrieve(question, k=k)
    response = llm.invoke(
        rag_prompt.format_messages(
            context=format_context(documents),
            question=question,
        )
    ).content
    sources = [
        {
            "pdf_page": document.metadata["page"] + 1,
            "source": Path(document.metadata["source"]).name,
            "preview": document.page_content[:120].replace("\n", " "),
        }
        for document in documents
    ]
    return {"question": question, "answer": response, "sources": sources}
    


def run_minimal_rag(question: str, k: int = 3) -> dict:
    documents = vectorstore.similarity_search(question, k=k)
    response = llm.invoke(
        rag_prompt.format_messages(
            context=format_context(documents),
            question=question,
        )
    ).content
    # set 으로 묶어서 중복 페이지를 없앰. 한 페이지에서 청크가 여러 개 나올 수 있음
    source_pages = sorted({d.metadata["page"] + 1 for d in documents})
    return {"question": question, "answer": response, "source_pages": source_pages}
# --8<-- [end:pipeline]



#== 검색과 생성을 나눠서 점검하기
#> 답이 틀렸을 때 검색이 문제인지 생성이 문제인지 먼저 갈라야 함.

# --8<-- [start:eval]
retrieval_cases = [
    {"question": "Claude Opus 5의 특징은 무엇인가요?", "expected_pages": {12, 13}},
    {"question": "GPT-5.6 제품군의 특징은 무엇인가요?", "expected_pages": {15}},
]


for case in retrieval_cases:
    found_pages = {d.metadata["page"] + 1 for d in retrieve(case["question"], k=3)}
    status = "통과" if found_pages & case["expected_pages"] else "확인 필요"
    print(status, sorted(found_pages), sorted(case["expected_pages"]))

# 생성 전에 문맥만 눈으로 보는 절차
inspection_docs = retrieve("Claude Opus 5의 특징은 무엇인가요?", k=3)
print(format_context(inspection_docs)[:2500])
# --8<-- [end:eval]

#== 정리

#! 1) `format_context` 를 찍어서 정답 문장이 문맥에 있는지 본다
#! 2) 없으면 `chunk_size` 와 `k` 를 건드린다 (검색 문제)
#! 3) 있는데 답이 틀리면 프롬프트를 고친다 (생성 문제)
#! 모델을 바꾸는 건 마지막임.

