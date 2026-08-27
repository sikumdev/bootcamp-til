"""
title: 텍스트 전처리 — 한국어 Kiwi · 영어 NLTK
tags: [nlp]
"""

#== 전처리를 왜 하나
#> 문장을 그대로 두면 "데이터를" 과 "데이터가" 가 다른 단어로 취급됨.

#! 목표는 `의미 있는 단어만 원형으로 남기는 것`.
#! 조사·어미를 떼고, 정보량 없는 단어를 지우고, 같은 뜻은 같은 형태로 만듦.


#== Counter — 빈도 세기
#> 전처리 결과를 확인할 때 계속 씀. 먼저 정리하고 감.

# --8<-- [start:counter]
from collections import Counter

words = ["data", "model", "data", "agent", "data", "model"]
counts = Counter(words)
# Counter({'data': 3, 'model': 2, 'agent': 1})
#(1)> dict 와 비슷한데 `값: 등장횟수` 형태로 자동으로 세어 줌

counts["data"]           # 3

# 없는 키를 조회해도 KeyError 가 아니라 0 이 나옴. dict 와 다른 점
counts["tool"]           # 0

# 빈도 높은 순으로 n 개. (값, 횟수) 튜플의 리스트로 나옴
counts.most_common(2)    # [('data', 3), ('model', 2)]
# --8<-- [end:counter]

#! `most_common()` 은 인자를 안 주면 전부 다 나옴. 정렬된 채로.
#! `most_common(1)` → `[('질문', 3)]` ← 리스트임. 값만 쓰려면 `[0][0]`


#== 1. 문자열 정규화
#> 공백과 기호를 먼저 정리함. 이게 안 되면 뒤가 다 어긋남.

# --8<-- [start:normalize]
import re

noisy = "  에이전트는   데이터를\n\n검색합니다.  "
re.sub(r"\s+", " ", noisy).strip()
#(1)> \s 는 스페이스·탭·줄바꿈을 전부 포함. + 로 연달아 붙은 걸 한 덩어리로

symbol = "MCP@에이전트 #도구 3개를 선택!"
cleaned = re.sub(r"[^가-힣A-Za-z0-9.!?\s]", " ", symbol)
cleaned = re.sub(r"\s+", " ", cleaned).strip()
# --8<-- [end:normalize]

#! 순서가 중요함. `기호 정리 → 공백 정리` 순으로 해야 함.
#! 기호를 공백으로 바꾸면 연속 공백이 새로 생기니까.

#! `.!?` 를 살려두는 이유 → 다음 단계인 `문장 분리`에서 필요해서.
#! 문장부호를 다 지우면 문장 경계를 못 찾음.


#== 2. 문장 분리 — Kiwi

# --8<-- [start:split_sents]
from kiwipiepy import Kiwi

# 형태소 분석기 객체. 한 번 만들어 두고 계속 씀 (만드는 데 시간이 걸림)
kiwi = Kiwi()

sents = kiwi.split_into_sents(source_text)
# Sentence(text='MCP 기반 에이전트는...', start=0, end=28, tokens=None, subs=[])
#(2)> 반환: list. 원소는 Sentence 객체

# 객체 그대로 두면 다루기 불편함
[s.text for s in sents]   # .text 로 문자열만 꺼냄
# --8<-- [end:split_sents]


#== 3. 형태소와 품사 태그

# --8<-- [start:tokenize]
tokens = kiwi.tokenize("MCP 기반 에이전트는 사용자의 질문을 분석합니다.")
# Token(form='MCP', tag='SL', start=0, len=3)
#(1)> 반환: list. 원소는 Token 객체

# form = 표면형(실제 글자), tag = 품사
#(2)> [('MCP','SL'), ('기반','NNG'), ('에이전트','NNG'), ('는','JX'),
#(2)>  ('사용자','NNG'), ('의','JKG'), ('질문','NNG'), ('을','JKO'),
#(2)>  ('분석','NNG'), ('하','XSV'), ('ᆸ니다','EF'), ('.','SF')]
[(t.form, t.tag) for t in tokens]
# --8<-- [end:tokenize]

#! "에이전트는" → `에이전트`(NNG) + `는`(JX)
#! "분석합니다" → `분석`(NNG) + `하`(XSV) + `ᆸ니다`(EF)
#! `ᆸ니다` 처럼 낯선 글자가 나오는 건 정상임. 자모 단위로 분리된 어미.

