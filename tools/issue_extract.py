#!/usr/bin/env python3
"""실습 .py에서 `#@@@ 주제` 마커를 뽑아 GitHub 이슈 생성 목록(JSON)을 만든다.

중복 방지: 파일경로+주제로 만든 fingerprint를 이슈 본문에 심고,
이미 열려 있거나 닫힌 이슈에 같은 fingerprint가 있으면 건너뛴다.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

MARK_RE = re.compile(r"^\s*#@@@\s+(.*)$")


def fingerprint(path, topic):
    key = f"{path.as_posix()}::{topic.lower()}"
    return "til-" + hashlib.sha1(key.encode()).hexdigest()[:10]


def existing_fingerprints():
    """gh로 열림/닫힘 모든 이슈 본문에서 fingerprint를 수집한다."""
    try:
        raw = subprocess.check_output(
            ["gh", "issue", "list", "--state", "all",
             "--limit", "500", "--json", "body"],
            text=True,
        )
    except Exception:
        return set()
    found = set()
    for item in json.loads(raw):
        for fp in re.findall(r"til-[0-9a-f]{10}", item.get("body") or ""):
            found.add(fp)
    return found


def collect(paths):
    items = []
    for path in paths:
        for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            m = MARK_RE.match(raw)
            if m:
                topic = m.group(1).strip()
                items.append({
                    "topic": topic,
                    "path": path.as_posix(),
                    "line": lineno,
                    "fp": fingerprint(path, topic),
                })
    return items


def build(paths):
    seen = existing_fingerprints()
    new = []
    for it in collect(paths):
        if it["fp"] in seen:
            continue
        seen.add(it["fp"])  # 같은 실행 내 중복도 방지
        body = (
            f"실습 중 더 알아보기로 표시한 주제입니다.\n\n"
            f"- 출처: `{it['path']}` (line {it['line']})\n\n"
            f"<!-- {it['fp']} -->"
        )
        new.append({
            "title": f"[공부] {it['topic']}",
            "body": body,
            "labels": ["til-todo"],
        })
    return new


if __name__ == "__main__":
    paths = [pathlib.Path(a) for a in sys.argv[1:] if a.endswith(".py")]
    print(json.dumps(build(paths), ensure_ascii=False, indent=2))
