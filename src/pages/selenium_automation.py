import sys
import os

# Adiciona a raiz do projeto ao sys.path para reconhecer a pasta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import logging
from selenium import webdriver

# Importa as duas Page Objects (Selenium)
from src.pages.LoginPageSelenium import LoginPageSelenium
from src.pages.FormPageSelenium import FormPageSelenium

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run():
    # 1. Carrega o DataPool
    with open('datapool.json', 'r', encoding='utf-8') as f:
        lotes = json.load(f)

    # 2. Inicializa o Chrome
    driver = webdriver.Chrome()
    driver.implicitly_wait(5)
    
    try:
        # 3. Navega para a tela de Login inicial
        driver.get("http://localhost:8000/login.html")

        # 4. Instancia as páginas
        login_page = LoginPageSelenium(driver)
        form_page = FormPageSelenium(driver)

        # 5. Faz o login (FORA do loop, acontece apenas uma vez)
        logger.info("--- Iniciando Autenticação (Selenium) ---")
        login_page.fazer_login("admin", "123456")

        # 6. Redireciona para a página do formulário de lote (se a aplicação não redirecionar automaticamente)
        driver.get("http://localhost:8000/lote-teste.html")

        # 7. Executa o loop do DataPool chamando a FormPage
        for dados in lotes:
            logger.info(f"--- Processando Lote (Selenium): {dados['numero_lote']} ---")
            form_page.preencher_formulario(dados)
            form_page.is_sucesso(dados['numero_lote'])
            
            # Recarrega a página para limpar o formulário para o próximo ciclo
            driver.get("http://localhost:8000/lote-teste.html")

    finally:
        driver.quit()

if __name__ == "__main__":
    run()