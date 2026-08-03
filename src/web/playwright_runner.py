"""Runner Playwright (sync) — login + formulário de lote."""
from __future__ import annotations

import logging
import subprocess
import sys

from playwright.sync_api import sync_playwright

from src.artifacts import pasta_screenshots
from src.config import Config
from src.pages.FormPagePlaywright import FormPagePlaywright
from src.pages.LoginPagePlaywright import LoginPage

logger = logging.getLogger(__name__)


def _instalar_chromium() -> bool:
    """Baixa o Chromium do Playwright (necessário na 1ª execução e no Runner)."""
    logger.info("[Playwright] Instalando Chromium (python -m playwright install)...")
    processo = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        capture_output=True,
        text=True,
    )
    if processo.returncode == 0:
        logger.info("[Playwright] Chromium instalado.")
        return True
    logger.error("[Playwright] Falha ao instalar Chromium: %s", processo.stderr.strip())
    return False


def _abrir_chromium(playwright, config: Config):
    try:
        return playwright.chromium.launch(headless=config.playwright_headless)
    except Exception as exc:
        navegador_ausente = "Executable doesn't exist" in str(exc)
        if not (navegador_ausente and config.playwright_auto_install):
            raise
        logger.warning("[Playwright] Navegador ausente — instalando automaticamente.")
        if not _instalar_chromium():
            raise
        return playwright.chromium.launch(headless=config.playwright_headless)


def processar_lotes_playwright(
    lotes: list[dict],
    config: Config,
    usuario: str,
    senha: str,
) -> list[dict]:
    """Processa uma lista de lotes no formulário web via Playwright."""
    resultados: list[dict] = []
    pasta_snaps = pasta_screenshots(config)

    with sync_playwright() as p:
        browser = _abrir_chromium(p, config)
        page = browser.new_page()
        try:
            logger.info("[Playwright] Abrindo: %s", config.web_automation_url)
            page.goto(config.web_automation_url)

            login = LoginPage(page)
            login.fazer_login(usuario, senha)

            if config.screenshot_enabled:
                form_tmp = FormPagePlaywright(page)
                form_tmp.tirar_screenshot(pasta_snaps / "login_ok_playwright.png")

            form = FormPagePlaywright(page)
            for dados in lotes:
                numero = str(dados.get("numero_lote") or dados.get("lote_id", "SEM_ID"))
                logger.info("[Playwright] Processando lote: %s", numero)
                try:
                    form.preencher_formulario(dados)
                    ok, snap = form.is_sucesso(
                        numero,
                        pasta_snapshots=pasta_snaps,
                        screenshot_enabled=config.screenshot_enabled,
                    )
                    resultados.append(
                        {
                            "numero_lote": numero,
                            "sucesso": ok,
                            "driver": "playwright",
                            "screenshot": str(snap) if snap else None,
                        }
                    )
                    page.reload()
                except Exception as exc:
                    logger.error("[Playwright] Erro no lote %s: %s", numero, exc)
                    snap = None
                    if config.screenshot_enabled:
                        snap = form.tirar_screenshot(
                            pasta_snaps / f"erro_excecao_playwright_{numero}.png"
                        )
                    resultados.append(
                        {
                            "numero_lote": numero,
                            "sucesso": False,
                            "driver": "playwright",
                            "erro": str(exc),
                            "screenshot": str(snap) if snap else None,
                        }
                    )
                    page.reload()
        finally:
            browser.close()

    return resultados
