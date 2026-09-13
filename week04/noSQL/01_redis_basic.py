"""
title: Redis — 메모리 key-value 저장소
tags: [redis]
"""

#== Redis 가 뭐냐
#> 데이터를 메모리(RAM)에 저장하는 key-value 데이터베이스.

# --8<-- [start]
Postgres 는 디스크(HDD,SSD)에 저장함. 안전한 대신 상대적으로 느림.
Redis 는 메모리에 저장함. 빠른 대신 서버가 죽으면 날아갈 수 있음.

Postgres → 없어지면 안 되는 것 (회원 정보, 주문 내역)
Redis    → 없어져도 다시 만들 수 있는 것 (캐시, 세션, 카운터, 대기열)

구조는 단순함. `key → value` 하나뿐.
대신 value 자리에 String·Hash·List 같은 여러 자료구조가 올 수 있음.
# --8<-- [end]

#! 예전에 lru_cache vs Redis 정리했던 것과 이어짐.
#! lru_cache 는 내 프로세스 안에만 있어서 워커마다 따로 놀았음.
#! Redis 는 별도 프로그램이라 워커가 몇 개든 같은 데이터를 봄. 그게 핵심 차이.


#== Docker 띄우고 연결하기

# --8<-- [start:setup]
# docker run -d --name db-redis -p 6379:6379 redis:8
# pip install redis

import redis

r = redis.Redis(
    host="127.0.0.1", port=6379,
    db=0,
    #(1)> Redis 는 0~15 번 DB 가 나뉘어 있음. 서로 안 보임
    decode_responses=True,
    #(2)> 이걸 안 주면 값이 bytes 로 돌아옴
    socket_connect_timeout=3,
)

print(r.ping())   # True
# --8<-- [end:setup]

#! - `decode_responses` 차이
#! True  → '안녕'
#! False → b'\xec\x95\x88\xeb\x85\x95'
#! 안 주면 매번 `.decode()` 를 붙여야 함. 켜두는 게 편함.


#== key 이름 규칙

#! `stock:1`, `cache:price:1` 처럼 콜론으로 구분하는 게 관례.
#! : 형식으로 쓰는 이유 → 사람이 읽기 좋고, `cache:*` 처럼 묶어서 찾기 좋아서.
#! 관례 → `용도:대상:식별자` (예: `session:user:100`, `cache:price:1`)


#== String — 값 하나 저장하기

# --8<-- [start:string]
r.set("demo:greeting", "안녕하세요")
r.get("demo:greeting")        # '안녕하세요'
r.exists("demo:greeting")     # 1
r.delete("demo:greeting")     # 1  (지운 개수)

r.mset({"a": 1, "b": 2, "c": 3})
r.mget("a", "b", "c", "d")  # ['1', '2', '3', None]
#(1)> 여러 개를 한 번에. 없는 key 자리에는 None 이 들어옴
# --8<-- [end:string]

#! `exists` 는 True/False 가 아니라 `개수`를 돌려줌.
#! 있으면 1, 없으면 0. `r.exists("a","b","없음")` → 2
#! if 문에서는 어차피 0 이 False 라 그냥 써도 되긴 함.

#! `넣을 때 숫자를 넣어도 꺼내면 문자열임. `r.mget` 결과가 '1','2','3'`
#! 계산에 쓰려면 `int()` 로 바꿔야 함. Redis 는 전부 문자열로 저장함.


#== TTL — 시간이 지나면 자동 삭제

# --8<-- [start:ttl]
r.set("demo:notice", "잠시 표시되는 안내", ex=30)
#(1)> ex=30 → 30초 뒤 자동 삭제

r.ttl("demo:notice")   # 30   남은 초
r.ttl("TTL없는key")     # -1   key 는 있는데 만료 시간이 없음
r.ttl("없는key")        # -2   key 자체가 없음

r.expire("demo:notice", 200)   # 나중에 TTL 을 걸거나 바꾸기 
r.persist("demo:notice")       # TTL 없애기 (영구 보관)
# --8<-- [end:ttl]

#! 헷갈리면 "없는 key 가 더 없으니까 -2" 로 외울 것.

#! `set` 을 다시 하면 TTL 이 사라짐.
#! `r.set("k","v",ex=100)` → ttl 100
#! `r.set("k","v2")`       → ttl -1   ← TTL 이 날아감
#! 값만 바꾸려다 만료 설정을 통째로 지우게 됨.
#! 값을 갱신하면서 TTL 을 유지하려면 `ex` 를 매번 같이 줄 것.


#== Counter — 숫자 세기

# --8<-- [start:counter]
r.set("demo:visits", 0)
r.incr("demo:visits")            # 1   (반환값이 증가 후 값)
r.incrby("demo:visits", 4)       # 5
r.decrby("demo:visits", 2)       # 3
r.get("demo:visits")             # '3'  ← 문자열
# --8<-- [end:counter]

