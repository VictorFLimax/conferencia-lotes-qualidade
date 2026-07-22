import logging
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

            # Preenchimento dos campos usando os dados recebidos do orquestrador
            logger.info(f"[Automação] Inserindo Lote: {dados_lote['numero_lote']}")
            await page.fill("#lote", dados_lote["numero_lote"])

            logger.info(f"[Automação] Selecionando Produto ID: {dados_lote['produto_id']}")
            await page.select_option("#produto", str(dados_lote["produto_id"]))

            logger.info(f"[Automação] Definindo Status: {dados_lote['status']}")
            await page.check(f'input[name="status"][value="{dados_lote["status"]}"]')

            logger.info("[Automação] Enviando formulário...")
            await page.click('button[type="submit"]')

            # Espera ativa pela confirmação
            logger.info("[Automação] Aguardando confirmação do sistema...")
            
            # Adicionado um timeout de 5 segundos. Se não aparecer, lança exceção.
            await page.wait_for_selector("#mensagemSucesso.show", state="visible", timeout=5000)
            
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