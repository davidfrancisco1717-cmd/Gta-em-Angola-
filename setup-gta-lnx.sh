#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

if [ ! -f "../story/stories.json" ]; then
  echo "Erro: arquivo ../story/stories.json nao encontrado."
  echo "Mantenha a pasta setup dentro da pasta principal do jogo."
  exit 1
fi

NEED_INSTALL=0
if [ ! -x ".venv/bin/python3" ]; then
  NEED_INSTALL=1
elif ! .venv/bin/python3 -c "import PySide6" >/dev/null 2>&1; then
  NEED_INSTALL=1
fi

if [ "$NEED_INSTALL" -eq 1 ]; then
  echo "Ambiente ou dependencias (PySide6) ainda nao instalados."
  read -r -p "Deseja instalar agora? (S/N): " RESP
  case "$RESP" in
    [sS])
      if command -v python3 >/dev/null 2>&1; then
        python3 install.py || {
          echo "Falha durante a instalacao."
          exit 1
        }
      else
        echo "Python 3 nao encontrado. Instale Python 3.11+ e tente novamente."
        exit 1
      fi
      ;;
    *)
      echo "Instalacao cancelada. Execute install-lnx.sh quando desejar instalar."
      exit 1
      ;;
  esac
fi

if ! .venv/bin/python3 main.py; then
  echo ""
  echo "O Setup encerrou com erro. Veja os detalhes acima."
  read -r -p "Pressione ENTER para fechar..."
  exit 1
fi
