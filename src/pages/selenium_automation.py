import json
import logging
from selenium import webdriver
from src.pages.form_page_selenium import FormPageSelenium

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run():
    # Carrega o DataPool
    with open('datapool.json', 'r', encoding='utf-8') as f:
        lotes = json.load(f)

    driver = webdriver.Chrome()
    driver.get("http://localhost:8000/lote-teste.html")
    
    form_page = FormPageSelenium(driver)

    for dados in lotes:
        logger.info(f"--- Processando Lote: {dados['numero_lote']} ---")
        form_page.preencher_formulario(dados)
        form_page.is_sucesso(dados['numero_lote'])
        driver.refresh() 

    driver.quit()

if __name__ == "__main__":
    run()
