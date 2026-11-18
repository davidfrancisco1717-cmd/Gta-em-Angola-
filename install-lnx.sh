#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 install.py
else
  echo "Python 3 nao encontrado. Instale Python 3.11+ e tente novamente."
  exit 1
fi
