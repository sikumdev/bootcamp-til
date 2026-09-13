"""
title: 검색 품질 — Cross-Encoder 리랭킹, LongContextReorder
tags: [reranker]
"""

#== 기본 세팅

# --8<-- [start:common_imports]
import logging
import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
#(1)> TOKENIZERS_PARALLELISM 옵션이 지난 노트엔 없었는데 여기 새로 추가됨. HuggingFace
#(1)> 토크나이저가 멀티프로세스로 돌 때 나오는 경고를 끄는 옵션임

from dotenv import load_dotenv
from transformers.utils import logging as hf_logging

from kiwipiepy import Kiwi
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.retrievers import BM25Retriever
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.document_transformers import LongContextReorder
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI

hf_logging.disable_progress_bar()
load_dotenv()
# --8<-- [end:common_imports]


#== 하이브리드 후보 만들기 — BM25 + Dense
#> 이번엔 문서에 "2025년(옛 규정)"과 "2026년(현재 규정)"이 섞여 있어서, 
#> 두 검색기 모두 2026년 문서만 쓰도록 따로 필터링해야 함. 
#> BM25와 Dense가 필터링하는 "방식"이 서로 다름.

# --8<-- [start:hybrid_with_filter]

embedding = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
kiwi = Kiwi()

def kiwi_tokenize(text):
    return [token.form for token in kiwi.tokenize(text)]

support_documents = [
    Document(
        page_content="2026년 결제 API에서 SRV-502 오류가 발생하면 API 게이트웨이를 재시작하고 10분 동안 오류율을 관찰합니다.",
        metadata={"title": "SRV-502 대응", "category": "결제", "year": 2026},
    ),
    Document(
        page_content="2025년 SRV-502 오류는 전체 결제 서버를 재부팅하는 방식으로 처리했습니다.",
        metadata={"title": "SRV-502 이전 대응", "category": "결제", "year": 2025},
    ),
    Document(
        page_content="AUTH-401 오류는 인증 토큰 만료 여부를 확인한 뒤 사용자의 세션을 다시 발급합니다.",
        metadata={"title": "AUTH-401 대응", "category": "인증", "year": 2026},
    ),
]
support_query = "2026년 결제 API의 SRV-502 오류는 어떻게 조치하나요?"

# BM25는 "색인하기 전에" 파이썬 리스트 컴프리헨션으로 2025년 문서를 아예 빼버림.
#(1)> BM25Retriever는 filter 인자 자체가 없으니까, 
#(1)> 걸러내려면 색인 대상 리스트 자체를 미리 줄이는 수밖에 없음
support_current_documents = [
    document for document in support_documents
    if document.metadata["year"] == 2026
]

support_store = Chroma.from_documents(
    support_documents, embedding, collection_name="reranker_support_demo"
)

# Dense 쪽은 "전체 문서(2025년 포함)를 다 색인"해두고 검색할 때 필터로 걸러냄.
#(2)> Chroma는 벡터DB라서 메타데이터 필터를 지원함
support_dense = support_store.as_retriever(
    search_kwargs={"k": 5, "filter": {"year": 2026}},
)

support_bm25 = BM25Retriever.from_documents(
    support_current_documents, preprocess_func=kiwi_tokenize,
)

support_bm25.k = 5

support_hybrid = EnsembleRetriever(
    retrievers=[support_bm25, support_dense], weights=[0.5, 0.5], c=60,
)

hybrid_candidates = support_hybrid.invoke(support_query)[:5]

for rank, document in enumerate(hybrid_candidates, start=1):
    print(rank, document.metadata["year"], document.metadata["title"])

# --8<-- [end:hybrid_with_filter]

#! 헷갈렸던 것 → BM25와 Dense가 "연도 필터링"을 하는 방식 자체가 다름. 
#! BM25는 색인 대상 리스트를 미리 줄이는 "사전 필터링"이고,
#! Dense는 전체를 색인해두고 검색 시점에 거르는 "사후 필터링"임.


#== Cross-Encoder 재채점 — 질문·문서 쌍을 직접 채점
#> Bi-Encoder(Dense 검색)는 질문과 문서를 따로따로 벡터로 바꿔서 빠르게 비교함.
#> Cross-Encoder는 질문+문서를 "한 입력"으로 같이 넣어서 관련성 점수 하나를 뽑음 
#> 훨씬 정확하지만 후보 하나하나마다 계산해야 해서 느림. 
#> 그래서 1차로 넓게 찾은 후보(hybrid_candidates)에만 적용함.


# --8<-- [start:cross_encoder_manual]
reranker_model = HuggingFaceCrossEncoder(model_name="../models/bge-reranker-v2-m3")

# 결과 값
#(1)> [9.9770314e-01 2.7035687e-05 1.5630291e-04 1.6361049e-05 2.8395929e-05]
reranker_scores = reranker_model.score(
    [(support_query, document.page_content) for document in hybrid_candidates]
)


reranked_order = sorted(
    range(len(hybrid_candidates)),
    key=lambda index: reranker_scores[index],
    reverse=True,
#(1)> 점수가 높을수록 관련도가 높다는 뜻이라 내림차순 정렬을 해야 1등이 진짜 1등이 됨.
)


