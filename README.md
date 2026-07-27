# 부트캠프 TIL

실습 코드(`.py`)에 주석만 달면 학습 노트 사이트가 자동으로 만들어지는 저장소입니다.
`git push` 한 번이면 노트 변환 → 공부 주제 이슈 생성 → 사이트 배포가 자동으로 돕니다.

## 폴더 구조

```
.
├─ docs/                     # 여기 안에서 실습하고 정리합니다
│  ├─ index.md               # 첫 화면 · 진도표
│  └─ week01/                # 주차별 폴더
│     ├─ main.py             # 실습 코드 (여기만 신경 쓰면 됨)
│     └─ main.md             # ← py2md.py 가 자동 생성 (직접 고치지 말 것)
├─ tools/
│  ├─ py2md.py               # .py → 학습 노트 .md 변환
│  └─ issue_extract.py       # #@@@ → GitHub 이슈 (중복 방지 포함)
├─ .github/workflows/
│  └─ deploy.yml             # push 시 변환·이슈·배포 자동 실행
├─ .vscode/
│  └─ python.code-snippets   # 기호 입력 단축어 (til, sec, fold 등)
├─ mkdocs.yml                # 사이트 설정
├─ preview.sh                # 로컬 미리보기
└─ README.md
```

## 주석 기호

실습 `.py` 파일에 아래 기호를 주석으로 달면 노트가 자동으로 만들어집니다.

| 기호 | 뜻 | 노트에서 |
|---|---|---|
| `#==` | 섹션 제목 | `##` 헤딩 |
| `#>` | 설명 (여러 줄은 한 문단으로 합쳐짐) | 본문 문단 |
| `#!` | 배운 점 · 막혔던 부분 | 노란 박스 (코드 바로 밑, 줄바꿈 유지, 연속 줄은 한 박스로) |
| `#?` | 나중에 볼 것 | 하단 체크박스 |
| `#@@@` | 따로 팔 큰 주제 | GitHub 이슈 |
| `#(1)>` | 코드 줄 강조 + 클릭 설명 | 그 줄이 파란 배경, 코드 밑에 접이식 박스 |
| `#(1:5)>` | 여러 줄(위로 5줄) 강조 + 설명 | 지정한 줄 수만큼 파란 배경 |
| `# --8<-- [start]`<br>`# --8<-- [end]` | 노트에 넣을 코드 구간 | 이 구간 안의 코드만 노트에 나옴 |

`title:` 이 아예 없으면 아직 안 쓴 파일로 보고 노트를 만들지 않습니다.

## 핵심 규칙 1: 코드는 감싼 구간만 나옵니다

노트에 코드를 넣으려면 그 부분을 `# --8<-- [start]` 와 `# --8<-- [end]` 로
감싸야 합니다. 감싸지 않은 코드는 노트에 나오지 않습니다 (섹션 제목·설명만 남음).

이름은 없어도 됩니다. 한 파일에서 여러 구간을 뽑을 때만 `[start:이름]` 처럼 구분하세요.

## 핵심 규칙 2: 코드 줄 강조 + 접이식 설명

문법·개념 설명은 코드에 길게 남기지 말고 접어두세요.
코드 줄 아래에 `#(1)>` 로 설명을 달면, 그 코드 줄이 파란 배경으로 강조되고
바로 밑에 접이식 박스(클릭하면 펼쳐짐)가 생깁니다. 첫 줄이 박스 제목이 됩니다.

```python
# --8<-- [start]
@app.post("/posts")
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    created_post = Post(**post.model_dump())
    #(1)> model_dump()가 pydantic 객체를 dict로 변환
    #(1)> **가 그 dict를 키워드 인자로 풀어줌 → Post(title=..., ...)
    #(1)> 즉, DB 객체를 만드는 것
    db.add(created_post)
    return created_post
# --8<-- [end]
```

- `#(1)>` 는 바로 위 한 줄을 강조합니다.
- 여러 줄을 강조하려면 첫 줄에만 `:줄수` 를 붙입니다. 예: `#(1:5)>` = 위로 5줄.
  나머지 줄은 그냥 `#(1)>` 로 두면 됩니다 (범위는 첫 줄이 정함).
- 줄바꿈은 그대로 유지됩니다.

강조할 코드가 여러 줄일 때 예시:

```python
    update_dict = {
        key: value
        for key, value in post_update.model_dump().items()
        if value is not None
    }
    #(1:5)> 실제로 보낸(None이 아닌) 필드만 골라 수정
    #(1)> 1) model_dump()로 요청을 dict로 변환
    #(1)> 2) .items()로 (key, value) 쌍을 꺼냄
```

## 기호 입력 단축어 (VS Code / Cursor)

