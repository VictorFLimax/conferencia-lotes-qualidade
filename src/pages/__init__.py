"""Page Objects de login e formulário (Playwright e Selenium)."""
from src.pages.LoginPagePlaywright import LoginPagePlaywright
from src.pages.LoginPageSelenium import LoginPageSelenium
from src.pages.FormPagePlaywright import FormPagePlaywright
from src.pages.FormPageSelenium import FormPageSelenium

__all__ = [
    "LoginPagePlaywright",
    "LoginPageSelenium",
    "FormPagePlaywright",
    "FormPageSelenium",
]
