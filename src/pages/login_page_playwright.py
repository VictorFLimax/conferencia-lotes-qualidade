import logging
from playwright.async_api import Page

logger = logging.getLogger(__name__)

class LoginPagePlaywright:
    
    def __init__(self, page: Page):
        self.page = page

    async def fazer_login(self, usuario: str, senha: str):
        logger.info("[Playwright] Preenchendo credenciais de login...")
        
        # Mapeamento e ação usando localizadores do Playwright
        await self.page.locator("#user-name").fill(usuario)
        await self.page.locator("#password").fill(senha)
        
        logger.info("[Playwright] Clicando no botão de login...")
        await self.page.locator("#login-button").click()
        
        # Aguarda o redirecionamento após o login
        await self.page.wait_for_load_state("networkidle")
