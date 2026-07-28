from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

        # Mapeamento dos elementos (Mapeados como atributos da instância)
        self.usuario_input = (By.ID, "user-name")
        self.senha_input = (By.ID, "password")
        self.login_button = (By.ID, "login-button")

    def fazer_login(self, usuario, senha):
        # Aguarda o campo de usuário ficar visível
        self.wait.until(EC.visibility_of_element_located(self.usuario_input))

        # Preenche o usuário
        self.driver.find_element(*self.usuario_input).clear()
        self.driver.find_element(*self.usuario_input).send_keys(usuario)

        # Preenche a senha
        self.driver.find_element(*self.senha_input).clear()
        self.driver.find_element(*self.senha_input).send_keys(senha)

        # Clica no botão de login
        self.driver.find_element(*self.login_button).click()

        # Aguarda a URL mudar após o login
        return self.wait.until(EC.url_changes(self.driver.current_url))