"""Orquestrador Multi-Bot para o Pipeline de Conferência de Lotes (S10-B).

Implementa a dependência sequencial entre 3+ bots usando create_task().
Nomenclatura obrigatória: nome_aluno-nome_bot-versao
"""
from __future__ import annotations

import logging
import os
from typing import Any

from botcity.maestro import BotMaestroSDK

logger = logging.getLogger(__name__)

BOT_DISPATCHER = "andre-dispatcher-v1"
BOT_CONFERENCIA = "gustavo-conferencia-v1"
BOT_RELATORIO = "victor-relatorio-v1"

class Orchestrator:
    def __init__(self, maestro: BotMaestroSDK):
        self.maestro = maestro

    def executar_pipeline(self, parametros_iniciais: dict[str, Any] | None = None) -> str | None:
        """Dispara a cadeia de bots sequencialmente com rastreamento de dependências."""
        parametros = parametros_iniciais or {}
        cadeia_execucao = []

        # 1. Disparar Bot Dispatcher
        logger.info("Disparando Bot: %s", BOT_DISPATCHER)
        task_dispatcher = self._disparar_bot(BOT_DISPATCHER, parametros)
        if not task_dispatcher:
            logger.error("Falha crítica ao disparar %s", BOT_DISPATCHER)
            return None
        cadeia_execucao.append({"bot": BOT_DISPATCHER, "task_id": getattr(task_dispatcher, 'id', 'desconhecido')})

        # 2. Disparar Bot Conferencia (depende do Dispatcher)
        parametros_conferencia = {
            **parametros,
            "predecessor_task_id": getattr(task_dispatcher, 'id', ''),
            "predecessor_bot": BOT_DISPATCHER,
            "cadeia_execucao": cadeia_execucao
        }
        logger.info("Disparando Bot: %s (dependente de %s)", BOT_CONFERENCIA, BOT_DISPATCHER)
        task_conferencia = self._disparar_bot(BOT_CONFERENCIA, parametros_conferencia)
        if not task_conferencia:
            logger.error("Falha crítica ao disparar %s", BOT_CONFERENCIA)
            return None
        cadeia_execucao.append({"bot": BOT_CONFERENCIA, "task_id": getattr(task_conferencia, 'id', 'desconhecido')})

        # 3. Disparar Bot Relatorio (depende do Conferencia)
        parametros_relatorio = {
            **parametros,
            "predecessor_task_id": getattr(task_conferencia, 'id', ''),
            "predecessor_bot": BOT_CONFERENCIA,
            "cadeia_execucao": cadeia_execucao
        }
        logger.info("Disparando Bot: %s (dependente de %s)", BOT_RELATORIO, BOT_CONFERENCIA)
        task_relatorio = self._disparar_bot(BOT_RELATORIO, parametros_relatorio)
        if not task_relatorio:
            logger.error("Falha crítica ao disparar %s", BOT_RELATORIO)
            return None
        cadeia_execucao.append({"bot": BOT_RELATORIO, "task_id": getattr(task_relatorio, 'id', 'desconhecido')})

        logger.info("Pipeline orquestrado com sucesso. Cadeia de execução: %s", cadeia_execucao)
        return getattr(task_relatorio, 'id', None)

    def _disparar_bot(self, bot_label: str, parametros: dict[str, Any]) -> Any | None:
        try:
            task = self.maestro.create_task(
                activity_label=bot_label,
                parameters=parametros,
                test=False
            )
            logger.info("Task criada com sucesso para %s. Task ID: %s", bot_label, getattr(task, 'id', 'N/A'))
            return task
        except Exception as e:
            logger.error("Erro ao criar task para %s: %s", bot_label, e)
            return None

def executar_orquestrador_cli() -> int:
    """Ponto de entrada para orquestração via CLI."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    
    maestro = BotMaestroSDK()
    maestro.RAISE_NOT_CONNECTED = False
    
    server = os.getenv("MAESTRO_SERVER_URL", "https://lgcmd.botcity.dev")
    login = os.getenv("MAESTRO_LOGIN", "")
    key = os.getenv("MAESTRO_API_KEY", "")
    
    if not key:
        logger.error("MAESTRO_API_KEY não definida no ambiente.")
        return 1
        
    maestro.login(server=server, login=login, key=key)
    
    orchestrator = Orchestrator(maestro)
    sucesso = orchestrator.executar_pipeline({"fonte": "orquestrador_cli", "s10b": True})
    
    return 0 if sucesso else 1

if __name__ == "__main__":
    raise SystemExit(executar_orquestrador_cli())
