import pytest
from src.web_automation_playwright import preencher_lote

@pytest.mark.asyncio
async def test_preencher_lote_playwright_sucesso():
    """
    Testa o preenchimento com sucesso do formulário usando a automação em Playwright.
    """
    dados_teste = {
        "numero_lote": "LOTE-PLAYWRIGHT-001",
        "produto_id": "1",          
        "status": "processamento"   
    }

    url_teste = "http://localhost:8080/lote-teste.html"

    await preencher_lote(dados_lote=dados_teste, url=url_teste)