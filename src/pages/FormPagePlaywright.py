import logging
import re

logger = logging.getLogger(__name__)

class FormPagePlaywright:
    def __init__(self, page):
        self.page = page
        # Locator do elemento de mensagem de sucesso
        self.msg_sucesso = page.locator("#mensagemSucesso")

    def preencher_formulario(self, dados_lote: dict):
        logger.info(f"[Playwright-POM] Inserindo Lote: {dados_lote['numero_lote']}")
        self.page.get_by_label(re.compile(r"Lote", re.IGNORECASE)).fill(dados_lote["numero_lote"])

        logger.info(f"[Playwright-POM] Selecionando Produto ID: {dados_lote.get('produto_id') or dados_lote.get('produto')}")
        self.page.get_by_label(re.compile(r"Produto", re.IGNORECASE)).select_option(
            str(dados_lote.get("produto_id") or dados_lote.get("produto"))
        )

        status_valor = dados_lote.get("status", "pendente").lower()
        logger.info(f"[Playwright-POM] Definindo Status: {status_valor}")
        self.page.locator(f"input[name='status'][value='{status_valor}']").check()

        logger.info("[Playwright-POM] Enviando formulário...")
        self.page.locator("button[type='submit']").click()

    def is_sucesso(self, numero_lote: str = "desconhecido") -> bool:
        logger.info("[Playwright-POM] Aguardando confirmação do sistema...")
        try:
            # Espera até que o elemento #mensagemSucesso fique visível no DOM
            self.msg_sucesso.wait_for(state="visible", timeout=5000)
            
            # Valida se a classe 'show' foi aplicada ao elemento
            classes = self.msg_sucesso.get_attribute("class") or ""
            if "show" in classes:
                snapshot_path = f"sucesso_playwright_{numero_lote}.png"
                self.page.screenshot(path=snapshot_path)
                logger.info(f"[Playwright-POM] Sucesso salvo: '{snapshot_path}'.")
                return True
            
            logger.warning("[Playwright-POM] Elemento de mensagem visível, mas sem classe 'show'.")
            return False

        except Exception as e:
            logger.error(f"[Playwright-POM] Falha na validação: {e}")
            self.page.screenshot(path=f"erro_playwright_{numero_lote}.png")
            return False