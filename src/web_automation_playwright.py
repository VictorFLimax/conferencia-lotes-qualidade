"""
Fachada de automação Playwright encapsulando o uso das páginas POM.
"""
import logging
from playwright.sync_api import sync_playwright

from src.pages.LoginPagePlaywright import LoginPagePlaywright
from src.pages.FormPagePlaywright import FormPagePlaywright

logger = logging.getLogger(__name__)


class WebAutomationSession:
    """Gerencia o ciclo de vida do navegador (1 login por execução)."""

    def __init__(self, config):
        self.config = config
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        # Usa headless da config se existir, padrão True para produção
        headless = getattr(self.config, "web_headless", True)
        self.browser = self.playwright.chromium.launch(headless=headless)
        self.page = self.browser.new_page()
        
        url = getattr(self.config, "web_automation_url", "http://localhost:8000/login.html")
        self.page.goto(url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()


def fazer_login(page, usuario: str, senha: str) -> None:
    """Instancia a LoginPagePlaywright e realiza autenticação única."""
    logger.info("--- Iniciando Autenticação (Playwright POM) ---")
    login_page = LoginPagePlaywright(page)
    login_page.fazer_login(usuario, senha)


def preencher_lote(page, dados: dict, config) -> dict:
    """
    Executa o preenchimento de 1 lote na fila utilizando a FormPagePlaywright.
    """
    numero_lote = dados.get("numero_lote", "desconhecido")
    logger.info("--- Processando Lote no FormPage: %s ---", numero_lote)

    # Navega/garante que está na tela do formulário
    url_form = getattr(config, "web_form_url", "http://localhost:8000/lote-teste.html")
    page.goto(url_form)

    # Executa interações via POM
    form_page = FormPagePlaywright(page)
    form_page.preencher_formulario(dados)
    form_page.is_sucesso(numero_lote)

    # Tira a foto de evidência
    caminho_evidencia = f"artefatos/aprovado-{numero_lote}.png"
    page.screenshot(path=caminho_evidencia)

    return {"screenshot": caminho_evidencia}