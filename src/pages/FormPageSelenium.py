import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

logger = logging.getLogger(__name__)

class FormPageSelenium:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

        # Locators ajustados exatamente ao HTML de lote-teste.html
        self.input_numero_lote = (By.ID, "lote")
        self.select_produto    = (By.ID, "produto")
        self.button_enviar     = (By.CSS_SELECTOR, "button[type='submit']")
        self.msg_sucesso       = (By.ID, "mensagemSucesso")

    def preencher_formulario(self, dados_lote: dict):
        """
        Preenche o formulário de cadastro de lote.
        Aceita tanto 'produto' quanto 'produto_id' no dicionário.
        """
        logger.info(f"[FormPage] Iniciando preenchimento do lote: {dados_lote.get('numero_lote')}")
        
        try:
            # 1. Inserir Número do Lote
            self.wait.until(EC.visibility_of_element_located(self.input_numero_lote))
            logger.info(f"[FormPage] Inserindo Lote: {dados_lote['numero_lote']}")
            elem_lote = self.driver.find_element(*self.input_numero_lote)
            elem_lote.clear()
            elem_lote.send_keys(dados_lote["numero_lote"])
            
            # 2. Selecionar Produto (Dropdown) - Trata a chave de forma segura
            produto_val = dados_lote.get("produto") or dados_lote.get("produto_id")
            if produto_val is None:
                raise KeyError("O dicionário 'dados_lote' precisa conter a chave 'produto' ou 'produto_id'.")

            logger.info(f"[FormPage] Selecionando Produto: {produto_val}")
            select_elem = Select(self.driver.find_element(*self.select_produto))
            try:
                select_elem.select_by_value(str(produto_val))
            except Exception:
                select_elem.select_by_visible_text(str(produto_val))
            
            # 3. Selecionar Status (Radio Buttons)
            status_valor = dados_lote.get("status", "pendente").lower()
            logger.info(f"[FormPage] Definindo Status: {status_valor}")
            radio_locator = (By.CSS_SELECTOR, f"input[name='status'][value='{status_valor}']")
            self.driver.find_element(*radio_locator).click()
            
            # 4. Enviar formulário
            logger.info("[FormPage] Enviando formulário...")
            self.driver.find_element(*self.button_enviar).click()
            
        except Exception as e:
            logger.error(f"[FormPage] Falha durante o preenchimento do formulário: {e}")
            
            # Snapshot em caso de erro
            numero_lote = dados_lote.get("numero_lote", "desconhecido")
            erro_snapshot = f"erro_preenchimento_{numero_lote}.png"
            self.driver.save_screenshot(erro_snapshot)
            logger.info(f"[FormPage] Snapshot de ERRO salvo como '{erro_snapshot}'.")
            
            raise e

    def is_sucesso(self, numero_lote: str = "desconhecido") -> bool:
        logger.info("[FormPage] Aguardando confirmação do sistema...")
        
        try:
            # Espera até que a div #mensagemSucesso fique visível
            elemento = self.wait.until(EC.visibility_of_element_located(self.msg_sucesso))
            
            classes = elemento.get_attribute("class") or ""
            if "show" in classes:
                logger.info("[FormPage] Lote cadastrado e verificado com sucesso!")
                
                snapshot_path = f"sucesso_{numero_lote}.png"
                self.driver.save_screenshot(snapshot_path)
                logger.info(f"[FormPage] Snapshot de SUCESSO salvo como '{snapshot_path}'.")
                
                return True
            else:
                logger.warning("[FormPage] O elemento de mensagem existe mas não possui a classe 'show'.")
                return False
                
        except Exception as e:
            logger.warning(f"[FormPage] A mensagem de sucesso não apareceu a tempo ou houve erro: {e}")
            
            falha_snapshot = f"falha_verificacao_{numero_lote}.png"
            self.driver.save_screenshot(falha_snapshot)
            logger.info(f"[FormPage] Snapshot de FALHA NA VALIDAÇÃO salvo como '{falha_snapshot}'.")
            
            return False