# --8<-- [start:tags]
# 자주 나오는 태그
 NNG  일반명사      데이터, 질문, 도구
 NNP  고유명사      서울, 부산
 SL   외국어        MCP, AI, GPT
 VV   동사 어근     읽, 쓰, 받, 만들
 VA   형용사 어근   빠르, 정확
 XSV  동사 파생 접미사   하 (분석+하)
 XSA  형용사 파생 접미사 하 (정확+하)
 JKS JKO JX JKG     주격·목적격·보조사·관형격 조사
 EF EC ETM          종결·연결·관형형 어미
 SF                 마침표
# --8<-- [end:tags]

#! 다 외울 필요 없음. `NNG · NNP · SL · VV · VA` 다섯 개만 알면 됨.
#! 나머지는 "조사·어미라서 버릴 것" 으로 뭉뚱그려도 됨.


#== 4. base_tag — 태그에 붙은 결합 정보 떼기

# --8<-- [start:base_tag]
def base_tag(tag):
    return tag.split("-")[0].split("+")[0]

base_tag("VV")      # 'VV'
base_tag("VV-R")    # 'VV'
base_tag("VV+EC")   # 'VV'
#(1)> 태그 뒤에 -R, +EC 처럼 결합 정보가 붙어 나올 때가 있음
#(1)> 그대로 비교하면 in {"VV"} 에 안 걸림. 앞부분만 떼어내서 비교
# --8<-- [end:base_tag]

#! `"VV-R".split("-")` → `['VV', 'R']` → `[0]` → `'VV'`


#== 5. 품사로 단어 고르기

# --8<-- [start:select_pos]
# set 이라 | 로 합집합. in 검사가 빨라서 set 을 씀
noun_tags = {"NNG", "NNP", "SL"}          # 명사 계열
content_tags = noun_tags | {"VV", "VA"}   # 내용어 (명사 + 동사·형용사 어근)

nouns = [t.form for t in kiwi.tokenize(text) if base_tag(t.tag) in noun_tags]
# "서울에서 학생이 책을 읽는다." → ['서울', '학생', '책']

verbs = [t.form for t in kiwi.tokenize(text) if base_tag(t.tag) == "VV"]
# "학생이 책을 읽고 메모를 쓴다." → ['읽', '쓰']
#(2)> 동사 어근은 `쓴다` 가 아니라 `쓰` 로 나옴. 어미가 떨어져서
# --8<-- [end:select_pos]

#! `내용어(content word)` = 뜻을 담은 단어. 명사·동사·형용사.
#! 반대는 `기능어(function word)` = 조사·어미. 문법 역할만 함.


#== 하다 파생 동사는 VV 가 아님

# --8<-- [start:derived_verb]
tokens = kiwi.tokenize("모델이 데이터를 분석하고 결과를 생성한다.")

# [('모델','NNG'), ('이','JKS'), ('데이터','NNG'), ('를','JKO'),
#  ('분석','NNG'), ('하','XSV'), ('고','EC'),
#  ('결과','NNG'), ('를','JKO'), ('생성','NNG'), ('하','XSV'), ...]

# 명사만 : ['모델', '데이터', '분석', '결과', '생성']
# VV 만  : []          ← 하나도 없음
# XSV 만 : ['하', '하']
# --8<-- [end:derived_verb]



#! "분석하다" 는 `분석`(NNG) + `하`(XSV) 로 쪼개짐.
#! 동사처럼 보이지만 `명사 + 접미사` 구조라 VV 가 아님.

#! 그래서 명사 태그만 골라도 `분석`, `생성` 이 잡힘. 오히려 잘된 것.
#! 한국어는 이런 파생 동사가 아주 많아서 `명사만 골라도 대부분 커버됨`.

#! 반대로 VV 만 고르면 순수 동사(읽·쓰·받)만 남고 파생 동사는 다 빠짐.



#== 6. 불용어 제거

# --8<-- [start:stopwords]
# set 으로 두는 이유 → in 검사가 리스트보다 훨씬 빠름
base_stopwords = {"기반", "필요", "결과"}
filtered = [w for w in content_words if w not in base_stopwords]
Counter(filtered).most_common(5)
# --8<-- [end:stopwords]

