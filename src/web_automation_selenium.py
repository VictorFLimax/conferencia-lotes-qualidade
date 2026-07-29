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
    Automação para preencher o formulário de cadastro de lote usando Selenium.
    """
    logger.info("[Automação] Iniciando o Selenium WebDriver...")
    
    driver = webdriver.Chrome()
    driver.implicitly_wait(2)
    wait = WebDriverWait(driver, 5)

    try:
        logger.info(f"🌐 [Automação] Acessando: {url}")
        driver.get(url)

        # 1. Campo 'Número do Lote' (id="lote")
        logger.info(f"[Automação] Inserindo Lote: {dados_lote['numero_lote']}")
        campo_lote = wait.until(EC.element_to_be_clickable((By.ID, "lote")))
        campo_lote.clear()
        campo_lote.send_keys(dados_lote["numero_lote"])

        # 2. Select 'Produto' (id="produto")
        logger.info(f"[Automação] Selecionando Produto ID: {dados_lote['produto_id']}")
        campo_produto = driver.find_element(By.ID, "produto")
        select = Select(campo_produto)
        select.select_by_value(str(dados_lote["produto_id"]))

        # 3. Radio Button por valor (name="status" e value="...")
        logger.info(f"[Automação] Definindo Status: {dados_lote['status']}")
        status_valor = dados_lote["status"].lower() # ex: 'pendente', 'processamento', 'concluido'
        radio_button = driver.find_element(By.CSS_SELECTOR, f"input[name='status'][value='{status_valor}']")
        if not radio_button.is_selected():
            radio_button.click()

        # 4. Botão de Envio (button[type='submit'])
        logger.info("[Automação] Enviando formulário...")
        btn_submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        btn_submit.click()

        # 5. Aguardar mensagem de sucesso ficar visível (id="mensagemSucesso" com classe ".show")
        logger.info("[Automação] Aguardando confirmação do sistema...")
        wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#mensagemSucesso.show"))
        )
        
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