"""Page Object — Formulário de lote (Playwright sync)."""
from __future__ import annotations

import logging
from pathlib import Path

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class FormPagePlaywright:
    def __init__(self, page: Page):
        self.page = page

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

        logger.info("[Playwright] Inserindo lote: %s", numero)
        self.page.locator("#lote").fill(numero)

        if produto_id.isdigit():
            self.page.locator("#produto").select_option(produto_id)
        else:
            opcao = "1" if "a" in produto_id.lower() else "2"
            self.page.locator("#produto").select_option(opcao)

        logger.info("[Playwright] Definindo status: %s", status_valor)
        self.page.locator(f"input[name='status'][value='{status_valor}']").check()

        logger.info("[Playwright] Enviando formulário...")
        self.page.locator("button.btn-submit").click()

    def tirar_screenshot(self, caminho: Path) -> Path:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.page.screenshot(path=str(caminho), full_page=True)
        logger.info("[Playwright] Screenshot salvo: %s", caminho)
        return caminho

    def is_sucesso(
        self,
        numero_lote: str,
        pasta_snapshots: Path | None = None,
        screenshot_enabled: bool = True,
    ) -> tuple[bool, Path | None]:
        logger.info("[Playwright] Aguardando confirmação...")
        pasta = pasta_snapshots or Path("logs/screenshots")
        pasta.mkdir(parents=True, exist_ok=True)
        try:
            self.page.locator("#mensagemSucesso.show").wait_for(
                state="visible", timeout=5_000
            )
            caminho: Path | None = None
            if screenshot_enabled:
                caminho = self.tirar_screenshot(
                    pasta / f"sucesso_playwright_{numero_lote}.png"
                )
            return True, caminho
        except Exception as exc:
            caminho = None
            if screenshot_enabled:
                caminho = self.tirar_screenshot(
                    pasta / f"erro_playwright_{numero_lote}.png"
                )
            logger.error("[Playwright] Falha na confirmação: %s", exc)
            return False, caminho