#! `incr` 은 int 를 주는데 `get` 은 str 을 줌.
#! incr 반환 → 1 (숫자)
#! get 반환  → '5' (문자열)
#! 반환값을 그냥 쓰면 int, 나중에 조회하면 str. 
#! `set` 을 안 하고 바로 `incr` 을 해도 됨. 없으면 0 부터 시작함.
#! Redis 는 명령을 하나씩 처리해서 incr 이 안전함.



#== Hash — 한 key 에 여러 필드

# --8<-- [start:hash]
key = "demo:user:100"
r.hset(key, mapping={"name": "김민준", "grade": "일반", "points": 1000})

r.hincrby(key, "points", 200)

r.hget(key, "name")     # '김민준'
r.hget(key, "없는필드")   # None
r.hgetall(key)          # {'name':'김민준', 'grade':'일반', 'points':'1200'}
r.hlen(key)             # 3
# --8<-- [end:hash]

#! String 으로 해도 되는데 왜 Hash 냐 →
#! 이름만 바꾸고 싶을 때 String 이면 전체를 꺼내서 고치고 다시 넣어야 함.
#! Hash 는 `hset(key, "name", "새이름")` 으로 그 필드만 건드림.
#! 주의 → TTL 은 key 단위로만 걸림. 필드 하나에만 만료를 걸 수는 없음.


#== List — 순서가 있는 데이터

# --8<-- [start:list]
r.delete("q")

for n in ("A-101", "A-102", "A-103"):
    r.lpush("q", n)


r.lrange("q", 0, -1)   # ['A-103', 'A-102', 'A-101']  ← 넣은 역순

r.brpop("q", timeout=1)   # ('q', 'A-101')
#(3)> 오른쪽에서 꺼냄 = 가장 먼저 넣은 것 → 선착순(FIFO)
#(3)> 반환값이 값만이 아니라 (key, 값) 튜플임. 
# --8<-- [end:list]

#! 위 결과 전부 직접 확인함.

#! `lpush + brpop` = 선착순 대기열. 왼쪽으로 넣고 오른쪽에서 꺼내니까.
#! `brpop` 의 b 는 blocking. 목록이 비어 있으면 timeout 만큼 기다림.
#! 일반 `rpop` 은 안 기다리고 바로 None.
#! `ltrim(key, 0, 2)` = 앞에서 3개만 남기고 나머지 버림.



#== Cache-Aside — 캐시를 옆에 두고 쓰는 방식
#> 캐시를 먼저 보고, 없을 때만 원본을 조회해서 캐시에 채워 넣는 패턴.

# --8<-- [start:cache_aside]
def get_product_price(product_id, ttl_seconds=60):
    cache_key = f"cache:price:{product_id}"

    cached = r.get(cache_key)
    if cached is not None:
        return "HIT", int(cached)
        #(1)> ① 캐시에 있으면 그대로 씀. 원본은 안 건드림

    source_prices = {"1": 4500, "2": 3800}       # 실제로는 DB 조회
    price = source_prices.get(str(product_id))
    if price is None:
        return "MISS", None

    r.set(cache_key, price, ex=ttl_seconds)
    return "MISS", price
    #(3)> ② 가져온 값을 TTL 과 함께 캐시에 넣음 → 다음 요청은 HIT
# --8<-- [end:cache_aside]

#! 흐름 세 줄 → 캐시 확인 → 없으면 원본 → 캐시에 저장.
#! TTL 을 꼭 걸어야 함. 안 걸면 원본이 바뀌어도 옛날 값을 영원히 씀.

#! `if cached is not None` 으로 쓴 이유 →
#! 캐시된 값이 `"0"` 이면 `if cached:` 는 False 가 됨. 0원인 상품이 계속 MISS 가 남.



#== Pub/Sub — 메시지 방송
#> 발행(publish)하면 그 채널을 구독(subscribe)한 쪽이 받는 구조.

# --8<-- [start:pubsub]
# 구독자 쪽
sub = redis.Redis(decode_responses=True)
p = sub.pubsub(ignore_subscribe_messages=True)
#(1)> 이 옵션이 없으면 "구독 시작했다" 는 안내 메시지까지 같이 들어옴
p.subscribe("news")

# listen() 은 메시지가 올 때까지 계속 기다림 → 별도 스레드나 프로세스가 필요함.
for m in p.listen():
    print(m)   # {'type':'message', 'pattern':None, 'channel':'news', 'data':'첫 소식'}
    #(2)> 실제 내용은 m["data"] 에 들어 있음

# 발행자 쪽
r.publish("news", "첫 소식")     # 1  ← 받은 구독자 수
r.publish("빈채널", "아무도 안 들음")  # 0
# --8<-- [end:pubsub]


#! 제일 중요한 것 → `그 순간 듣고 있는 사람만 받음`.
#! 구독자가 0명이면 publish 반환값이 0 이고, 메시지는 그냥 사라짐. 저장 안 됨.
#! 나중에 접속한 사람은 지난 메시지를 절대 못 봄.


