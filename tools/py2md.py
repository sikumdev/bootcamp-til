#!/usr/bin/env python3
"""실습 코드(.py)를 MkDocs 학습 노트(.md)로 변환한다.

사용법:
    python py2md.py week03/groupby.py
    python py2md.py docs/**/*.py
"""
import ast
import datetime
import pathlib
import re
import sys

MARK_RE = re.compile(r"^\s*#(==|>|!|\?)\s?(.*)$")
# #@@@ 는 issue_extract.py 가 처리하므로 노트/코드 양쪽에서 제외한다.
ISSUE_RE = re.compile(r"^\s*#@@@\s+")
# snippet 구간 표시(--8<-- [start]/[end])는 노트 코드에서 제거한다.
SNIPPET_RE = re.compile(r"^\s*#\s*-{2,}8<-{2,}\s*\[(start|end)")
# 코드 줄 끝의 접이식 주석 마커:  ... code ...  #(1) 또는 #(1:3) 짧은 설명
INLINE_RE = re.compile(r"^(.*?)\s*#\((\d+)(?::(\d+))?\)(?!>)\s?(.*)$")
# 여러 줄 접기 설명의 이어지는 줄:  #(1)> 또는 #(1:3)> 긴 설명
CONT_RE = re.compile(r"^\s*#\((\d+)(?::(\d+))?\)>\s?(.*)$")


META_RE = re.compile(r"^\s*(title|tags|date)\s*:\s*(.*)$")


def read_meta(src):
    """title/tags/date 를 찾는다. 먼저 모듈 docstring을 보고,
    없으면 파일 전체에서 title:/tags: 로 시작하는 줄을 찾는다(위치 무관)."""
    meta, skip = {}, 0
    try:
        tree = ast.parse(src)
        doc = ast.get_docstring(tree)
    except SyntaxError:
        doc = None
    if doc is not None:
        skip = tree.body[0].end_lineno
        for line in doc.splitlines():
            m = META_RE.match(line)
            if m:
                meta[m.group(1).lower()] = m.group(2).strip()
    # 모듈 docstring에서 title 을 못 찾았으면 파일 전체를 훑는다.
    if not meta.get("title"):
        for line in src.splitlines():
            m = META_RE.match(line)
            if m and m.group(1).lower() not in meta:
                meta[m.group(1).lower()] = m.group(2).strip()
    return meta, skip


SNIP_START_RE = re.compile(r"^\s*#\s*-{2,}8<-{2,}\s*\[start")
SNIP_END_RE = re.compile(r"^\s*#\s*-{2,}8<-{2,}\s*\[end")


def parse(src, skip=0):
    body, questions = [], []
    code, hl = [], []
    notes = {}        # {번호: [설명 줄, ...]}  삽입 순서 유지
    note_order = []   # 번호 등장 순서

    lines = src.splitlines()
    # 파일에 --8<-- [start] 가 하나라도 있으면 "구간만" 모드.
    snippet_mode = any(SNIP_START_RE.match(l) for l in lines)
    in_region = False

    def mark_hl(idx):
        """code 리스트에서 1-based 줄 번호 idx 를 강조 목록에 추가(중복 방지)."""
        if idx not in hl:
            hl.append(idx)

    def flush():
        nonlocal code, hl, notes, note_order
        while code and not code[-1].strip():
            code.pop()
        if code:
            ordered = [(n, "<br>".join(s for s in notes[n] if s).strip())
                       for n in note_order]
            body.append(("code", list(code), (sorted(hl), ordered)))
        code, hl = [], []
        notes, note_order = {}, []

    for lineno, raw in enumerate(lines, 1):
        if lineno <= skip:
            continue
        # snippet 구간 시작/끝
        if SNIP_START_RE.match(raw):
            in_region = True
            continue
        if SNIP_END_RE.match(raw):
            in_region = False
            continue
        if ISSUE_RE.match(raw):
            continue
        # 파일 중간의 title:/tags:/date: 줄, 그리고 그걸 감싼 docstring 따옴표는 노트에서 제외
        if META_RE.match(raw) or raw.strip() in ('"""', "'''"):
            continue
        m = MARK_RE.match(raw)
        if m and not (lineno == 1 and raw.startswith("#!/")):
            tag, text = m.group(1), m.group(2).strip()
            if tag == "==":
                flush()
                body.append(("head", text, None))
            elif tag == ">":
                flush()
                if body and body[-1][0] == "prose":
                    body[-1] = ("prose", body[-1][1] + " " + text, None)
                else:
                    body.append(("prose", text, None))
            elif tag == "!":
                if body and body[-1][0] == "warn":
                    merged = body[-1][1] + ([text] if text else [])
                    body[-1] = ("warn", merged, None)
                else:
                    flush()
                    body.append(("warn", [text] if text else [], None))
            elif tag == "?":
                questions.append(text)
            continue
        # 여러 줄 접기 설명의 이어지는 줄:  #(1)> 또는 #(1:3)> ...
        cont = CONT_RE.match(raw)
        if cont:
            num, span, text = cont.group(1), cont.group(2), cont.group(3).rstrip()
            if num not in notes:
                notes[num] = []
                note_order.append(num)
                if code:
                    # 직전의 비어있지 않은 코드 줄 위치를 찾는다.
                    last = None
                    for i in range(len(code) - 1, -1, -1):
                        if code[i].strip():
                            last = i
                            break
                    if last is not None:
                        n_lines = int(span) if span else 1
                        # last 줄 포함해서 위로 n_lines 개를 강조
                        for j in range(last - n_lines + 1, last + 1):
                            if 0 <= j < len(code):
                                mark_hl(j + 1)
            if text:
                notes[num].append(text)
            continue
        # snippet 모드에서는 구간 밖의 코드는 노트에 넣지 않는다.
        if snippet_mode and not in_region:
            continue
        if not raw.strip() and not code:
            continue
        # 코드 줄 끝의 접이식 주석 마커:  code  #(1) 또는 #(1:3) 짧은 설명
        inl = INLINE_RE.match(raw)
        if inl and inl.group(1).strip():
            code_part = inl.group(1).rstrip()
            num, span, note_text = inl.group(2), inl.group(3), inl.group(4).strip()
            code.append(code_part)   # 마커 텍스트는 코드에서 제거
            n_lines = int(span) if span else 1
            cur = len(code)          # 1-based 현재 줄
            for j in range(cur - n_lines + 1, cur + 1):
                if j >= 1:
                    mark_hl(j)
            if num not in notes:
                notes[num] = []
                note_order.append(num)
            if note_text:
                notes[num].append(note_text)
            continue
        code.append(raw)
    flush()
    return body, [], questions


