# Setup — Editor Local de Histórias

Aplicação desktop multiplataforma (Windows, macOS e Linux) para criar, editar e validar histórias, personagens, itens, missões e locais sem editar arquivos Markdown manualmente.

## Pré-requisitos

- Python 3.11 ou superior

## Instalação e execução

### Instalação e abertura por duplo clique

| Sistema | Instalar dependências | Abrir o Setup | Desinstalar dependências |
|---|---|---|---|
| Windows | `install-win.bat` | `setup-gta-win.bat` | `uninstall-win.bat` |
| macOS | `install-mac.command` | `setup-gta-mac.command` | `uninstall-mac.command` |
| Linux | `install-lnx.sh` | `setup-gta-lnx.sh` | `uninstall-lnx.sh` |

### Instalação automática via terminal (Windows, macOS e Linux)

Entre na pasta `setup` e execute o instalador:

```bash
cd setup
python3 install.py        # macOS / Linux (ou "py install.py" no Windows)
```

Para instalar e já abrir a aplicação em seguida:

```bash
python3 install.py --run
```

### Instalação manual (opcional)

#### macOS / Linux

```bash
cd setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

#### Windows (PowerShell)

```powershell
cd setup
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## Testes automatizados (camada de domínio e validação)

```bash
python3 -m unittest discover -s setup/tests
```
