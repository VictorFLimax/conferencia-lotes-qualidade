"""
Fachada de automação Selenium encapsulando o uso das páginas POM.
"""
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from src.pages.LoginPageSelenium import LoginPageSelenium
from src.pages.FormPageSelenium import FormPageSelenium

logger = logging.getLogger(__name__)


class WebAutomationSessionSelenium:
    """Gerencia o ciclo de vida do navegador Selenium (1 login por execução)."""

    def __init__(self, config):
        self.config = config
        self.driver = None

    def __enter__(self):
        chrome_options = Options()
        if getattr(self.config, "web_headless", True):
            chrome_options.add_argument("--headless=new")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)

        url = getattr(self.config, "web_automation_url", "http://localhost:8000/login.html")
        self.driver.get(url)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()


def fazer_login(driver, usuario: str, senha: str) -> None:
    """Instancia a LoginPageSelenium e realiza a autenticação."""
    logger.info("--- Iniciando Autenticação (Selenium POM) ---")
    login_page = LoginPageSelenium(driver)
    login_page.fazer_login(usuario, senha)


def preencher_lote(driver, dados: dict, config) -> dict:
    """
    Executa o preenchimento de 1 lote na fila utilizando a FormPageSelenium.
    """
    numero_lote = dados.get("numero_lote", "desconhecido")
    logger.info("--- Processando Lote no FormPage (Selenium): %s ---", numero_lote)

    url_form = getattr(config, "web_form_url", "http://localhost:8000/lote-teste.html")
    driver.get(url_form)

    form_page = FormPageSelenium(driver)
    form_page.preencher_formulario(dados)
    form_page.is_sucesso(numero_lote)

    caminho_evidencia = f"artefatos/aprovado-{numero_lote}.png"
    driver.save_screenshot(caminho_evidencia)

    return {"screenshot": caminho_evidencia}