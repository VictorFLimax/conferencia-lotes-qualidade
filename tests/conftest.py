import os
import sys
from unittest.mock import MagicMock

import pandas as pd
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


# ---------------------------------------------------------------------------
# Fixtures para Automação Web (Suas fixtures originais)
# ---------------------------------------------------------------------------
@pytest.fixture
def login_url():
    return f"{BASE_URL}/login.html"


@pytest.fixture
def lote_url():
    return f"{BASE_URL}/lote-teste.html"


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


# ---------------------------------------------------------------------------
# Fixtures para Regras de Negócio e Mocks (Requisito Seção 5.5 da Aula 23)
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_base_referencia():
    """
    Mock da Base_Referencia simulando um banco/sistema externo.
    Evita dependência de arquivo físico em disco para a lógica de validação.
    """
    mock = MagicMock()
    mock.obter_dados.return_value = pd.DataFrame([
        {"lote": "LOTE_001", "status_esperado": "APROVADO", "quantidade": 100},
        {"lote": "LOTE_002", "status_esperado": "REPROVADO", "quantidade": 50},
    ])
    return mock


@pytest.fixture
def sample_registro_valido():
    """Registro base válido para reuso nos testes unitários."""
    return {
        "lote": "LOTE_001",
        "data": "2026-08-18",
        "status": "OK",
        "quantidade": 100,
        "observacao": "Lote inspecionado sem anomalias"
    }


@pytest.fixture
def sample_dataframe_10dias():
    """DataFrame simulando o arquivo de entrada com os dados de inspeção."""
    return pd.DataFrame([
        {"dia": "Dia 1", "lote": "LOTE_001", "status": "OK", "quantidade": 100},
        {"dia": "Dia 2", "lote": "LOTE_002", "status": "NOK", "quantidade": 50}
    ])