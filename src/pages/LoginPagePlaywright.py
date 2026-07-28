from playwright.sync_api import Page


class LoginPage:

    def __init__(self, page: Page):
        self.page = page

        # Mapeamento dos elementos (utilizando locators)
        self.usuario_input = page.locator("#user-name")
        self.senha_input = page.locator("#password")
        self.login_button = page.locator("#login-button")

    def fazer_login(self, usuario: str, senha: str):
        # O Playwright já aguarda o elemento estar visível e interativo automaticamente
        url_inicial = self.page.url

        # Preenche o usuário (fill limpa o campo antes de digitar)
        self.usuario_input.fill(usuario)

        # Preenche a senha
        self.senha_input.fill(senha)

        # Clica no botão de login
        self.login_button.click()

        # Aguarda a URL mudar após o login
        self.page.wait_for_url(lambda url: url != url_inicial)