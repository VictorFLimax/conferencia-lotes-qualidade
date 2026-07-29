import logging
import re
from playwright.async_api import async_playwright

# Configuração básica do logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

async def preencher_lote(dados_lote: dict, url: str = "http://localhost:8000/lote-teste.html"):
    """
    Automação para preencher o formulário de cadastro de lote.
    """
    logger.info("[Automação] Iniciando o Playwright...")
    
    async with async_playwright() as p:
        try:
            # O parâmetro slow_mo garante visualização limpa sem usar time.sleep
            browser = await p.chromium.launch(headless=False, slow_mo=400)
            page = await browser.new_page()

            logger.info(f"🌐 [Automação] Acessando: {url}")
            await page.goto(url)

            # =========================================================
            # REFATORAÇÃO: USO DE LOCATORS SEMÂNTICOS
            # =========================================================

            # Substituído '#lote' por get_by_label
            logger.info(f"[Automação] Inserindo Lote: {dados_lote['numero_lote']}")
            await page.get_by_label(re.compile("Número do Lote")).fill(dados_lote["numero_lote"])

            # Substituído '#produto' por get_by_label
            logger.info(f"[Automação] Selecionando Produto ID: {dados_lote['produto_id']}")
            await page.get_by_label(re.compile("Produto")).select_option(str(dados_lote["produto_id"]))

            # Mapeamento e substituição do seletor CSS do Radio Button por get_by_label
            logger.info(f"[Automação] Definindo Status: {dados_lote['status']}")
            status_map = {
                "pendente": "Pendente",
                "processamento": "Em Processamento",
                "concluido": "Concluído"
            }
            status_label = status_map.get(dados_lote["status"].lower(), "Pendente")
            await page.get_by_label(status_label, exact=True).check()

            # Substituído 'button[type="submit"]' por get_by_role
            logger.info("[Automação] Enviando formulário...")
            await page.get_by_role("button", name="Processar Lote").click()

            # Substituído espera por CSS '#mensagemSucesso.show' por get_by_text
            logger.info("[Automação] Aguardando confirmação do sistema...")
            mensagem_sucesso = page.get_by_text("Lote processado com sucesso.")
            await mensagem_sucesso.wait_for(state="visible", timeout=5000)
            
            # =========================================================

            logger.info("[Automação] Lote cadastrado e verificado com sucesso!")

            # Snapshot de Sucesso
            snapshot_path = f"sucesso_{dados_lote['numero_lote']}.png"
            await page.screenshot(path=snapshot_path)
            logger.info(f"[Automação] Snapshot de SUCESSO salvo como '{snapshot_path}'.")

        except Exception as e:
            logger.error(f"[Automação] Falha na execução da rotina: {e}")
            
            # Tenta tirar um snapshot do estado em que o erro ocorreu
            try:
                if 'page' in locals() and not page.is_closed():
                    erro_snapshot = f"erro_execucao_{dados_lote['numero_lote']}.png"
                    await page.screenshot(path=erro_snapshot)
                    logger.info(f"[Automação] Snapshot de ERRO salvo como '{erro_snapshot}'.")
            except Exception as snap_error:
                logger.error(f"[Automação] Não foi possível salvar o snapshot de erro: {snap_error}")
            
            # Repassa a exceção para que o main.py (orquestrador) saiba que a tarefa falhou
            raise e
            
        finally:
            if 'browser' in locals():
                logger.info("[Automação] Fechando o navegador.")
                await browser.close()
