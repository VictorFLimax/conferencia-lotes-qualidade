# main.py - Ponto de entrada do BotCity
import os
import sys
import json
import logging
from dataclasses import dataclass
from typing import Any
from datetime import datetime
from botcity.maestro import BotMaestroSDK, AlertType
from src.config import Config
from src.dispatcher import run_dispatcher
from src.bot import process_item

@dataclass
class ExecutionResult:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    status: str
    message: str
    detail: Any

# Garante que a pasta logs exista
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(Config.LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    maestro = BotMaestroSDK()
    if Config.MAESTRO_ENABLED:
        maestro.login(server=Config.MAESTRO_SERVER_URL, login="", key=Config.MAESTRO_API_KEY)
        maestro.log(message="Iniciando auditoria de acessos", task_id=maestro.task_id)
        logger.info("Conectado ao BotCity Maestro.")

    if not os.path.exists(Config.INPUT_FOLDER):
        logger.error(f"FAIL FAST: A pasta '{Config.INPUT_FOLDER}' não foi encontrada.")
        if Config.MAESTRO_ENABLED:
            maestro.alert(
                task_id=maestro.task_id,
                title="Falha Crítica: Pasta de Entrada",
                message=f"A pasta '{Config.INPUT_FOLDER}' não existe. O bot foi encerrado imediatamente.",
                alert_type=AlertType.ERROR
            )
        sys.exit(1)

    summary = {
        "inicio": datetime.now().isoformat(),
        "total_processados": 0,
        "sucessos": 0,
        "erros": 0,
        "fim": None,
        "erro_critico": None
    }

    try:
        csv_path = os.path.join(Config.INPUT_FOLDER, "usuarios_auditoria.csv")
        if os.path.exists(csv_path):
            run_dispatcher(maestro, csv_path)

        logger.info(f"Iniciando consumo da fila: {Config.DATA_POOL_NAME}")
        while True:
            item = maestro.get_datapool_item(pool_name=Config.DATA_POOL_NAME)
            if not item:
                logger.info("Fila vazia. Encerrando loop de processamento.")
                break

            summary["total_processados"] += 1
            success = process_item(maestro, item)
            if success:
                summary["sucessos"] += 1
            else:
                summary["erros"] += 1

    except Exception as e:
        logger.error(f"Erro crítico na execução do bot: {e}")
        summary["erro_critico"] = str(e)
    finally:
        summary["fim"] = datetime.now().isoformat()
        
        report_path = "relatorio_execucao.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Relatório de execução gerado: {report_path}")
        
        if Config.MAESTRO_ENABLED:
            maestro.post_artifact(
                task_id=maestro.task_id,
                artifact_name="Relatorio_Auditoria.json",
                file_path=report_path
            )
            logger.info("Artefato enviado ao Maestro.")
            
            final_status = ExecutionResult.FAILED if summary["erro_critico"] else ExecutionResult.SUCCESS
            result = ExecutionResult(
                status=final_status,
                message=f"Auditoria concluída. Sucessos: {summary['sucessos']}, Erros: {summary['erros']}",
                detail=summary
            )
            
            maestro.finish_task(
                task_id=maestro.task_id,
                status=result.status,
                message=result.message,
                detail=result.detail
            )

if __name__ == '__main__':
    main()
