"""
title: 도커 — 이미지와 컨테이너 기초
tags: [docker]
"""
#== 이미지와 컨테이너
#> 제일 헷갈리는 부분. 사실 셋으로 나눠 봐야 정리가 됨.
 
# --8<-- [start:concept]
 Dockerfile    →    이미지    →    컨테이너
  (스크립트)       (실행한 결과)    (돌고 있는 것)
        docker build      docker run
# --8<-- [end:concept]
 
# --8<-- [start]
Dockerfile = 설치 지시서. "우분투 깔고, 파이썬 설치하고, 내 코드 복사해라".
#(1)> 이게 스크립트임. 명령어가 줄줄이 적혀 있는 텍스트 파일.
 
docker build = 그 지시서를 `실제로 실행`함.
#(2)> 우분투가 깔리고 파이썬이 설치되고 코드가 복사됨.
 
이미지 = 그 작업이 다 끝난 상태의 디스크를 통째로 얼려서 저장한 것.
#(3)> → 명령어 모음이 아니라 `명령어를 이미 다 실행해놓은 결과물`임.
#(3)> 안에 /bin, /etc, /usr 같은 폴더가 실제 파일로 들어 있음.
 
컨테이너 = 그 이미지를 실행한 것.
# --8<-- [end]

#== 프로그램에 대응시키면
 
# --8<-- [start:analogy]
도커                파이썬으로 치면
Dockerfile    →     빌드 스크립트 (setup.py, Makefile)
이미지        →     빌드 결과물 (python.exe, 설치 폴더 전체)
컨테이너      →     그걸 실행한 프로세스
# --8<-- [end:analogy]
 
#! `이미지 = .exe 파일`, `컨테이너 = 그 프로세스` 가 제일 정확한 대응.
#! python.exe 하나로 파이썬 프로세스를 여러 개 띄울 수 있음. 그거랑 같음.
#! .exe 파일 자체는 실행 중이 아니고, 더블클릭해야 프로세스가 생김.
#! → 이미지도 그냥 파일 덩어리일 뿐이고, run 을 해야 컨테이너가 생김.


#== 컨테이너는 진짜 그냥 프로세스임
#> 가상 머신이 아님. 여기가 제일 오해하기 쉬운 부분.
 
# --8<-- [start:process]
docker run ubuntu:20.04 ls /   # bin boot dev etc home lib ...
#(1)> 컨테이너 안에서 본 / 임. 이미지 안에 실제로 들어있는 폴더들
#(1)> 내 PC 의 / 가 아님
# --8<-- [end:process]
 
#! 컨테이너는 내 PC 에서 도는 그냥 프로세스임. 호스트에서 ps 를 치면 목록에 보임.
#! 다만 그 프로세스가 파일 시스템을 볼 때
#! `내 PC 의 / 가 아니라 이미지 안의 / 를 보도록` 도커가 가려놓은 것.
 

#== 이미지 하나로 컨테이너 여러 개

# --8<-- [start:concept]
  ubuntu:20.04 이미지 
         │
    ┌────┼────┐
    ▼    ▼    ▼
  box1  box2  box3     ← 컨테이너 3개. 
# --8<-- [end:concept]

#! 이미지는 읽기 전용이라 여러 컨테이너가 `공유해서` 씀. 복사하는 게 아님.
#! 컨테이너를 지우면 그 안에서 만든 것도 같이 사라짐.
#! 남겨야 할 데이터는 -v 로 호스트 폴더에 연결해둬야 함 (아래 참고).
#! `(참고)`
#! 태그(tag) = 이미지의 버전 표시. `ubuntu:20.04` 에서 20.04 부분.
#! 생략하면 `:latest` 로 자동 지정됨. 근데 latest 는 "최신" 이 아니라 그냥 기본 이름임.



#== 이미지 명령어

# --8<-- [start:image_cmd]
# 이미지 받기
docker pull ubuntu:20.04

# 받아둔 이미지 목록(docker image ls)
docker images
#(1)> docker image ls 와 같음.

# 이미지 삭제 (docker image remove)
docker rmi ubuntu:20.04
# --8<-- [end:image_cmd]

#! 해당 이미지로 만든 컨테이너가 하나라도 남아 있으면 rmi 가 안 됨.
#! 멈춰 있는 컨테이너여도 마찬가지. 컨테이너를 먼저 지우고 이미지를 지울 것.
#! pull 을 따로 안 해도 됨. docker run 할 때 없으면 알아서 받아옴.


#== 컨테이너 만들기 — create / start / run
#> 셋의 관계를 알면 헷갈릴 일이 없음.

