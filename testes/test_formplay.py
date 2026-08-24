"""
Testes do formulário de cadastro de lote (Playwright) contra lote-teste.html.
"""
from src.pages.FormPagePlaywright import FormPagePlaywright

DADOS_VALIDOS = {
    "numero_lote": "LOTE-TESTE-PLAYWRIGHT-0001",
    "produto_id": 2,
    "status": "concluido",
}

def test_cadastro_lote_com_sucesso(playwright_page, lote_url):
    playwright_page.goto(lote_url)
    form_page = FormPagePlaywright(playwright_page)

    form_page.preencher_formulario(DADOS_VALIDOS)

    assert form_page.is_sucesso(DADOS_VALIDOS["numero_lote"]), (
        "A mensagem de sucesso do cadastro de lote não apareceu."
    )