import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def preencher_lote(dados_lote: dict, url: str = "http://localhost:8000/lote-teste.html"):
    """
    Automação para preencher o formulário de cadastro de lote usando Selenium e IDs simples.
    """
    logger.info("[Automação] Iniciando o Selenium WebDriver...")
    
    driver = webdriver.Chrome()
    driver.implicitly_wait(2)
    wait = WebDriverWait(driver, 5)

    try:
        logger.info(f"🌐 [Automação] Acessando: {url}")
        driver.get(url)

        # 1. Campo 'Número do Lote'
        logger.info(f"[Automação] Inserindo Lote: {dados_lote['numero_lote']}")
        campo_lote = wait.until(EC.element_to_be_clickable((By.ID, "lote"))) # <-- Altere 'lote' se necessário
        campo_lote.clear()
        campo_lote.send_keys(dados_lote["numero_lote"])

        # 2. Select 'Produto'
        logger.info(f"[Automação] Selecionando Produto ID: {dados_lote['produto_id']}")
        campo_produto = driver.find_element(By.ID, "produto") # <-- Altere 'produto' se necessário
        select = Select(campo_produto)
        select.select_by_value(str(dados_lote["produto_id"]))

        # 3. Radio Button
        logger.info(f"[Automação] Definindo Status: {dados_lote['status']}")
        # Mapeia a chave dos dados para o ID exato do radio no HTML
        status_id_map = {
            "pendente": "status_pendente",       # <-- Altere o ID do HTML
            "processamento": "status_processando", # <-- Altere o ID do HTML
            "concluido": "status_concluido"     # <-- Altere o ID do HTML
        }
        id_radio = status_id_map.get(dados_lote["status"].lower(), "status_pendente")
        radio_button = driver.find_element(By.ID, id_radio)
        if not radio_button.is_selected():
            radio_button.click()

        # 4. Botão de Envio
        logger.info("[Automação] Enviando formulário...")
        btn_submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")) # Ou use (By.ID, "btn-processar")
        )
        btn_submit.click()

        # 5. Aguardar mensagem de sucesso
        logger.info("[Automação] Aguardando confirmação do sistema...")
        wait.until(
            EC.visibility_of_element_located((By.ID, "mensagemSucesso")) # <-- Altere o ID do elemento da mensagem
        )
        
        # =========================================================

        logger.info("[Automação] Lote cadastrado e verificado com sucesso!")

        # Snapshot de Sucesso
        snapshot_path = f"sucesso_{dados_lote['numero_lote']}.png"
        driver.save_screenshot(snapshot_path)
        logger.info(f"[Automação] Snapshot de SUCESSO salvo como '{snapshot_path}'.")

    except Exception as e:
        logger.error(f"[Automação] Falha na execução da rotina: {e}")
        
        try:
            erro_snapshot = f"erro_execucao_{dados_lote['numero_lote']}.png"
            driver.save_screenshot(erro_snapshot)
            logger.info(f"[Automação] Snapshot de ERRO salvo como '{erro_snapshot}'.")
        except Exception as snap_error:
            logger.error(f"[Automação] Não foi possível salvar o snapshot de erro: {snap_error}")
        
        raise e
        
    finally:
        logger.info("[Automação] Fechando o navegador.")
        driver.quit()