# --8<-- [start:run_relation]
# 나눠서 하기
docker create --name mybox ubuntu:20.04   # 만들기만 (아직 안 돌아감)
docker start mybox                        # 돌리기

# 한 번에 하기 (create + start -> run)
#(1)> run = (이미지 없으면 pull) + create + start
docker run --name mybox ubuntu:20.04

# --8<-- [end:run_relation]

#! run 은 매번 `새 컨테이너`를 만듦. start 는 `기존 컨테이너`를 다시 켬.

#== 컨테이너 목록 보기

# --8<-- [start:ps]
docker ps        # 실행 중인 것만
docker ps -a     # 멈춘 것까지 전부
docker ps -aq    # ID 만 (다른 명령에 넘길 때 씀)
# --8<-- [end:ps]


#== -it 없이 실행하면 왜 바로 꺼지나
#> 컨테이너는 `안에서 돌 프로그램이 있을 때만` 살아 있음.
#> 그 프로그램이 끝나면 컨테이너도 같이 끝남. 빈 상자로 대기하지 않음.

# --8<-- [start:why_it]
# 만들어지긴 하는데 즉시 종료됨. docker ps 에 안 보임
docker run --name box1 ubuntu:20.04

# 이건 컨테이너 안 쉘로 들어가짐. 프롬프트가 root@... 로 바뀜
docker run -it --name box2 ubuntu:20.04

# --8<-- [end:why_it]


#! ubuntu 이미지는 `기본 실행 프로그램`이 `bash` 임.
#! 근데 -it 가 없으면 입력받을 통로가 없어서 bash 가 할 일이 없다고 판단하고 즉시 종료.
#! → bash 가 끝났으니 컨테이너도 끝남.

#! `-i (interactive)` = 입력 통로를 열어둠
#! `-t (tty)        ` = 가상 터미널을 붙여줌 (프롬프트가 보이게)
#! 둘은 거의 항상 같이 씀. 그래서 `-it` 로 붙여 씀.


#== run 옵션 정리

# --8<-- [start:run_opts]
docker run -it --name mybox ubuntu:20.04
            │    │      │     │
            │    │      │     └─ 이미지 (여기서 컨테이너를 만듦)
            │    │      └─ 컨테이너 이름
            │    └─ 이름 붙이기 옵션
            └─ 대화형 + 터미널 연결

# --rm : 종료되면 컨테이너까지 자동 삭제
docker run -it --rm --name mytest ubuntu:20.04

# -d : 백그라운드 실행 (detached)
#(2)> 프롬프트가 안 넘어가고 바로 되돌아옴. 컨테이너는 뒤에서 계속 돎
#(2)> -it 를 같이 쓰는 이유 → 입력 통로가 열려 있어야 bash 가 안 죽음
docker run -it -d --name mytest ubuntu:20.04


# -p : 포트 연결 (호스트:컨테이너)
#(3)> 내 컴퓨터 8080 으로 들어온 요청을 컨테이너 안 80 으로 넘김
#(3)> 브라우저에서 localhost:8080 → 컨테이너의 nginx 가 응답
#(3)> 왼쪽이 내 컴퓨터, 오른쪽이 컨테이너. 순서 헷갈리기 쉬움
docker run -d -p 8080:80 --name web nginx


# -v : 폴더 연결 (호스트경로:컨테이너경로)
#(4)> 컨테이너를 지워도 /home/me/data 의 파일은 남음
#(4)> DB 데이터처럼 사라지면 안 되는 건 반드시 이걸로 빼둘 것
docker run -it -v /home/me/data:/data --name box ubuntu:20.04


# -e : 환경변수 전달
docker run -d -e POSTGRES_PASSWORD=1234 postgres:15
# --8<-- [end:run_opts]

#! -d 와 --rm 을 같이 쓰면 종료되는 순간 사라져서 로그도 못 봄. 조심.


#== 컨테이너 안으로 들어가기 — attach vs exec
#> 이름이 비슷한데 하는 일이 다름.

# --8<-- [start:attach_exec]
# attach — 이미 돌고 있는 그 프로그램의 화면에 붙는 것
#(1)> 새 프로세스를 만들지 않음. 원래 돌던 bash 에 그대로 연결
#(1)> 여기서 Ctrl+C 나 exit 를 하면 그 프로그램이 끝나서 컨테이너도 꺼짐
#(1)> 안 끄고 빠져나오려면 Ctrl+P 다음 Ctrl+Q
docker attach mybox


# exec — 컨테이너 안에서 새 프로그램을 하나 더 띄우는 것
#(2)> 원래 돌던 것과 별개로 새 bash 를 띄움
#(2)> 여기서 exit 해도 컨테이너는 계속 돎. 훨씬 안전함
docker exec -it mybox /bin/bash

