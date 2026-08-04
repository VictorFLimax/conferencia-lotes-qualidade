"""Page Object — Formulário de lote (Selenium)."""
from __future__ import annotations

import logging
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

logger = logging.getLogger(__name__)


class FormPageSelenium:
    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver, timeout)
        self.input_numero_lote = (By.ID, "lote")
        self.select_produto = (By.ID, "produto")
        self.button_enviar = (By.CSS_SELECTOR, "button.btn-submit")
        self.msg_sucesso = (By.CSS_SELECTOR, "#mensagemSucesso.show")

    def preencher_formulario(self, dados_lote: dict) -> None:
        numero = str(dados_lote.get("numero_lote") or dados_lote.get("lote_id", ""))
        produto_id = str(
            dados_lote.get("produto_id")
            or dados_lote.get("codigo_produto")
            or dados_lote.get("produto")
            or "1"
        )
        status = str(dados_lote.get("status", "pendente")).lower()

        status_map = {
            "aprovado": "concluido",
            "ok": "concluido",
            "concluido": "concluido",
            "reprovado": "pendente",
            "nok": "pendente",
            "pendente": "pendente",
            "em_analise": "processamento",
            "processamento": "processamento",
        }
        status_valor = status_map.get(status, "pendente")

        logger.info("[Selenium] Inserindo lote: %s", numero)
        self.wait.until(EC.visibility_of_element_located(self.input_numero_lote))
        campo = self.driver.find_element(*self.input_numero_lote)
        campo.clear()
        campo.send_keys(numero)

        select = Select(self.driver.find_element(*self.select_produto))
        if produto_id.isdigit():
            select.select_by_value(produto_id)
        else:
            select.select_by_value("1" if "a" in produto_id.lower() else "2")

        logger.info("[Selenium] Definindo status: %s", status_valor)
        radio = self.driver.find_element(
            By.CSS_SELECTOR, f"input[name='status'][value='{status_valor}']"
        )
        if not radio.is_selected():
            radio.click()

        logger.info("[Selenium] Enviando formulário...")
        self.driver.find_element(*self.button_enviar).click()

    def tirar_screenshot(self, caminho: Path) -> Path:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.driver.save_screenshot(str(caminho))
        logger.info("[Selenium] Screenshot salvo: %s", caminho)
        return caminho

    def is_sucesso(
        self,
        numero_lote: str = "desconhecido",
        pasta_snapshots: Path | None = None,
        screenshot_enabled: bool = True,
    ) -> tuple[bool, Path | None]:
        logger.info("[Selenium] Aguardando confirmação...")
        pasta = pasta_snapshots or Path("logs/screenshots")
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            self.wait.until(EC.visibility_of_element_located(self.msg_sucesso))
            caminho: Path | None = None
            if screenshot_enabled:
                caminho = self.tirar_screenshot(
                    pasta / f"sucesso_selenium_{numero_lote}.png"
                )
            return True, caminho
        except Exception as exc:
            caminho = None
            if screenshot_enabled:
                caminho = self.tirar_screenshot(
                    pasta / f"erro_selenium_{numero_lote}.png"
                )
            logger.warning("[Selenium] Confirmação não apareceu: %s", exc)
            return False, caminho
