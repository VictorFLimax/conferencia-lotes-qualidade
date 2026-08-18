import pytest
from src.pages.LoginPagePlaywright import LoginPage as LoginPagePlaywright


@pytest.mark.e2e
def test_login_com_dados_validos_mostra_sucesso(playwright_page, login_url):
    playwright_page.goto(login_url)

    login_page = LoginPagePlaywright(playwright_page)
    login_page.fazer_login("admin", "123456")

    # Espera a mensagem de sucesso aparecer ou o redirecionamento acontecer
    playwright_page.wait_for_selector("#mensagemSucesso.show, body", timeout=5000)
    
    # Aguarda a transição de página para lote-teste.html provocada pelo setTimeout do JS
    playwright_page.wait_for_url("**/lote-teste.html", timeout=5000)
    assert "lote-teste.html" in playwright_page.url