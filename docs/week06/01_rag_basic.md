---
title: LangChain RAG — 최소 파이프라인
date: 2026-09-01
tags: [rag]
---

# LangChain RAG — 최소 파이프라인

> 원본 코드: [`01_rag_basic.py`](01_rag_basic.py)

## RAG 최소 파이프라인

로드→분할→임베딩→저장→검색→생성

## RAG 가 뭘 해결하는가

LLM 혼자 답할 때 생기는 환각·최신성·출처 문제를, 프롬프트에 근거 문서를 끼워 넣어서 메우는 방식.<br>모델을 건드리는 게 아니라 입력 문자열을 바꾸는 것뿐임.

## 파이프라인 6단계와 담당 객체

각 단계가 어떤 타입을 받아서 어떤 타입을 뱉는지 확인

!!! warning
     | 단계 | 담당 클래스 | 입력 → 출력 |
     |---|---|---|
     | 로드 | `TextLoader` | 파일 경로 → `list[Document]` |
     | 분할 | `RecursiveCharacterTextSplitter` | `list[Document]` → `list[Document]` (더 잘게) |
     | 임베딩 | `OpenAIEmbeddings` | `str` → `list[float]` |
     | 저장 | `Chroma` | `list[Document]` + 임베딩 객체 → 벡터 저장소 |
     | 검색 | `VectorStoreRetriever` | `str` 질문 → `list[Document]` |
     | 생성 | `ChatOpenAI` | 프롬프트 → `AIMessage` |

    로드~저장까지는 문서가 바뀔 때만 한 번 도는 배치 작업이고,  
    검색~생성은 사용자가 질문할 때마다 매번 도는 요청 처리임.

## Document — page_content + metadata

Document는 검색의 최소 단위.<br>본문 문자열(page_content)과 출처 딕셔너리(metadata)를 한 덩어리로 묶은 클래스임.

<div class="til-code" markdown>
```python
from langchain_core.documents import Document

intro_documents = [
    Document(
        page_content=(
            "RAG는 질문과 관련된 문서를 검색하고, 검색된 내용을 LLM의 문맥으로 전달합니다. "
            "문서 전체가 아니라 질문에 필요한 부분만 사용하므로 근거 중심 답변을 만들 수 있습니다."
        ),
        metadata={"source": "rag_intro"},
    ),
    Document(
        page_content=(
            "임베딩은 텍스트의 의미를 숫자 벡터로 변환합니다. "
            "표현이 달라도 의미가 비슷한 문장은 벡터 공간에서 가까운 위치에 놓입니다."
        ),
        metadata={"source": "embedding_intro"},
    ),
    Document(
        page_content=(
            "벡터 저장소는 문서 벡터를 저장하고 질문 벡터와 가까운 문서를 검색합니다. "
            "Chroma는 파이썬에서 사용할 수 있는 벡터 저장소입니다."
        ),
        metadata={"source": "vectorstore_intro"},
    ),
]

print(len(intro_documents[0].page_content))   # 97
print(intro_documents[0].metadata["source"])  # rag_intro
```
</div>

!!! warning
    임베딩되는 건 `page_content` 뿐이고 `metadata` 는 벡터에 안 들어감.  
    그래서 메타데이터에 적은 단어로는 유사도 검색이 안 됨.  
    출처로 걸러내고 싶으면 검색 시 `filter` 를 따로 줘야 하는 구조임.

## TextSplitter — 검색 단위로 자르기

문서 전체를 통째로 프롬프트에 넣지 않으려고 잘게 쪼갬. 쪼개는 기준이 검색 품질을 결정함.

