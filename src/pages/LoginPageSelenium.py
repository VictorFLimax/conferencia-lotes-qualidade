"""Page Object — Login (Selenium)."""
from __future__ import annotations

import logging

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)

class LoginPageSelenium:
    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.usuario_input = (By.ID, "usuario")
        self.senha_input = (By.ID, "senha")
        self.login_button = (By.CSS_SELECTOR, "button.btn-submit")
        self.msg_sucesso = (By.ID, "mensagemSucesso")
        self.msg_erro = (By.ID, "mensagemErro")

    def fazer_login(self, usuario: str, senha: str) -> None:
        logger.info("[Selenium] Preenchendo credenciais de login...")
        url_inicial = self.driver.current_url

        self.wait.until(EC.visibility_of_element_located(self.usuario_input))
        campo_usuario = self.driver.find_element(*self.usuario_input)
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        campo_senha = self.driver.find_element(*self.senha_input)
        campo_senha.clear()
        campo_senha.send_keys(senha)

        self.driver.find_element(*self.login_button).click()
        self.wait.until(EC.url_changes(url_inicial))
        logger.info("[Selenium] Login concluído.")
