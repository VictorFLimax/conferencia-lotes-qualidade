import pytest
from src.web_automation_playwright import preencher_lote


@pytest.mark.e2e
def test_preencher_lote_sucesso(login_url, lote_url):
    dados_lote = {
        "numero_lote": "LOTE_TESTE_01",
        "codigo_produto": "PROD_01",
        "quantidade": "100",
        "data_fabricacao": "2026-01-01",
        "data_validade": "2026-12-31",
        "status": "APROVADO",
    }

    config = {
        "url_login": login_url,
        "url_form": lote_url,
        "headless": True
    }

    resultado = preencher_lote(dados_lote, login_url)
    assert resultado is not None