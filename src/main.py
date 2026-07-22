"""Ponto de entrada do bot de conferência de lotes com BotCity Maestro."""
from __future__ import annotations
import os
import sys
import json
import logging
from dataclasses import dataclass
from typing import Any
from datetime import datetime
from pathlib import Path

from botcity.maestro import BotMaestroSDK, AlertType, ActivityStatus

from .config import Config
from .dispatcher import run_dispatcher
from .bot import process_item
from .relatorio import gerar_relatorio_divergencias
from .validacao import ResultadoValidacao, RegistroLote, Divergencia

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.FileHandler("logs/execucao.log", encoding='utf-8'), logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

@dataclass
class ExecutionResult:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    status: str
    message: str
    detail: Any

def main() -> int:
    config = Config.carregar()
    
    maestro = BotMaestroSDK()
    if config.maestro_enabled:
        maestro.login(server=config.maestro_server_url, login="", key=config.maestro_api_key)
        maestro.log(message="Iniciando conferência de lotes v1.0", task_id=maestro.task_id)
        logger.info("Conectado ao BotCity Maestro.")

    if not config.caminho_planilha_entrada.exists():
        erro = f"Planilha de entrada não encontrada: {config.caminho_planilha_entrada}"
        logger.error(erro)
        if config.maestro_enabled:
            maestro.alert(task_id=maestro.task_id, title="Falha Crítica", message=erro, alert_type=AlertType.ERROR)
        return 1

    summary = {"inicio": datetime.now().isoformat(), "total_processados": 0, "sucessos": 0, "erros": 0, "fim": None, "erro_critico": None}
    resultados_validacao: list[ResultadoValidacao] = [] # Para o relatório final

    try:
        logger.info("Executando Dispatcher...")
        run_dispatcher(maestro, config)

        logger.info(f"Iniciando consumo da fila: {config.data_pool_name}")
        while True:
            item = maestro.get_datapool_item(pool_name=config.data_pool_name)
            if not item:
                logger.info("Fila vazia. Encerrando loop.")
                break

            summary["total_processados"] += 1
            
            # Recriamos o objeto ResultadoValidacao localmente para o relatório final
            from src.base_referencia import BaseReferencia
            from src.validacao import ConferenciaLotes, registro_de_linha
            base = BaseReferencia(config)
            conferencia = ConferenciaLotes(base)
            resultado = conferencia.validar_registro(registro_de_linha(item.fields))
            resultados_validacao.append(resultado)

            sucesso = process_item(maestro, item, config)
            if sucesso:
                summary["sucessos"] += 1
            else:
                summary["erros"] += 1

        if summary["erros"] > 0:
            logger.info("Gerando relatório de divergências em Excel...")
            caminho_saida = config.caminho_saida_relatorio
            gerar_relatorio_divergencias(resultados_validacao, caminho_saida)
            logger.info(f"Relatório de divergências gerado: {caminho_saida}")

    except Exception as e:
        logger.error(f"Erro crítico na execução do bot: {e}", exc_info=True)
        summary["erro_critico"] = str(e)
    finally:
        summary["fim"] = datetime.now().isoformat()
        
        report_path = "logs/relatorio_execucao.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4, ensure_ascii=False)
        
        if config.maestro_enabled:
            maestro.post_artifact(task_id=maestro.task_id, artifact_name="Relatorio_Execucao.json", file_path=report_path)
            
            final_status = ExecutionResult.FAILED if summary["erro_critico"] else ExecutionResult.SUCCESS
            result = ExecutionResult(status=final_status, message=f"Conferência concluída. Sucessos: {summary['sucessos']}, Erros: {summary['erros']}", detail=summary)
            maestro.finish_task(task_id=maestro.task_id, status=result.status, message=result.message, detail=result.detail)

    return 0 if summary["erro_critico"] is None else 1

if __name__ == "__main__":
    sys.exit(main())