<div class="til-code" markdown>
```python hl_lines="3"
from langchain_text_splitters import CharacterTextSplitter

# 동작 순서는  `separator` → `chunk_size` → `chunk_overlap` 임
intro_splitter = CharacterTextSplitter(
    chunk_size=60,
    chunk_overlap=15,
    separator="",
)


intro_chunks = intro_splitter.split_documents(intro_documents)

print(len(intro_chunks))                                # 6
print([len(d.page_content) for d in intro_chunks])      # [60, 52, 59, 24, 59, 30]
print(intro_chunks[0].page_content[-15:])               
print(intro_chunks[1].page_content[:15])                
print(intro_chunks[0].metadata)                         # {'source': 'rag_intro'}
```
<div class="til-note" data-til-line="3" hidden>`separator=""` 라서 분할기가 텍스트를 글자 하나하나로 먼저 쪼갬<br>쪼갠 글자들을 `60` 자를 넘지 않는 선까지 앞에서부터 다시 붙임<br>청크를 하나 끊고 나서, 뒤쪽 `15` 자만 남기고 다음 청크를 이어서 만듦</div>
</div>

!!! warning
    청크 6개, 길이는 `[60, 52, 59, 24, 59, 30]` 이었음.  
    여기서 헷갈렸던 것 → `chunk_size=60` 인데 왜 청크들의 크기가 다 60이 아닌가?  
    분할기가 60자를 채운 다음 마지막에 `text.strip()` 을 하기 때문임.  
    60번째 글자가 공백이면 그게 잘려나가서 52,59..등이 됌.  
    `chunk_overlap` 은 `보장`이 아니라 `목표`임.  
    `separator=""` 면 조각이 글자 1개씩이라 15자에 딱 맞게 남길 수 있어서 겹침이 잘 생김.  
    `반대로 조각 하나가 `chunk_overlap` 보다 크면 전부 버려져서 겹침이 `0` 이 됨`

## Embeddings — 텍스트를 숫자 벡터로

의미가 비슷한 문장을 벡터 공간에서 가까운 좌표에 놓는 변환기. 검색이 가능해지는 이유임.

<div class="til-code" markdown>
```python
from langchain_openai import OpenAIEmbeddings

intro_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
intro_query = "RAG는 문서를 어떻게 사용하나요?"

# embed_query 는 질문 문자열 하나를 받아 `list[float]` 하나를 반환함
intro_query_vector = intro_embeddings.embed_query(intro_query)

print(type(intro_query_vector))     # <class 'list'>
print(len(intro_query_vector))      # 벡터 차원 수
print(intro_query_vector[:5])       # 앞 5개 좌표값
```
</div>

!!! warning
    `embed_query(문자열)` → 벡터 1개. 사용자 `질문`을 벡터로 만들 때 씀.  
    `embed_documents(문자열 목록)` → 벡터 목록. `저장할 문서`들을 벡터로 만들 때 씀.

## VectorStore(Chroma) — 저장, 그리고 재실행 함정

청크의 벡터와 본문을 같이 들고 있다가, 질문 벡터와 가까운 것을 찾아주는 저장소.

<div class="til-code" markdown>
```python hl_lines="3"
from langchain_chroma import Chroma

# from_documents 는 청크를 임베딩까지 해서 넣고 `Chroma` 객체를 반환함
intro_vectorstore = Chroma.from_documents(
    documents=intro_chunks,
    embedding=intro_embeddings,
    collection_name="simple_rag_intro",
)

print(intro_vectorstore._collection.count())        # 6
print(len(intro_vectorstore.get()["ids"]))          # 6
```
<div class="til-note" data-til-line="3" hidden>`embedding` 에는 벡터가 아니라 `임베딩 객체`가 들어감. 저장소가 내부에서 호출함</div>
<div class="til-note" data-til-line="3" hidden>`collection_name` 은 문서 그룹 이름. 같은 이름이면 같은 통에 들어감</div>
</div>

!!! warning
    같은 `collection_name` 으로 셀을 두 번 실행하면 데이터가 누적됨.  
    청크 4개짜리로 테스트했더니 1회 실행 후 `count()` 가 `4`, 2회 실행 후 `8` 이 나왔음.  
    `from_documents` 는 덮어쓰기가 아니라 `get_or_create_collection` + 추가라서 그럼.  
    `persist_directory` 속성을 안 주면 Chroma 는 프로세스 메모리에만 존재함.