# --8<-- [end:attach_exec]

#! 결론 → 컨테이너 안을 들여다볼 때는 `exec` 를 쓸 것. attach 는 실수하기 쉬움.

# --8<-- [end:attach_exec]
쉘 이름이 이미지마다 다름
- ubuntu·debian 계열 → /bin/bash
- alpine           → /bin/sh  (용량을 줄이려고 bash 를 아예 안 넣음)

# --8<-- [end:attach_exec]

#! exec 는 실행 중인 컨테이너에만 됨. 멈춘 컨테이너엔 안 됨.
#! 멈춘 걸 다시 대화형으로 켜려면 → `docker start -ai mybox`


#== 멈추기 · 지우기

# --8<-- [start:stop_rm]
# 정상 종료 요청을 보내고 10초 기다림. 안 끝나면 강제 종료
docker stop mybox

# 기다리지 않고 즉시 강제 종료. 급할 때만
docker kill mybox

# 컨테이너 삭제. 실행 중이면 에러가 남
docker rm mybox

# 실행 중이어도 멈추고 지움
docker rm -f mybox

# 멈춰 있는 것까지 전부 삭제. 청소용
docker rm $(docker ps -aq)
# --8<-- [end:stop_rm]

#! 순서 → 컨테이너 stop → 컨테이너 rm → 이미지 rmi.
#! 거꾸로 하려고 하면 "쓰는 중" 이라고 막힘.

#! 백그라운드로 띄운 컨테이너가 뭘 하는지 보려면
#! `docker logs mybox`      — 지금까지 출력 보기
#! `docker logs -f mybox`   — 계속 따라가며 보기 (Ctrl+C 로 빠져나옴)


#== -p 와 -v 는 '내 PC 가 먼저'

# --8<-- [start:order]
# 왼쪽 = 내 PC(호스트) 포트, 오른쪽 = 컨테이너 포트
#(1)> 둘이 같은 숫자면 티가 안 나서 순서를 틀려도 모르고 넘어감
-p 5432:5432

# 내 PC 5433 으로 들어온 요청을 컨테이너 5432 로 넘김
#(2)> 내 PC 에 이미 Postgres 가 돌고 있으면 이렇게 피해야 함
-p 5433:5432

# 왼쪽 = 내 PC 쪽(볼륨 이름 또는 경로), 오른쪽 = 컨테이너 안 경로
#(3)> 외우는 법 → "내 것 먼저, 컨테이너 나중". -p 와 -v 둘 다 같음
-v db-pg-data:/var/lib/postgresql/data
# --8<-- [end:order]


#== 볼륨 두 종류 — 이름 볼륨 vs 경로 연결
#> -v 뒤 왼쪽에 뭘 쓰느냐로 갈림.

# --8<-- [start:volume_kinds]
# ① 이름 볼륨 (named volume) — 도커가 알아서 관리
#(1)> db-pg-data 는 경로가 아니라 이름. 도커가 자기 영역에 저장소를 만들어 줌
#(1)> DB 데이터처럼 "내가 직접 열어볼 일 없는" 것에 적합
-v db-pg-data:/var/lib/postgresql/data


# ② 경로 연결 (bind mount) — 내 PC 의 실제 폴더
#(2)> 슬래시로 시작하면 경로로 인식됨
#(2)> 소스 코드처럼 "내가 편집기로 직접 고칠" 것에 적합
-v /home/me/data:/data

# 볼륨 관리
docker volume ls              # 목록
docker volume rm db-pg-data   # 삭제
# --8<-- [end:volume_kinds]

#! `docker rm db-pg` 로 컨테이너를 지워도 이름 볼륨은 안 지워짐.
#! 그게 볼륨을 쓰는 이유임 — 컨테이너보다 오래 살아야 하니까.
#! 진짜로 초기화하려면 `docker volume rm` 까지 해야 함.

#== 실전 예시 — Postgres(pgvector) 띄우기

# --8<-- [start:postgres]
# -d               백그라운드로 띄움 (DB 는 계속 돌아야 하니까)
# -e PASSWORD      postgres 이미지는 이 값이 없으면 아예 안 뜸. 필수
# -p 5432:5432     내 PC 5432 → 컨테이너 5432
# -v db-pg-data:…  DB 파일이 저장되는 경로를 볼륨에 연결
# pgvector/pgvector:pg17   Postgres 17 + pgvector 확장이 들어있는 이미지


docker run -d 
  --name db-pg 
  -e POSTGRES_PASSWORD=postgres 
  -p 5432:5432 
  -v db-pg-data:/var/lib/postgresql/data 
  pgvector/pgvector:pg17

# 떴는지 확인
docker ps