`.vscode/python.code-snippets` 덕분에 `.py` 에서 단축어 + Tab 으로 기호를 넣을 수 있습니다.

| 단축어 | 나오는 것 |
|---|---|
| `til` | 파일 전체 기본 틀 (title, tags, 섹션) |
| `sec` | `#== ` |
| `desc` | `#> ` |
| `stuck` | `#! ` |
| `todo` | `#? ` |
| `issue` | `#@@@ ` |
| `fold` | `#(1)>` (한 줄 강조 설명) |

## 처음 세팅 (한 번만)

1. GitHub에 **public** 저장소를 만들고 이 파일들을 올립니다.
2. `mkdocs.yml` 의 `site_url`, `repo_url` 을 본인 주소로 바꿉니다.
3. 저장소 **Settings → Actions → General → Workflow permissions** 를
   **Read and write permissions** 로 바꿉니다 (배포·이슈 생성에 필요).
4. 첫 push 후 워크플로우가 성공하면 `gh-pages` 브랜치가 생깁니다.
   그다음 **Settings → Pages → Source** 를 `gh-pages` 브랜치 / `/ (root)` 로 지정합니다.
5. 저장소 **Issues → Labels** 에서 `til-todo` 라벨을 하나 만듭니다.
6. 로컬에 도구 설치: `pip install mkdocs-material`

> 워크플로우 파일(`.github/workflows/deploy.yml`)을 로컬에서 push 하려면
> Personal Access Token 에 `workflow` 권한이 필요합니다. 없으면 push 가 거부되니,
> 토큰에 권한을 추가하거나 이 파일만 GitHub 웹에서 직접 만드세요.

## 로컬 미리보기

push 전에 사이트를 미리 보려면 저장소 최상단에서 실행합니다.

```bash
./preview.sh
```

브라우저에서 터미널에 뜨는 주소(예: http://127.0.0.1:8000/ )로 접속하세요.
끌 때는 `Ctrl + C`.

> `.py` 를 새로 고쳤을 때는 `mkdocs serve` 가 자동 반영하지 않습니다.
> `Ctrl + C` 로 끄고 `./preview.sh` 를 다시 실행하세요.

처음 한 번은 실행 권한이 필요할 수 있습니다: `chmod +x preview.sh`

## 매일 하는 일

1. `docs/주차폴더/` 안에서 `.py` 로 실습하며 주석으로 정리
   (노트에 넣을 코드는 `# --8<-- [start]` / `[end]` 로 감싸기)
2. 미리보기: `./preview.sh`
3. `git add . && git commit -m "1주차 게시글 CRUD" && git push`

push하면 나머지(노트 변환·이슈 생성·사이트 배포)는 자동입니다.

## 사진 · 표 넣기

사진이나 표가 많은 노트는 `.py` 대신 **`.md` 로 직접** 쓰는 것이 편합니다.
스크립트는 `.py` 만 변환하고 `.md` 는 건드리지 않으므로, 직접 쓴 `.md` 는
그대로 사이트에 나옵니다 (짝이 되는 `.py` 가 없으면 안전).

**사진** — `.md` 파일을 열고 스크린샷을 복사한 뒤 붙여넣기(Ctrl/Cmd + V)하면,
이미지가 노트 옆 `img/` 폴더에 자동 저장되고 경로도 자동으로 삽입됩니다.
(Cursor/VS Code에 기본 내장. 안 되면 확장에서 "Paste Image" 설치)

```markdown
# SQL 조인 정리

![조인 결과](img/join_result.png)

핵심 쿼리는 이 부분:

```python
--8<-- "week02-sql/practice.py:join"
```
```

**표** — `.md` 에 마크다운 표를 그대로 씁니다.

```markdown
| 조인 종류 | 설명 |
|---|---|
| INNER | 양쪽 다 있는 것만 |
| LEFT | 왼쪽 기준 전부 |
```

정리하면: 코드 위주인 날은 `.py`, 사진·표가 많은 날은 `.md`. 둘은 같은 사이트에 섞입니다.

## 주의

- 자동 생성된 `.md` 를 손으로 고치면 다음 push 때 덮어써집니다.
  특정 노트를 직접 다듬고 싶으면, 짝이 되는 `.py` 를 지우고 `.md` 만 남겨
  직접 관리하는 파일로 승격시키세요.
- `#@@@` 는 정말 따로 시간 잡고 팔 큰 주제에만 쓰세요.
  자잘한 건 `#?` 로 노트에 남기는 편이 이슈 목록을 깔끔하게 유지합니다.
- 코드 줄 강조·접이식 박스는 브라우저에서 동작합니다.
  정적 파일이 아니라 `./preview.sh` 미리보기나 실제 배포 사이트에서 확인하세요.