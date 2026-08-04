import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class LoginPageSelenium:
    """
    Page Object para login.html (Selenium).

    Locators alinhados com o HTML real da tela de login:
      - input#usuario
      - input#senha
      - button.btn-submit (o botão não possui id)
      - div#mensagemSucesso / div#mensagemErro
    """

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

        self.usuario_input = (By.ID, "usuario")
        self.senha_input = (By.ID, "senha")
        self.login_button = (By.CSS_SELECTOR, "button.btn-submit")
        self.msg_sucesso = (By.ID, "mensagemSucesso")
        self.msg_erro = (By.ID, "mensagemErro")

    def fazer_login(self, usuario: str, senha: str):
        logger.info("[LoginPage-Selenium] Preenchendo credenciais de login...")
        self.wait.until(EC.visibility_of_element_located(self.usuario_input))

        campo_usuario = self.driver.find_element(*self.usuario_input)
        campo_usuario.clear()
        campo_usuario.send_keys(usuario)

        campo_senha = self.driver.find_element(*self.senha_input)
        campo_senha.clear()
        campo_senha.send_keys(senha)

        logger.info("[LoginPage-Selenium] Clicando em 'Entrar'...")
        self.driver.find_element(*self.login_button).click()

    def is_login_sucesso(self) -> bool:
        try:
            elemento = self.wait.until(EC.visibility_of_element_located(self.msg_sucesso))
            return elemento.is_displayed()
        except Exception as e:
            logger.warning(f"[LoginPage-Selenium] Mensagem de sucesso não apareceu: {e}")
            return False

    def is_login_erro(self) -> bool:
        try:
            elemento = self.wait.until(EC.visibility_of_element_located(self.msg_erro))
            return elemento.is_displayed()
        except Exception as e:
            logger.warning(f"[LoginPage-Selenium] Mensagem de erro não apareceu: {e}")
            return False