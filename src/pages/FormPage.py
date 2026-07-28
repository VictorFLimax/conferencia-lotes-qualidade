import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

# Configuração básica do logger para a página
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class FormPage:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

        # Locators perfeitamente encapsulados
        self.input_numero_lote = (By.ID, "numero_lote")
        self.select_produto    = (By.ID, "produto")
        self.select_status     = (By.ID, "status")
        self.button_enviar     = (By.ID, "btn_enviar")
        self.msg_sucesso       = (By.ID, "mensagem_sucesso")

    def preencher_formulario(self, dados_lote: dict):
        logger.info(f"[FormPage] Iniciando preenchimento do lote: {dados_lote.get('numero_lote')}")
        
        try:
            # Aguarda o primeiro campo ficar visível antes de interagir
            self.wait.until(EC.visibility_of_element_located(self.input_numero_lote))
            
            logger.info(f"[FormPage] Inserindo Lote: {dados_lote['numero_lote']}")
            self.driver.find_element(*self.input_numero_lote).send_keys(dados_lote["numero_lote"])
            
            logger.info(f"[FormPage] Selecionando Produto: {dados_lote['produto']}")
            Select(self.driver.find_element(*self.select_produto)).select_by_visible_text(dados_lote["produto"])
            
            logger.info(f"[FormPage] Definindo Status: {dados_lote['status']}")
            Select(self.driver.find_element(*self.select_status)).select_by_visible_text(dados_lote["status"])
            
            logger.info("[FormPage] Enviando formulário...")
            self.driver.find_element(*self.button_enviar).click()
            
        except Exception as e:
            logger.error(f"[FormPage] Falha durante o preenchimento do formulário: {e}")
            
            # Tira um snapshot em caso de erro na interação
            numero_lote = dados_lote.get('numero_lote', 'desconhecido')
            erro_snapshot = f"erro_preenchimento_{numero_lote}.png"
            self.driver.save_screenshot(erro_snapshot)
            logger.info(f"[FormPage] Snapshot de ERRO salvo como '{erro_snapshot}'.")
            
            # Repassa a exceção para que o orquestrador (main.py) saiba da falha
            raise e

    def is_sucesso(self, numero_lote: str = "desconhecido") -> bool:
        logger.info("[FormPage] Aguardando confirmação do sistema...")
        
        try:
            # Espera explícita pela mensagem de sucesso
            elemento = self.wait.until(EC.visibility_of_element_located(self.msg_sucesso))
            
            if elemento.is_displayed():
                logger.info("[FormPage] Lote cadastrado e verificado com sucesso!")
                
                # Snapshot de sucesso
                snapshot_path = f"sucesso_{numero_lote}.png"
                self.driver.save_screenshot(snapshot_path)
                logger.info(f"[FormPage] Snapshot de SUCESSO salvo como '{snapshot_path}'.")
                
                return True
                
        except Exception as e:
            logger.warning(f"[FormPage] A mensagem de sucesso não apareceu a tempo ou houve erro: {e}")
            
            # Snapshot para investigar por que falhou a validação
            falha_snapshot = f"falha_verificacao_{numero_lote}.png"
            self.driver.save_screenshot(falha_snapshot)
            logger.info(f"[FormPage] Snapshot de FALHA NA VALIDAÇÃO salvo como '{falha_snapshot}'.")
            
            return False
