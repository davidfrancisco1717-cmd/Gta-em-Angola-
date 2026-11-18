from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


SETUP_DIR = Path(__file__).resolve().parent
VENV_DIR = SETUP_DIR / '.venv'


def remove_pycache(root: Path) -> int:
    removed = 0
    for cache_dir in list(root.rglob('__pycache__')):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
            removed += 1
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Remove o ambiente virtual (.venv) e as dependências instaladas pelo Setup (não remove o Python).',
    )
    parser.add_argument(
        '-y',
        '--yes',
        action='store_true',
        help='Confirma a remoção sem perguntar.',
    )
    args = parser.parse_args()

    if not VENV_DIR.exists():
        removed_caches = remove_pycache(SETUP_DIR)
        print('Nenhuma dependência instalada encontrada (.venv não existe).')
        if removed_caches:
            print(f'Caches Python removidos: {removed_caches}.')
        return 0

    if not args.yes:
        reply = input(
            f'Isso removerá o ambiente virtual e as dependências em "{VENV_DIR}" (o Python do sistema será mantido).\n'
            'Deseja continuar? (S/N): '
        ).strip().lower()
        if reply not in ('s', 'sim', 'y', 'yes'):
            print('Desinstalação cancelada.')
            return 0

    try:
        shutil.rmtree(VENV_DIR)
        remove_pycache(SETUP_DIR)
    except OSError as exc:
        print(f'Erro ao remover dependências: {exc}', file=sys.stderr)
        return 1

    print('Dependências e ambiente virtual (.venv) removidos com sucesso!')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
