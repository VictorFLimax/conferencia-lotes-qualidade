import pytest
import requests
from src.web_automation_selenium import preencher_lote


@pytest.mark.e2e
def test_preencher_lote_sucesso(lote_url):
    """
    Testa o preenchimento com sucesso do formulário usando a automação em Selenium.
    """
    dados = {
        "numero_lote": "LOTE-TESTE-999",
        "produto_id": "2",
        "status": "concluido"
    }

    # Verifica se o servidor local está ativo antes de rodar o teste E2E
    try:
        response = requests.get(lote_url, timeout=2)
        if response.status_code != 200:
            pytest.skip(f"Servidor web indisponível na URL: {lote_url}")
    except Exception:
        pytest.skip(f"Servidor local não está rodando em {lote_url}. Inicie com 'python -m http.server 8000'")

    # Se a função executar sem levantar exceções, o teste passa
    preencher_lote(dados, url=lote_url)