# 준비가 끝났는지 로그로 확인
#(2)> "database system is ready to accept connections" 가 나와야 접속 가능
#(2)> -d 로 띄우면 화면에 아무것도 안 나오니 로그로 봐야 함
docker logs db-pg

# --8<-- [end:postgres]


#! 컨테이너가 Up 인 것과 DB 가 접속 받을 준비가 된 것은 다름.
#! 볼륨에 이미 데이터가 있으면 POSTGRES_PASSWORD 가 무시됨.
#! 그 변수는 "처음 초기화할 때" 만 쓰임. 비밀번호를 바꾸려면 볼륨을 지워야 함.


#== 컨테이너 안의 psql 쓰기

# --8<-- [start:psql]

# ① 명령 하나만 실행하고 나오기 — -c 옵션
#(1)> -it 가 없어도 됨. 결과만 받고 바로 끝나니까
#(1)> psql -U postgres  = postgres 라는 사용자로 접속
docker exec db-pg psql -U postgres -c "SELECT version();"


# l = 데이터베이스 목록
#(2)> 기본 DB 3개(postgres·template0·template1)가 나옴. 내가 만든 DB 가 여기 더해짐
docker exec db-pg psql -U postgres -c "\l"

# ② 대화형으로 들어가서 계속 쓰기 — -it 필요
#(3)> psql 프롬프트로 들어감. 여기선 \l, \dt 를 그냥 쳐도 됨
#(3)> 나올 때는 \q
docker exec -it db-pg psql -U postgres
# --8<-- [end:psql]

#! psql 안에서 쓰는 백슬래시 명령 몇 개
#! \l   데이터베이스 목록      \c 이름  그 DB 로 이동
#! \dt  테이블 목록           \d 이름  테이블 구조 보기
#! \q   나가기

#! 이건 SQL 이 아니라 psql 이라는 프로그램의 단축 명령임.

#! `-c` 하나에는 명령 하나만. 여러 개를 이어 쓰려면 `-c` 를 여러 번 붙이거나
#! 대화형(`-it`)으로 들어가는 게 편함.



#== 자주 막히는 것 정리

# --8<-- [start]
 ① run 했는데 ps 에 안 보임
    → 안에서 돌 프로그램이 없어서 즉시 종료됨. -it 를 붙일 것. ps -a 로 확인

 ② 같은 이름으로 run 이 안 됨
    → 이미 있는 이름. `docker rm 이름` 으로 지우거나 `docker start 이름` 을 쓸 것

 ③ 이미지가 안 지워짐
    → 그 이미지로 만든 컨테이너가 남아 있음. 컨테이너부터 지울 것

 ④ attach 했다가 컨테이너가 꺼짐
    → Ctrl+C 로 나와서 그럼. exec 를 쓰거나 Ctrl+P, Ctrl+Q 로 빠져나올 것

 ⑤ bash 가 없다고 함
    → alpine 계열. /bin/sh 로 바꿀 것

 ⑥ 컨테이너 지웠더니 데이터가 사라짐
    → 원래 그럼. -v 로 볼륨이나 호스트 폴더에 연결해뒀어야 함

 ⑦ 포트가 이미 쓰이고 있다고 함 (port is already allocated)
    → 내 PC 에서 그 포트를 쓰는 게 있음. `-p 5433:5432` 처럼 왼쪽만 바꿀 것

 ⑧ DB 컨테이너는 떴는데 접속이 안 됨
    → 초기화 중일 수 있음. `docker logs` 로 ready 문구를 확인할 것

 ⑨ 비밀번호를 바꿔서 다시 run 했는데 옛날 게 먹힘
    → 볼륨에 기존 데이터가 남아 있음. `docker volume rm` 까지 해야 초기화됨
# --8<-- [end]

#== 정리

# --8<-- [start]
run = pull + create + start   ·   start = 기존 것 다시 켜기
-it = 대화형  ·  -d = 백그라운드  ·  --rm = 끝나면 삭제
-p 내PC:컨테이너 = 포트 연결  ·  -v 내PC:컨테이너 = 저장소 연결 (내 것이 먼저!)
-e = 환경변수 전달 (DB 비밀번호 같은 것)
attach = 돌던 프로그램에 붙기 (위험)  ·  exec = 새 프로그램 띄우기 (안전)
# --8<-- [end]

#! 핵심 감각 하나 → "컨테이너는 안에서 돌 프로그램이 있을 때만 산다".
#! 바로 꺼지는 문제의 대부분이 여기서 나옴.

#! 두 번째 감각 → "컨테이너는 언제든 버릴 수 있어야 한다".
#! 그래서 남겨야 할 데이터는 반드시 볼륨으로 빼둠.
