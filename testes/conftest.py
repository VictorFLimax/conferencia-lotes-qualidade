import os
import sys

import pytest

# Garante que 'src' seja importável (ex.: from src.pages.FormPageSelenium import ...)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# URL base onde login.html e lote-teste.html estão sendo servidos.
# Rode um servidor local antes dos testes, por exemplo:
#   python -m http.server 8000
# a partir da pasta que contém os dois arquivos .html.
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

# Defina HEADLESS=true para rodar sem abrir janela do navegador (ex.: em CI).
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


@pytest.fixture
def login_url():
    return f"{BASE_URL}/login.html"


@pytest.fixture
def lote_url():
    return f"{BASE_URL}/lote-teste.html"


# ---------------------------------------------------------------------------
# Selenium
# ---------------------------------------------------------------------------
@pytest.fixture
def selenium_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1280,900")

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

@pytest.fixture
def playwright_page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=HEADLESS, slow_mo=0 if HEADLESS else 200)
        page = browser.new_page()
        yield page
        browser.close()