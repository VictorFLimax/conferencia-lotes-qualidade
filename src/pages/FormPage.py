from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select # Necessário para o select_by_visible_text

class FormPage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10) # Inicializamos o wait na página

        # Locators do formulário perfeitamente encapsulados
        self.input_numero_lote = (By.ID, "numero_lote")
        self.select_produto    = (By.ID, "produto")
        self.select_status     = (By.ID, "status")
        self.button_enviar     = (By.ID, "btn_enviar")
        self.msg_sucesso       = (By.ID, "mensagem_sucesso")

    def preencher_formulario(self, dados_lote: dict):
        # 1. Aguarda o primeiro campo do formulário ficar visível antes de interagir
        self.wait.until(EC.visibility_of_element_located(self.input_numero_lote))
        
        self.driver.find_element(*self.input_numero_lote).send_keys(dados_lote["numero_lote"])
        
        Select(self.driver.find_element(*self.select_produto)).select_by_visible_text(dados_lote["produto"])
        Select(self.driver.find_element(*self.select_status)).select_by_visible_text(dados_lote["status"])
        
        self.driver.find_element(*self.button_enviar).click()

    def is_sucesso(self) -> bool:
        # 2. A própria página aguarda a mensagem aparecer e diz ao orquestrador se deu certo
        try:
            elemento = self.wait.until(EC.visibility_of_element_located(self.msg_sucesso))
            return elemento.is_displayed()
        except Exception:
            # Se der timeout e não aparecer, retorna falso
            return False