#! `불용어(stopword)` = 자주 나오지만 정보량이 낮은 단어.
#! 뉴스 분석에서 "기자" 는 불용어지만, 직업 분석에서는 핵심어임.


#== 7. N-gram

# --8<-- [start:ngram]
def make_ngrams(items, n):
    if n < 1:
        raise ValueError("n은 1 이상이어야 합니다.")
    return [tuple(items[i:i + n]) for i in range(len(items) - n + 1)]

make_ngrams(["에이전트","데이터","검색","도구"], 2)
# [('에이전트','데이터'), ('데이터','검색'), ('검색','도구')]
#(1)> 연속한 n 개를 묶음. 개수는 len - n + 1

# [] — n 이 단어 수보다 크면 빈 리스트. range 가 음수라 안 돎
make_ngrams(["질문","분석","도구","선택"], 5)
# --8<-- [end:ngram]

#! 왜 쓰냐 → 단어 하나로는 뜻이 안 잡히는 게 있어서.
#! "머신"·"러닝" 따로면 의미가 흐린데 ("머신","러닝") 이면 명확함.
#! `bigram` = 2개, `trigram` = 3개. n=1 은 그냥 단어 하나(unigram).



# --8<-- [start:ngram_boundary]
sentences = ["에이전트 데이터 검색", "모델 결과 생성"]

[g for s in sentences for g in make_ngrams(s.split(), 2)]
# [('에이전트','데이터'), ('데이터','검색'), ('모델','결과'), ('결과','생성')]
# --8<-- [end:ngram_boundary]

#! 핵심은 `문장 분리를 먼저 하는` 것. N-gram 을 만들려면 경계가 필요함.


#== 8. 전처리 함수로 묶기

# --8<-- [start:pipeline_ko]
# 기본값을 None 으로 두고 안에서 채움
#(1)> 기본값 자리에 set() 을 직접 쓰면 모든 호출이 같은 객체를 공유해서 위험함
def preprocess_korean(text, selected_tags=None, stopwords=None):
    selected_tags = content_tags if selected_tags is None else set(selected_tags)
    stopwords = set() if stopwords is None else set(stopwords)

    normalized = re.sub(r"\s+", " ", text).strip()
    tagged = [(t.form, base_tag(t.tag)) for t in kiwi.tokenize(normalized)]
    selected = [f for f, tg in tagged if tg in selected_tags and f not in stopwords]

    return {"normalized": normalized, "tagged": tagged,
            "tokens": selected, "frequency": Counter(selected)}

# --8<-- [end:pipeline_ko]

#! 반환 키 네 개의 뜻
#! `normalized` — 공백 정리만 한 원문
#! `tagged`     — (표면형, 태그) 전부. 버려진 조사까지 다 들어있음
#! `tokens`     — 실제로 고른 단어들 ← 보통 이걸 씀
#! `frequency`  — tokens 의 Counter

#! 인자를 바꾸면 결과가 달라짐. 같은 문장에서
#! 명사만               → ['모델', '데이터', '분석']
#! 내용어               → + 형용사 어근
#! 내용어 - {"데이터"}   → 데이터 빠짐



#== 영어 — 토큰화 두 가지

# --8<-- [start:en_tokenize]
from nltk.tokenize import TreebankWordTokenizer, WordPunctTokenizer

tb = TreebankWordTokenizer()
wp = WordPunctTokenizer()

text = "Good muffins cost $3.88 in New York. I can't wait!"

tb.tokenize(text)
#(1)> 13개 ['Good','muffins','cost','$','3.88','in','New','York.','I','ca',"n't",'wait','!']
#(1)> 3.88 을 하나로 유지. can't 를 ca + n't 로 (영어 문법 규칙)
#(1)> ★ 'York.' 에 마침표가 붙어 있음. 문장 끝을 못 알아챈 것

wp.tokenize(text)
#(2)> 17개 ['Good','muffins','cost','$','3','.','88','in','New','York','.','I','can',"'",'t','wait','!']
#(2)> 3.88 을 3 . 88 로 쪼갬. 기호를 전부 떼어냄
# --8<-- [end:en_tokenize]

#! 직접 돌려서 확인한 값임. 개수가 13 vs 17.

