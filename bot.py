"""
Ponto de entrada exigido pelo BotCity Runner / Easy Deploy.

Ao subir o ZIP no Maestro, o Runner executa este arquivo.
Documentação: https://documentation.botcity.dev/tutorials/custom-automations/python-custom/
"""
from __future__ import annotations

import sys
from pathlib import Path

# Garante imports do pacote src/ tanto no Runner quanto local
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
