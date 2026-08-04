import pytest
from src.web_automation_playwright import preencher_lote


def test_preencher_lote_sucesso():
    """
    Testa o preenchimento com sucesso do formulário usando a automação em Selenium.
    """
    dados_teste = {
        "numero_lote": "LOTE-TESTE-999",
        "produto_id": "2",
        "status": "concluido"
    }

    url_teste = "http://localhost:8080/lote-teste.html"

    # A automação propaga exceções em caso de falha, então a ausência delas valida o fluxo
    preencher_lote(dados_lote=dados_teste, url=url_teste)
