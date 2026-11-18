#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 uninstall.py
else
  echo "Python 3 nao encontrado."
fi
echo ""
read -r -p "Pressione ENTER para fechar..."
