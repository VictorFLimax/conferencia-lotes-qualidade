"""Runner Playwright (sync) — login + formulário de lote."""
from __future__ import annotations

import logging

from playwright.sync_api import sync_playwright

from src.artifacts import pasta_screenshots
from src.config import Config
from src.pages.FormPagePlaywright import FormPagePlaywright
from src.pages.LoginPagePlaywright import LoginPage

logger = logging.getLogger(__name__)


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
        browser = p.chromium.launch(headless=config.playwright_headless)
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
