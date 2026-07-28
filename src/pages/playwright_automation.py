import json
import logging
import asyncio
from playwright.async_api import async_playwright
from src.pages.form_page_playwright import FormPagePlaywright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run():
    with open('datapool.json', 'r', encoding='utf-8') as f:
        lotes = json.load(f)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=400)
        page = await browser.new_page()
        await page.goto("http://localhost:8000/lote-teste.html")

        form_page = FormPagePlaywright(page)

        for dados in lotes:
            logger.info(f"--- Processando Lote: {dados['numero_lote']} ---")
            await form_page.preencher_formulario(dados)
            await form_page.is_sucesso(dados['numero_lote'])
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
