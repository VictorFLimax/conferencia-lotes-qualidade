import logging
import re
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class LoginPagePlaywright:
    """
    Page Object para login.html (Playwright, assíncrono).

    Usa locators semânticos (get_by_label / get_by_role / get_by_text),
    alinhados com os labels e textos reais do HTML de login.
    """

    def __init__(self, page: Page):
        self.page = page

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