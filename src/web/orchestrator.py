"""Orquestrador: escolhe Playwright ou Selenium conforme WEB_AUTOMATION_DRIVER."""
from __future__ import annotations

import logging

from src.config import Config

logger = logging.getLogger(__name__)


def executar_automacao_web(
    lotes: list[dict],
    config: Config,
    usuario: str | None = None,
    senha: str | None = None,
) -> list[dict]:
    """
    Executa a automação web com o driver definido no .env.

    WEB_AUTOMATION_DRIVER=playwright  → usa Playwright
    WEB_AUTOMATION_DRIVER=selenium    → usa Selenium
    """
    if not config.web_automation_enabled:
        logger.info("WEB_AUTOMATION_ENABLED=false — pulando automação web.")
        return []

    user = usuario or config.web_usuario
    password = senha or config.web_senha
    driver = config.web_automation_driver

    logger.info("Iniciando automação web com driver: %s", driver)

    if driver == "playwright":
        from src.web.playwright_runner import processar_lotes_playwright

        return processar_lotes_playwright(lotes, config, user, password)

    if driver == "selenium":
        from src.web.selenium_runner import processar_lotes_selenium

        return processar_lotes_selenium(lotes, config, user, password)

    raise ValueError(
        f"Driver não suportado: '{driver}'. Use WEB_AUTOMATION_DRIVER=playwright ou selenium."
    )
