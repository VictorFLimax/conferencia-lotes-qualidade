"""
Testes do formulário de cadastro de lote (Selenium) contra lote-teste.html.
"""
from src.pages.FormPageSelenium import FormPageSelenium

DADOS_VALIDOS = {
    "numero_lote": "LOTE-TESTE-SELENIUM-0001",
    "produto_id": 1,       # Produto A
    "status": "processamento",
}


def test_cadastro_lote_com_sucesso(selenium_driver, lote_url):
    selenium_driver.get(lote_url)
    form_page = FormPageSelenium(selenium_driver)

    form_page.preencher_formulario(DADOS_VALIDOS)

    assert form_page.is_sucesso(DADOS_VALIDOS["numero_lote"]), (
        "A mensagem de sucesso do cadastro de lote não apareceu."
    )