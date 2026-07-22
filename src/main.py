import asyncio
import logging
import os
from web_automation import preencher_lote

# Configuração básica do logger para o orquestrador
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [ORQUESTRADOR] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

async def main():
    logger.info("=" * 50)
    logger.info("INICIANDO ORQUESTRADOR DE TAREFAS")
    logger.info("=" * 50)

    url_alvo = os.getenv("TARGET_URL", "http://localhost:8000/lote-teste.html")

    # Dados que o orquestrador poderia ler de um banco de dados, API, fila (RabbitMQ/SQS) ou CSV
    dados_para_processar = {
        "numero_lote": "LOTE-2026-8842",
        "produto_id": 2,          # Corresponde ao Produto B
        "status": "concluido"     # 'pendente', 'processamento' ou 'concluido'
    }

    try:
        logger.info(f"Iniciando processamento para o lote: {dados_para_processar['numero_lote']}")
        
        # Executa a tarefa de automação
        await preencher_lote(dados_lote=dados_para_processar, url=url_alvo)
        
        logger.info("Processo finalizado com sucesso pelo orquestrador.")

    except Exception as erro:
        # Captura a exceção propagada pelo web_automation.py
        logger.error(f"Falha crítica na execução da tarefa: {erro}")
        # Aqui você poderia adicionar lógicas de retentativa (retry) ou envio de alertas/emails

    finally:
        logger.info("=" * 50)
        logger.info("ORQUESTRADOR FINALIZADO")
        logger.info("=" * 50)

if __name__ == "__main__":
    # Inicia o loop de eventos assíncrono
    asyncio.run(main())