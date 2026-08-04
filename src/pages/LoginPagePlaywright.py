<<<<<<< HEAD
"""Page Object — Login (Playwright sync)."""
from __future__ import annotations

import logging

from playwright.sync_api import Page
=======
import logging
import re
from playwright.async_api import Page

logger = logging.getLogger(__name__)
>>>>>>> a841090a6c45662863391390bba21a2fbd4c8d91

logger = logging.getLogger(__name__)


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.usuario_input = page.locator("#usuario")
        self.senha_input = page.locator("#senha")
        self.login_button = page.locator("button.btn-submit")

<<<<<<< HEAD
    def fazer_login(self, usuario: str, senha: str) -> None:
        logger.info("[Playwright] Preenchendo credenciais de login...")
        url_inicial = self.page.url
        self.usuario_input.fill(usuario)
        self.senha_input.fill(senha)
        self.login_button.click()
        # login.html redireciona para lote-teste.html após ~1.2s
        self.page.wait_for_url(lambda url: url != url_inicial, timeout=10_000)
        logger.info("[Playwright] Login concluído.")
=======
    async def fazer_login(self, usuario: str, senha: str):
        logger.info("[LoginPage-Playwright] Preenchendo credenciais de login...")
        await self.page.get_by_label(re.compile("Usuário ou E-mail")).fill(usuario)
        await self.page.get_by_label(re.compile("Senha")).fill(senha)

        logger.info("[LoginPage-Playwright] Clicando em 'Entrar'...")
        await self.page.get_by_role("button", name="Entrar").click()

    async def is_login_sucesso(self) -> bool:
        try:
            mensagem = self.page.get_by_text("Login realizado com sucesso.")
            await mensagem.wait_for(state="visible", timeout=5000)
            return True
        except Exception as e:
            logger.warning(f"[LoginPage-Playwright] Sucesso não confirmado: {e}")
            return False

    async def is_login_erro(self) -> bool:
        try:
            mensagem = self.page.get_by_text("Usuário ou senha inválidos.")
            await mensagem.wait_for(state="visible", timeout=5000)
            return True
        except Exception as e:
            logger.warning(f"[LoginPage-Playwright] Erro não confirmado: {e}")
            return False
>>>>>>> a841090a6c45662863391390bba21a2fbd4c8d91
