import json
import logging
import sys
import os

# Adiciona a raiz do projeto ao sys.path para reconhecer a pasta 'src'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from playwright.sync_api import sync_playwright

from src.pages.LoginPagePlaywright import LoginPagePlaywright
from src.pages.FormPagePlaywright import FormPagePlaywright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def run():
    # 1. Carrega o DataPool (certifique-se de ter o arquivo datapool.json)
    with open('datapool.json', 'r', encoding='utf-8') as f:
        lotes = json.load(f)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=400)
        page = browser.new_page()
        
        # 2. Navega para a tela de Login inicial (Ajuste a URL)
        page.goto("http://localhost:8000/login.html")

        # 3. Instancia as páginas
        login_page = LoginPagePlaywright(page)
        form_page = FormPagePlaywright(page)

        # 4. Faz o login (síncrono)
        logger.info("--- Iniciando Autenticação (Playwright) ---")
        login_page.fazer_login("admin", "123456")

        # Se após o login você precisa ir manualmente para a tela do formulário:
        page.goto("http://localhost:8000/lote-teste.html")

        # 5. Executa o loop do DataPool
        for dados in lotes:
            logger.info(f"--- Processando Lote: {dados['numero_lote']} ---")
            form_page.preencher_formulario(dados)
            form_page.is_sucesso(dados['numero_lote'])
            
            # Recarrega a página para limpar o formulário para o próximo lote
            page.goto("http://localhost:8000/lote-teste.html")

        browser.close()

if __name__ == "__main__":
    run()