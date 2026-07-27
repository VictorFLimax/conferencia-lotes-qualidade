import pytest
from web_automation import preencher_lote

def test_preencher_lote_sucesso():
    dados = {
        "numero_lote": "LOTE-TESTE-999",
        "produto_id": "2",
        "status": "concluido"
    }
    # Se a função executar sem levantar exceções, o teste passa
    preencher_lote(dados, url="http://localhost:8080/lote-teste.html")