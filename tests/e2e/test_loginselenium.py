import pytest
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.pages.LoginPageSelenium import LoginPage as LoginPageSelenium


@pytest.mark.e2e
def test_login_com_dados_validos_mostra_sucesso(selenium_driver, login_url):
    selenium_driver.get(login_url)
    login_page = LoginPageSelenium(selenium_driver)

    login_page.fazer_login("admin", "123456")

    # Aguarda o redirecionamento provocado pelo setTimeout(..., 1200) do HTML
    WebDriverWait(selenium_driver, 5).until(EC.url_contains("lote-teste.html"))
    assert "lote-teste.html" in selenium_driver.current_url