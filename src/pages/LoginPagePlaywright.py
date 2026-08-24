"""Page Object — Login (Playwright sync)."""
from __future__ import annotations

import logging

from playwright.sync_api import Page

logger = logging.getLogger(__name__)


class LoginPagePlaywright:
    def __init__(self, page: Page):
        self.page = page
        self.usuario_input = page.locator("#usuario")
        self.senha_input = page.locator("#senha")
        self.login_button = page.locator("button.btn-submit")

    def fazer_login(self, usuario: str, senha: str) -> None:
        logger.info("[Playwright] Preenchendo credenciais de login...")
        url_inicial = self.page.url
        self.usuario_input.fill(usuario)
        self.senha_input.fill(senha)
        self.login_button.click()
        # login.html redireciona para lote-teste.html após ~1.2s
        self.page.wait_for_url(lambda url: url != url_inicial, timeout=10_000)
        logger.info("[Playwright] Login concluído.")
