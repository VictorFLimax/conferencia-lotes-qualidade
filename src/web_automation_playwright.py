"""Compatibilidade: delega ao orquestrador web (Playwright/Selenium)."""
from __future__ import annotations

import os

from src.config import Config
from src.web import executar_automacao_web


def preencher_lote(dados_lote: dict, url: str | None = None) -> list[dict]:
    if url:
        os.environ["WEB_AUTOMATION_URL"] = url
    os.environ["WEB_AUTOMATION_ENABLED"] = "true"
    config = Config.carregar()
    return executar_automacao_web([dados_lote], config)
