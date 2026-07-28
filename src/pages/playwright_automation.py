import json
import logging
import asyncio
from playwright.async_api import async_playwright

# Importa as DUAS páginas de Playwright
from src.pages.login_page_playwright import LoginPagePlaywright
from src.pages.FormPagePlaywright import FormPagePlaywright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run():
    # 1. Carrega o DataPool
    with open('datapool.json', 'r', encoding='utf-8') as f:
        lotes = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=400)
        page = await browser.new_page()
        
        # 2. Navega para a tela de Login inicial
        await page.goto("https://sistema.exemplo.com/login")

        # 3. Instancia as páginas
        login_page = LoginPagePlaywright(page)
        form_page = FormPagePlaywright(page)

        # 4. Faz o login (FORA do loop, acontece apenas uma vez)
        logger.info("--- Iniciando Autenticação (Playwright) ---")
        await login_page.fazer_login("seu_usuario", "sua_senha")

        # 5. Executa o loop do DataPool chamando a FormPage
        for dados in lotes:
            logger.info(f"--- Processando Lote: {dados['numero_lote']} ---")
            await form_page.preencher_formulario(dados)
            await form_page.is_sucesso(dados['numero_lote'])
            
            # (Opcional) Recarregar a página ou clicar em "Novo Lote" para o próximo ciclo
            # await page.goto("URL_DO_FORMULARIO") 

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