for rank, index in enumerate(reranked_order, start=1):
    document = hybrid_candidates[index]
    print(
        f"{rank}위 | 1차 {index + 1}위 | "
        f"점수 {reranker_scores[index]:.3f} | {document.metadata['title']}"
    )
# --8<-- [end:cross_encoder_manual]
#! 이 수동 코드(score → sorted(reverse=True) → 인덱스로  재배열)가
#! 사실 LangChain에 내장된 CrossEncoderReranker.compress_documents랑
#! 로직이 완전히 똑같음.

#== 리랭킹 결과 — 후보 5개 중 상위 3개만 최종 근거로 
#> 하이브리드가 폭넓게(5개) 찾아오고, 리랭커가 그중 진짜 관련 있는 3개만 골라내는 2단계 구조임.
#> 리랭커는 "새 문서를 찾는" 게 아니라 "이미 찾아온 후보의 순서만 다시 매기는" 역할이라,
#> 애초에 하이브리드 후보에 없던 문서는 리랭커도 못 찾음.

# --8<-- [start:top3_select]
support_sources = [hybrid_candidates[index] for index in reranked_order[:3]]

for rank, document in enumerate(support_sources, start=1):
    print(rank, document.metadata["title"])
# --8<-- [end:top3_select]

#! 여기서 배운 것 → "후보를 넓게, 최종은 좁게" 2단계 구조가 핵심임. 1단계(하이브리드)
#! 에서 아예 후보에 못 든 문서는 2단계(리랭커)에서 아무리 관련 있어도 절대 못 나옴.
#! 그래서 1단계 k(여기선 5)를 너무 작게 잡으면 정답 문서가 후보에서 통째로 빠질
#! 위험이 있음


#== LangChain 내장 방식 — CrossEncoderReranker + ContextualCompressionRetriever
#> 위 두 셀(score → sorted → 슬라이싱)을 대신 해주는 LangChain 내장 클래스가 있음. 

# --8<-- [start:builtin_reranker]
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_classic.retrievers import ContextualCompressionRetriever

compressor = CrossEncoderReranker(model=reranker_model, top_n=3)

# ContextualCompressionRetriever 객체
#(3)> base_retriever가 후보를 찾아오고, base_compressor가 그 후보를 다시 채점해서 줄임
#(3)> invoke() 내부에서 base_retriever.invoke(query)로 전체 후보를 먼저 받고,
#(3)> 후보가 있으면 base_compressor.compress_documents(docs, query)로 압축함.
#(3)> 후보가 비어 있으면 압축 단계를 아예 건너뛰고 빈 리스트를 바로 반환함
support_rerank_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=support_hybrid,
)

support_sources = support_rerank_retriever.invoke(support_query)
# --8<-- [end:builtin_reranker]


#== LongContextReorder — 긴 문맥에서 근거 위치 재배치
#> LLM은 프롬프트가 길어지면 중간에 있는 내용을 앞·뒤보다 덜 신경 쓰는 경향이 있음
#> ("lost in the middle" 문제) LongContextReorder는 문서를 지우지 않고 순서만 바꿔서,
#> 가장 중요한 문서를 프롬프트의 맨 앞과 맨 뒤에 배치함.

# --8<-- [start:long_context_reorder]
reorder = LongContextReorder()

reordered_sources = reorder.transform_documents(support_sources)
#(1)> transform_documents의 입력·출력 둘 다 Document 리스트임 
#(1)> 문서를 새로 만들거나 지우는 게 아니라 순서만 바꾸는 거라 개수는 항상 그대로 유지됨

print("재배치 전:", [document.metadata["title"] for document in support_sources])
print("재배치 후:", [document.metadata["title"] for document in reordered_sources])

# --8<-- [end:long_context_reorder]

#! 입력이 [1위, 2위, 3위] 순서일 때 출력은 [1위, 3위, 2위]로 나옴. 
#! 순위(1,2,3)를 다 유지한 채로 "배치 위치"만 바꾸는 거였음 — 1위는 맨 앞 그대로,
#! 1위는 맨 앞 그대로 가장 관련도 낮은 문서(3위)가 중간으로 밀려나고, 그다음(2위)이 맨 뒤로 감.
#! 문서 개수가 늘어나면 남은 순위들이 번갈아 앞/뒤에 쌓이는 방식으로 확장됨


#== 최종 RAG 연결
#> 검색 근거(support_sources)를 프롬프트에 넣고 gpt-4o-mini로 답변을 생성하는 마지막 단계.

# --8<-- [start:final_rag]
def format_support_documents(documents):
    return "\n\n".join(
        f"[{document.metadata['title']} | {document.metadata['year']}년]\n"
        f"{document.page_content}"
        for document in documents
    )


support_context = format_support_documents(support_sources)

review_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "당신은 사내 IT 장애 대응 담당자입니다. "
            "제공된 문맥만 사용해 두 문장 이내로 답하세요.",
        ),
        ("human", "문맥:\n{context}\n\n질문: {question}"),
    ]
)


review_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


review_rag_chain = review_prompt | review_llm | StrOutputParser()
review_answer = review_rag_chain.invoke(
    {"context": support_context, "question": support_query}
)

print("검색 근거:", [d.metadata["title"] for d in support_sources])
print("RAG 답변:", review_answer)

# --8<-- [end:final_rag]