#! `Treebank` — 영어 문법 규칙을 씀. 숫자·축약형을 살림. 보통 이걸 씀
#! `WordPunct` — 글자 덩어리와 기호를 기계적으로 분리. 더 잘게 쪼갬

#! ★ Treebank 가 `York.` 를 하나로 남긴 게 눈에 띔.
#! 문장 단위로 먼저 자르지 않으면 이런 게 생김.
#! → 영어도 `문장 분리 → 토큰화` 순서가 안전함.

#! 한국어와 비교하면
#! 한국어는 조사가 붙어서 `형태소 분석`이 필요했음 (에이전트 + 는)
#! 영어는 공백으로 대충 나뉘어서 `토큰화`로 충분함


#== 영어 — 품사 부착

# --8<-- [start:en_pos]
from nltk import pos_tag

pos_tag(tb.tokenize("Alice studies language models."))
#(1)> Penn Treebank 태그. (단어, 태그) 튜플의 리스트
#(1)> [('Alice','NNP'), ('studies','NNS'), ('language','NN'), ('models','NNS'), ('.','.')]

nouns = [w for w, t in tagged if t.startswith("NN")]
verbs = [w for w, t in tagged if t.startswith("VB")]
#(2)> ★ startswith 로 비교함. NN·NNS·NNP·NNPS 를 한 번에 잡으려고
# --8<-- [end:en_pos]

#! 태그 계열
#! `NN` 명사   — NN(단수) NNS(복수) NNP(고유) NNPS(고유복수)
#! `VB` 동사   — VB VBD(과거) VBG(-ing) VBN(과거분사) VBP VBZ(3인칭)
#! `JJ` 형용사 — JJ JJR(비교급) JJS(최상급)
#! `RB` 부사

#! ★ 한국어 base_tag 와 하는 일이 같음. 둘 다 `태그 앞부분만 보는` 것.
#! 한국어는 `-`·`+` 를 떼고, 영어는 `startswith` 로 계열을 묶음.

#! `studies` 가 NNS(명사 복수)로 잡혔음. 문맥상 동사인데.
#! 통계 모델이라 이런 실수가 있음. 100% 믿으면 안 됨.


#== ★ 틀린 것 ③ 다른 문장의 결과를 씀

# --8<-- [start:en_pos_trap]
fill_tagged = pos_tag(tb.tokenize("Researchers build useful tools."))
direct_tagged = pos_tag(tb.tokenize("Alice studies language models."))

# ❌ 내가 쓴 것 — fill 을 씀
[w for w, t in fill_tagged if t.startswith('N')]
# ['Researchers', 'tools']    ← Alice 문장이 아님

# ✅ 정답 — direct 를 씀
[w for w, t in direct_tagged if t.startswith('NN')]
# ['Alice', 'studies', 'language', 'models']
# --8<-- [end:en_pos_trap]

#! 앞 셀에서 복사해 오면서 변수명을 안 바꿨음.
#! 결과가 그럴듯하게 나와서 눈치채기 어려웠음.

#! 습관 → 복붙한 뒤 `변수명을 먼저 바꾸고` 실행할 것.


#== 영어 — 개체명 인식 (NER)

# --8<-- [start:en_ner]
from nltk import ne_chunk
from nltk.tree import Tree

tree = ne_chunk(tagged)
#(1)> 반환: Tree 객체. 품사 붙은 토큰에서 사람·지역·기관을 묶어 줌
#(1)> (S
#(1)>   (PERSON Barack/NNP)      ← 개체로 묶인 건 자식 Tree
#(1)>   (PERSON Obama/NNP)
#(1)>   visited/VBD              ← 나머지는 그냥 (단어, 태그) 튜플
#(1)>   (GPE New/NNP York/NNP)

def extract_named_entities(chunk_tree):
    entities = []
    for node in chunk_tree:
        if isinstance(node, Tree):
            #(2)> ★ Tree 인 것만 개체명. 튜플은 그냥 단어라 건너뜀
            entities.append((node.label(), " ".join(w for w, _ in node.leaves())))
    return entities

# [('PERSON','Barack'), ('PERSON','Obama'), ('GPE','New York')]
# --8<-- [end:en_ner]

#! 직접 돌려서 확인한 값임.

