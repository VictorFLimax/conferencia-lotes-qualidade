"""
Testes de login (Selenium) contra a página real login.html.

Pré-requisito: servidor local rodando na pasta dos arquivos .html, ex.:
    python -m http.server 8000
"""
from src.pages.LoginPageSelenium import LoginPageSelenium


def test_login_com_dados_validos_mostra_sucesso(selenium_driver, login_url):
    selenium_driver.get(login_url)
    login_page = LoginPageSelenium(selenium_driver)

    login_page.fazer_login("usuario.teste@empresa.com", "senha123")

    assert login_page.is_login_sucesso(), (
        "A mensagem de sucesso não apareceu após login com usuário e senha preenchidos."
    )


def test_login_com_campos_vazios_mostra_erro(selenium_driver, login_url):
    selenium_driver.get(login_url)

    # Remove o 'required' do HTML via JS para conseguir submeter o form vazio
    # e validar a mensagem de erro customizada da página.
    selenium_driver.execute_script(
        "document.getElementById('usuario').removeAttribute('required');"
        "document.getElementById('senha').removeAttribute('required');"
    )

    login_page = LoginPageSelenium(selenium_driver)
    login_page.fazer_login("", "")

    assert login_page.is_login_erro(), (
        "A mensagem de erro não apareceu ao tentar logar com campos vazios."
    )