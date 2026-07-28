import logging
import re

logger = logging.getLogger(__name__)

class FormPagePlaywright:
    def __init__(self, page):
        # A página (browser tab) é injetada pelo orquestrador
        self.page = page

    async def preencher_formulario(self, dados_lote: dict):
        logger.info(f"[Playwright-POM] Inserindo Lote: {dados_lote['numero_lote']}")
        await self.page.get_by_label(re.compile("Número do Lote")).fill(dados_lote["numero_lote"])

        logger.info(f"[Playwright-POM] Selecionando Produto ID: {dados_lote['produto_id']}")
        await self.page.get_by_label(re.compile("Produto")).select_option(str(dados_lote["produto_id"]))

        status_map = {
            "pendente": "Pendente",
            "processamento": "Em Processamento",
            "concluido": "Concluído",
            "ativo": "Ativo"
        }
        status_label = status_map.get(dados_lote["status"].lower(), "Pendente")
        logger.info(f"[Playwright-POM] Definindo Status: {status_label}")
        await self.page.get_by_label(status_label, exact=True).check()

        logger.info("[Playwright-POM] Enviando formulário...")
        await self.page.get_by_role("button", name="Processar Lote").click()

    async def is_sucesso(self, numero_lote: str) -> bool:
        logger.info("[Playwright-POM] Aguardando confirmação do sistema...")
        try:
            mensagem_sucesso = self.page.get_by_text("Lote processado com sucesso.")
            await mensagem_sucesso.wait_for(state="visible", timeout=5000)
            
            snapshot_path = f"sucesso_playwright_{numero_lote}.png"
            await self.page.screenshot(path=snapshot_path)
            logger.info(f"[Playwright-POM] Sucesso salvo: '{snapshot_path}'.")
            return True
        except Exception as e:
            logger.error(f"[Playwright-POM] Falha na validação: {e}")
            await self.page.screenshot(path=f"erro_playwright_{numero_lote}.png")
            return False