#! 놓쳐도 되는 것에 씀 → 실시간 알림, 채팅, 대시보드 갱신.
#! 놓치면 안 되는 건 List 로 대기열을 만들거나 (lpush + brpop)
#! Redis Streams 같은 걸 씀.


#== keys 대신 scan_iter

# --8<-- [start:scan]
r.keys("cache:*")        # 결과는 같지만 위험
r.scan_iter("cache:*")   # 이쪽을 쓸 것
# --8<-- [end:scan]

#! 둘 다 같은 결과가 나옴 
#! Redis 는 명령을 하나씩 처리함 → `keys` 가 전체를 훑는 동안 서버가 멈춤.
#! key 가 수백만 개면 그 시간 동안 모든 요청이 대기함.
#! `scan_iter` 는 조금씩 나눠서 훑음 → 다른 요청이 중간중간 끼어들 수 있음.


#== 메모리가 꽉 차면 어떤 key 부터 지워지나
#> `maxmemory-policy` 설정이 정함. 
#> 메모리는 유한함. TTL 없이 계속 쌓으면 언젠가 꽉 참.

 
# --8<-- [start:maxmemory]
# 현재 설정 보기
CONFIG GET maxmemory          # 0 = 제한 없음 (기본값)
CONFIG GET maxmemory-policy   # noeviction (기본값)
 
# 바꾸기
CONFIG SET maxmemory 3mb
CONFIG SET maxmemory-policy allkeys-lru
#(1)> 파이썬에서는 r.config_set("maxmemory-policy", "allkeys-lru")
#(1)> 서버를 껐다 켜면 초기화됨. 영구 설정은 redis.conf 에
# --8<-- [end:maxmemory]
 
# --8<-- [start:policies]
 정책 8가지 — 이름이 "대상 - 고르는 방식" 구조라 조합으로 외우면 됨

 대상
   allkeys-   모든 key 를 대상으로
   volatile-  TTL 이 걸린 key 만 대상으로

 고르는 방식
   -lru      가장 오래 안 쓴 것부터        (Least Recently Used)
   -lfu      가장 적게 쓴 것부터           (Least Frequently Used)
   -random   아무거나
   -ttl      만료가 가장 임박한 것부터      (volatile 에만 있음)

 그 외
   noeviction  아무것도 안 지움. 대신 쓰기를 거부함  ← 기본값
# --8<-- [end:policies]
 
#! 기본값이 `noeviction` 임 → 꽉 차면 오래된 걸 지우는 게 아니라 `새로 쓰는 걸 거부`함.
 
# --8<-- [start:noeviction_test]
maxmemory 3mb 로 두고 계속 넣어봤더니
   7348개에서 멈추고 에러
   OOM command not allowed when used memory > 'maxmemory'
   → 읽기는 되는데 set 이 전부 실패함
# --8<-- [end:noeviction_test]
 
#! 캐시로 쓰는데 이 상태면 어느 순간부터 캐시에 아무것도 안 들어감.
#! 에러가 나서 서비스가 멈추거나, 조용히 캐시가 안 되고 원본만 계속 조회함.
#! → 캐시 용도면 `allkeys-lru` 로 바꿔둘 것.
 
#! `volatile-*` 은 TTL 걸린 key 만 지움.
#! TTL 이 하나도 없으면 지울 대상이 없어서 noeviction 처럼 멈춤. 
#! "TTL 을 안 거는 key 도 섞여 있는데 그건 지키고 싶다" 일 때만 쓸 것.
 
#== 고르는 기준
#! 캐시 전용 서버        → allkeys-lru (가장 흔함)
#! 인기 항목이 뚜렷함     → allkeys-lfu (자주 쓰는 건 오래돼도 남김)
#! 지우면 안 되는 게 섞임 → volatile-lru (단, TTL 을 꼭 걸어둘 것)
#! 데이터 저장 용도       → noeviction 유지 + 메모리 감시
 
#== lru 와 lfu 차이
#! lru → "언제 마지막으로 썼나". 하루 100번 쓰다가 1시간 쉰 key 가 밀려날 수 있음
#! lfu → "얼마나 자주 썼나". 그런 key 는 살아남음
 
 




#== 정리
# --8<-- [start]
Redis   = 메모리 key-value 저장소. 빠르고, 날아갈 수 있음
String  = 값 하나        set / get / mset / mget
Hash    = 여러 필드 묶음  hset / hget / hgetall / hincrby
List    = 순서 있는 목록  lpush / brpop / lrange / ltrim
TTL     = 자동 삭제 시계  ex= / ttl / expire / persist
Pub/Sub = 그 순간 듣는 사람에게만 방송
# --8<-- [end]

#! 실수하기 쉬운 것 세 개 
#! ① set 을 다시 하면 TTL 이 날아감 → 값 갱신할 때 ex 를 같이 줄 것
#! ② 꺼낸 값은 전부 문자열 → 계산 전에 int()
#! ③ Pub/Sub 은 저장이 안 됨 → 놓치면 안 되는 건 List 나 Streams