<div class="til-code" markdown>
```python
# 컬렉션 자체를 지움. 다시 만들기 전까지 이 객체로는 검색이 안 됨
intro_vectorstore.delete_collection()
```
</div>

## Retriever — 질문 문자열로 문서 찾기

벡터 저장소를 체인에 꽂을 수 있는 형태로 바꾼 것. 입력은 `str`, 출력은 `list[Document]`.

<div class="til-code" markdown>
```python hl_lines="1"
# as_retriever 가 `VectorStoreRetriever` 객체를 반환함
intro_retriever = intro_vectorstore.as_retriever(search_kwargs={"k": 2})

intro_relevant_docs = intro_retriever.invoke(intro_query)

for document in intro_relevant_docs:
    print(document.metadata["source"], document.page_content)

# 저장소를 직접 검색할 수도 있음 (체인에 못 꽂는 대신 인자를 그때그때 줄 수 있음)
hits = intro_vectorstore.similarity_search("오후 반차는 몇 시부터인가요?", k=3)
```
<div class="til-note" data-til-line="1" hidden>`k` 는 상위 몇 개를 가져올지. 안 주면 Chroma 기본값이 4</div>
</div>

!!! warning
    retriever 가 내부에서 임베딩 객체를 불러 질문을 벡터로 바꾸고, 저장된 벡터들과 거리를 잰 뒤,  
    가까운 순으로 `Document` 를 돌려주는 것까지 다 해줌.  
    `similarity_search` 와 `as_retriever` 의 차이 →  
    `similarity_search`는 저장소의 메서드라 호출할 때마다 `k` 를 바꿀 수 있지만 체인에 못 꽂음.  
    `as_retriever`는 `k` 를 객체 생성 시점에 박아두는 대신 체인 부품이 됨.  
    점수까지 보고 싶으면 `similarity_search_with_score` 를 써야 함(반환이 `(Document, 점수)` 튜플).

## 체인으로 묶기 — 프롬프트 + 문서체인 + 검색체인

<div class="til-code" markdown>
```python hl_lines="21 25"
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

intro_chain_prompt = ChatPromptTemplate.from_template("""
다음 문서에 근거해서만 질문에 답하세요.
문서에 답이 없으면 '문서에서 찾을 수 없습니다'라고 답하세요.

[문서]
{context}

[질문]
{input}
""")

print(intro_chain_prompt.input_variables)   # ['context', 'input']

messages = intro_chain_prompt.format_messages(context="근거", input="질문")
print(len(messages), type(messages[0]).__name__)    # 1 HumanMessage

# `문서 → 답변` 담당. 
intro_document_chain = create_stuff_documents_chain(llm, intro_chain_prompt)


# `검색 + 문서체인` 연결 담당. 
intro_rag_chain = create_retrieval_chain(intro_retriever, intro_document_chain)

# intro_response는 딕셔너리 형태임
intro_response = intro_rag_chain.invoke({"input": intro_query})

print(list(intro_response.keys()))          # ['input', 'context', 'answer']
print(len(intro_response["context"]))       # retriever 의 k 와 같음 (여기선 2)
print(intro_response["answer"])             # 답변 문자열
```
<div class="til-note" data-til-line="21" hidden>`Document` 목록의 본문(page_content)를 이어붙여 `{context}` 에 넣고 LLM 호출</div>
<div class="til-note" data-til-line="25" hidden>`input` 을 retriever 에 넘기고 결과를 intro_document_chain에 넘김</div>
</div>

!!! warning
    `create_stuff_documents_chain` → `이미 받은 문서`를 프롬프트에 쑤셔넣고(stuff) LLM 을 부름.  
    `create_retrieval_chain` → retriever 를 불러 `문서를 구해와서` 위 체인에 넘김.  
    `invoke()` 반환은 `dict` 이고 키는 `['input', 'context', 'answer']` 순서로 나왔음.