#! Tree 구조 → 루트는 항상 `S`(문장).
#! 개체명으로 잡힌 연속 토큰만 하위 Tree 로 묶이고, 나머지는 튜플로 평평하게 남음.
#! 그래서 `isinstance(node, Tree)` 로 걸러내는 것.

#! `label()` = 개체 종류 (PERSON·GPE·ORGANIZATION)
#! `leaves()` = 그 안의 (단어, 태그) 목록. 단어만 뽑아 이어붙임

#! ★ 결과가 완벽하지 않음. 확인해보니
#! `Barack` 과 `Obama` 가 `따로` 잡힘. 한 사람인데 두 개로.
#! `Google` 은 NNP 로 태그됐는데 개체명으로는 `안 잡힘`.
#! 통계 모델이라 그럼. 문맥에 따라 결과가 달라짐.

#! → NER 결과를 그대로 믿고 자동화하면 안 됨. 검토가 필요함.


#== 영어 — 어간(stem) vs 표제어(lemma)
#> 둘 다 "원형으로 되돌리기" 인데 방식이 완전히 다름.

# --8<-- [start:stem_lemma]
from nltk.stem import PorterStemmer, WordNetLemmatizer

st, lm = PorterStemmer(), WordNetLemmatizer()

[st.stem(w) for w in ["running","beautiful","believes","organization","studies"]]
#(1)> ['run', 'beauti', 'believ', 'organ', 'studi']
#(1)> ★ 사전에 없는 형태가 나옴. beauti · believ · studi
#(1)> 규칙으로 접미사를 자를 뿐이라 그럼. 빠르지만 거침

lm.lemmatize("children", pos="n")   # 'child'
lm.lemmatize("studies", pos="v")    # 'study'
lm.lemmatize("better", pos="a")     # 'good'
#(2)> 사전(WordNet)을 찾아서 진짜 원형을 돌려줌. better → good 까지 됨

lm.lemmatize("running")             # 'running'   ← 안 바뀜
lm.lemmatize("running", pos="v")    # 'run'
#(3)> ★ 품사를 안 주면 기본값이 명사. 동사는 pos="v" 를 꼭 줄 것
# --8<-- [end:stem_lemma]

#! 전부 직접 돌려서 확인한 값임.

#! `stem`  — 규칙 기반. 빠름. 결과가 단어가 아닐 수 있음
#! `lemma` — 사전 기반. 느림. 진짜 원형이 나옴. 품사가 필요함

#! 검색용 색인처럼 `형태만 맞추면 되는` 곳은 stem 으로 충분.
#! 사람이 읽거나 사전을 찾아야 하면 lemma.

#! ★ 한국어에는 이 구분이 없음. 형태소 분석이 이미 어근을 돌려줌.
#! `읽는다` → `읽`(VV). stem/lemma 를 따로 할 필요가 없음.


#== 영어 — 품사를 lemma 용으로 변환

# --8<-- [start:penn_to_wordnet]
def penn_to_wordnet(tag):
    if tag.startswith("J"): return "a"   # 형용사
    if tag.startswith("V"): return "v"   # 동사
    if tag.startswith("N"): return "n"   # 명사
    if tag.startswith("R"): return "r"   # 부사
    return "n"                            # 기본값 명사
# --8<-- [end:penn_to_wordnet]

#! 왜 필요하냐 → `태그 체계가 두 개`라서.
#! pos_tag 는 Penn Treebank (NN·VBD·JJ...)
#! lemmatize 는 WordNet ("n"·"v"·"a"·"r")
#! 그대로 넘기면 안 되니 변환 함수가 필요함.

#! 마지막 `return "n"` 이 중요함. 모르는 태그는 명사로 처리.
#! 없으면 None 이 넘어가서 에러가 남.


#== 영어 — 불용어와 필터링

# --8<-- [start:en_filter]
english_stopwords = {"a","an","the","and","of","to","in","at","with"}
allowed_prefixes = ("NN", "VB", "JJ")

filtered = [
    word.lower()
    for word, tag in tagged
    if word.isalpha()
    #(1)> 구두점·숫자 제거. '.' 나 '$' 는 isalpha() 가 False
    and word.lower() not in english_stopwords
    #(2)> 소문자로 바꿔서 비교. "The" 와 "the" 를 같이 처리
    and tag.startswith(allowed_prefixes)
    #(3)> ★ startswith 는 튜플을 받음. 여러 접두사를 한 번에 검사
]
# --8<-- [end:en_filter]

