"""
Testes de login (Playwright) contra a página real login.html.

Pré-requisitos:
    pip install playwright pytest-asyncio
    playwright install chromium
    python -m http.server 8000   (na pasta dos arquivos .html)
"""
from src.pages.LoginPagePlaywright import LoginPagePlaywright


def test_login_com_dados_validos_mostra_sucesso(playwright_page, login_url):
    playwright_page.goto(login_url)
    playwright_page.fill("#usuario", "admin")
    playwright_page.fill("#senha", "123456")
    playwright_page.click("button[type='submit']")
    
    assert playwright_page.is_visible("#mensagemSucesso")
