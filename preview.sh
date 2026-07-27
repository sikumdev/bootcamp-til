#!/usr/bin/env bash
# 로컬에서 노트를 변환하고 사이트를 미리 봅니다.
# 사용법: ./preview.sh
set -e

files=$(find docs -name '*.py')
if [ -n "$files" ]; then
  python tools/py2md.py $files
fi

mkdocs serve
