from __future__ import annotations

import argparse
from pathlib import Path
import platform
import subprocess
import sys
import venv


MIN_PYTHON = (3, 11)
SETUP_DIR = Path(__file__).resolve().parent
VENV_DIR = SETUP_DIR / '.venv'
REQUIREMENTS_FILE = SETUP_DIR / 'requirements.txt'
MAIN_FILE = SETUP_DIR / 'main.py'


def get_venv_python(venv_dir: Path) -> Path:
    if platform.system() == 'Windows':
        return venv_dir / 'Scripts' / 'python.exe'
    return venv_dir / 'bin' / 'python'


def run_step(cmd: list[str], description: str) -> None:
    print(f'==> {description}...')
    subprocess.run(cmd, check=True)


def ensure_venv() -> Path:
    venv_python = get_venv_python(VENV_DIR)
    if venv_python.is_file():
        print(f'==> Ambiente virtual já encontrado em {VENV_DIR}')
        return venv_python

    print(f'==> Criando ambiente virtual em {VENV_DIR}...')
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(VENV_DIR)
    if not venv_python.is_file():
        raise RuntimeError(f'Não foi possível localizar o executável Python em {venv_python}.')
    return venv_python


def install_dependencies(venv_python: Path) -> None:
    if not REQUIREMENTS_FILE.is_file():
        raise FileNotFoundError(f'Arquivo não encontrado: {REQUIREMENTS_FILE}')
    run_step(
        [str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'],
        'Atualizando pip',
    )
    run_step(
        [str(venv_python), '-m', 'pip', 'install', '-r', str(REQUIREMENTS_FILE)],
        'Instalando dependências (PySide6)',
    )
    run_step(
        [str(venv_python), '-c', 'import PySide6; print("PySide6 OK:", PySide6.__version__)'],
        'Validando instalação do PySide6',
    )


def main() -> int:
    parser = argparse.ArgumentParser(description='Instalador das dependências do Setup.')
    parser.add_argument(
        '--run',
        action='store_true',
        help='Abre o Setup automaticamente após concluir a instalação.',
    )
    args = parser.parse_args()

    if sys.version_info < MIN_PYTHON:
        print(
            f'Erro: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ é obrigatório '
            f'(versão atual: {sys.version_info.major}.{sys.version_info.minor}).',
            file=sys.stderr,
        )
        return 1

    try:
        venv_python = ensure_venv()
        install_dependencies(venv_python)
    except (subprocess.CalledProcessError, OSError, RuntimeError) as exc:
        print(f'Erro durante a instalação: {exc}', file=sys.stderr)
        return 1

    print('\nInstalação concluída com sucesso!')
    if platform.system() == 'Windows':
        print('Para abrir o Setup, execute:\n  .venv\\Scripts\\python.exe main.py')
    else:
        print('Para abrir o Setup, execute:\n  .venv/bin/python3 main.py')

    if args.run:
        return subprocess.call([str(venv_python), str(MAIN_FILE)])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