def render(path, meta, body, stuck, questions):
    title = meta.get("title", path.stem)
    out = ["---", f"title: {title}"]
    out.append(f"date: {meta.get('date', datetime.date.today().isoformat())}")
    if "tags" in meta:
        out.append(f"tags: {meta['tags']}")
    out.append("---")
    out.append("")
    out.append(f"# {title}")
    out.append("")
    out.append(f"> 원본 코드: [`{path.name}`]({path.name})")
    out.append("")

    for kind, a, b in body:
        if kind == "head":
            out.append(f"## {a}")
            out.append("")
        elif kind == "prose":
            out.append(a)
            out.append("")
        elif kind == "warn":
            # 여러 줄을 하나의 warning 박스로. 위치는 이 자리(대개 코드 바로 밑).
            out.append("!!! warning")
            for i, line in enumerate(a):
                suffix = "  " if i < len(a) - 1 else ""
                out.append(f"    {line}{suffix}")
            out.append("")
        else:
            hl, notes = b
            fence = "```python"
            if hl:
                fence += ' hl_lines="%s"' % " ".join(str(n) for n in hl)
            out.append(fence)
            out.extend(a)
            out.append("```")
            out.append("")
            # 코드 밑에 접이식(클릭하면 펼쳐지는) 박스로 설명을 넣는다.
            for num, note_text in notes:
                parts = [p.strip() for p in note_text.split("<br>") if p.strip()]
                if not parts:
                    continue
                summary = parts[0]
                out.append(f'??? note "{summary}"')
                rest = parts[1:] if len(parts) > 1 else []
                if rest:
                    for i, line in enumerate(rest):
                        suffix = "  " if i < len(rest) - 1 else ""
                        out.append(f"    {line}{suffix}")
                else:
                    # 한 줄짜리면 제목만으론 허전하니 본문에도 한 번 더
                    out.append(f"    {summary}")
                out.append("")

    if questions:
        out.append("## 다시 볼 것")
        out.append("")
        for q in questions:
            out.append(f"- [ ] {q}")
        out.append("")

    return "\n".join(out)


def convert(path):
    src = path.read_text(encoding="utf-8")
    meta, skip = read_meta(src)
    # title 이 비어 있으면 아직 안 쓴 템플릿이므로 노트를 만들지 않는다.
    if not meta.get("title", "").strip():
        return None
    body, stuck, questions = parse(src, skip)
    target = path.with_suffix(".md")
    target.write_text(render(path, meta, body, stuck, questions), encoding="utf-8")
    return target


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("사용법: python py2md.py <파일.py> [...]")
    for arg in sys.argv[1:]:
        p = pathlib.Path(arg)
        if p.suffix == ".py" and p.name != "py2md.py":
            result = convert(p)
            if result:
                print("생성:", result)
            else:
                print("건너뜀 (title 비어 있음):", p)