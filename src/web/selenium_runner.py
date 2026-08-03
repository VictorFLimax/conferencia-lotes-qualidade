"""Runner Selenium — login + formulário de lote."""
from __future__ import annotations

import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.artifacts import pasta_screenshots
from src.config import Config
from src.pages.FormPageSelenium import FormPageSelenium
from src.pages.LoginPageSelenium import LoginPage

logger = logging.getLogger(__name__)


def _criar_driver(headless: bool) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280,900")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def processar_lotes_selenium(
    lotes: list[dict],
    config: Config,
    usuario: str,
    senha: str,
) -> list[dict]:
    """Processa uma lista de lotes no formulário web via Selenium."""
    resultados: list[dict] = []
    pasta_snaps = pasta_screenshots(config)

    driver = _criar_driver(config.selenium_headless)
    try:
        logger.info("[Selenium] Abrindo: %s", config.web_automation_url)
        driver.get(config.web_automation_url)

        login = LoginPage(driver)
        login.fazer_login(usuario, senha)

        form = FormPageSelenium(driver)
        if config.screenshot_enabled:
            form.tirar_screenshot(pasta_snaps / "login_ok_selenium.png")

        for dados in lotes:
            numero = str(dados.get("numero_lote") or dados.get("lote_id", "SEM_ID"))
            logger.info("[Selenium] Processando lote: %s", numero)
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
                        "driver": "selenium",
                        "screenshot": str(snap) if snap else None,
                    }
                )
                driver.refresh()
            except Exception as exc:
                logger.error("[Selenium] Erro no lote %s: %s", numero, exc)
                snap = None
                if config.screenshot_enabled:
                    snap = form.tirar_screenshot(
                        pasta_snaps / f"erro_excecao_selenium_{numero}.png"
                    )
                resultados.append(
                    {
                        "numero_lote": numero,
                        "sucesso": False,
                        "driver": "selenium",
                        "erro": str(exc),
                        "screenshot": str(snap) if snap else None,
                    }
                )
                driver.refresh()
    finally:
        driver.quit()

    return resultados