#! `startswith(("NN","VB","JJ"))` 처럼 튜플을 넣을 수 있음. 몰랐던 것.
#! 리스트는 안 되고 `튜플`이어야 함.

#! ★ 한국어와 영어의 순서가 다름
#! 한국어 — 형태소 분석이 조사·어미를 알아서 떼어냄 → 품사로 고르면 끝
#! 영어   — 소문자 변환·구두점 제거를 `직접` 해야 함

#! 영어 불용어는 관사·전치사·접속사가 많음. 한국어보다 목록이 김.
#! NLTK 에 내장 목록도 있음 → `from nltk.corpus import stopwords`


#== 한국어 vs 영어 정리

# --8<-- [start:ko_vs_en]
#                 한국어 (Kiwi)              영어 (NLTK)
# 문장 분리       split_into_sents           문장 분리 후 토큰화 권장
# 단어 쪼개기     tokenize (형태소 분석)      TreebankWordTokenizer
# 품사            NNG·NNP·SL·VV·VA           NN·VB·JJ·RB 계열
# 태그 비교       base_tag() 로 앞부분        startswith() 로 계열
# 원형 복원       분석 결과가 이미 어근        stem 또는 lemmatize
# 소문자 처리     필요 없음                   .lower() 필요
# 구두점          SF 태그로 걸러짐            isalpha() 로 걸러야 함
# 개체명          별도 도구 필요              ne_chunk
# --8<-- [end:ko_vs_en]

#! 큰 차이 하나 → `한국어는 형태소 분석이 대부분을 해결함`.
#! 조사·어미 분리, 어근 복원, 구두점 태깅이 한 번에 됨.
#! 영어는 토큰화·소문자·구두점·원형복원을 따로따로 해야 함.

#! 대신 한국어는 형태소 분석기가 없으면 아무것도 못 함.
#! 영어는 `text.split()` 만으로도 어느 정도 됨.


#== 오늘 틀린 것 모음

#! ① N-gram 을 문장 경계 없이 만듦 → ('검색','모델') 같은 가짜 조합이 생김
#! ② mission_token_sets 에 `tagged` 를 넣음 → `tokens` 여야 함
#! ③ 영어 명사 추출에서 다른 문장의 `fill_tagged` 를 씀 → `direct_tagged`

#! ①②③ 공통점 → `문제 지문을 끝까지 안 읽음`.
#! "문장별", "토큰 집합", 변수명이 다 지문에 적혀 있었음.

#! 그리고 셋 다 `에러가 안 남`. 결과가 그럴듯하게 나와서 더 위험함.
#! 습관 → 결과를 기대값과 눈으로 대조할 것. 개수부터 세어볼 것.


#== 정리

#! 흐름  정규화 → 문장 분리 → 형태소 분석 → 품사 선택 → 불용어 제거 → 빈도
#! Kiwi  split_into_sents(문장) · tokenize(형태소) · token.form / token.tag
#! 태그  NNG NNP SL(명사) · VV VA(동사·형용사 어근) · 나머지는 조사·어미
#! base_tag  태그에 붙은 -R, +EC 를 떼어내고 비교
#! 하다 파생  분석하다 = 분석(NNG) + 하(XSV). VV 가 아님
#! N-gram  문장별로 만들 것. 경계를 넘으면 없던 조합이 생김
#! 영어  Treebank(문법 규칙) vs WordPunct(기계적) · stem(규칙) vs lemma(사전)
#! lemma  품사를 안 주면 명사로 처리됨. 동사는 pos="v" 필수

#! 감각 하나 → `전처리 결과는 항상 눈으로 볼 것`.
#! 중간 결과를 print 해서 조사가 남았는지, 이상한 게 섞였는지 확인.


#? Kiwi 사용자 사전에 도메인 단어를 추가하는 법 (MCP, 에이전트 같은 것)
#? 전처리한 토큰으로 문서-단어 행렬을 만드는 법 (numpy 노트와 연결)
#? 임베딩을 쓸 거면 전처리를 어디까지 해야 하는지
#? 한국어 개체명 인식은 어떤 도구를 쓰는지