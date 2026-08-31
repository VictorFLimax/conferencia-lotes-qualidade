"""Orquestrador Multi-Bot para o Pipeline de Conferência de Lotes (S10-B)."""
from __future__ import annotations
import logging
import os
from typing import Any
from botcity.maestro import BotMaestroSDK

logger = logging.getLogger(__name__)

# ATENÇÃO: Substitua 'victor' pelo seu nome real conforme exigido no enunciado
BOT_DISPATCHER = "andre-dispatcher-v1"
BOT_CONFERENCIA = "gustavo-conferencia-v1"
BOT_RELATORIO = "victor-relatorio-v1"

class OrquestradorMultiBot:
    def __init__(self, maestro: BotMaestroSDK):
        self.maestro = maestro

    def executar_pipeline(self, parametros_iniciais: dict[str, Any] | None = None) -> str | None:
        parametros = parametros_iniciais or {}
        cadeia_execucao = []

        # 1. Disparar Bot Dispatcher
        task_disp = self._disparar_bot(BOT_DISPATCHER, parametros)
        if not task_disp: return None
        cadeia_execucao.append({"bot": BOT_DISPATCHER, "task_id": getattr(task_disp, 'id', 'N/A')})

        # 2. Disparar Bot Conferencia (depende do Dispatcher)
        params_conf = {**parametros, "predecessor_task_id": getattr(task_disp, 'id', ''), "cadeia_execucao": list(cadeia_execucao)}
        task_conf = self._disparar_bot(BOT_CONFERENCIA, params_conf)
        if not task_conf: return None
        cadeia_execucao.append({"bot": BOT_CONFERENCIA, "task_id": getattr(task_conf, 'id', 'N/A')})

        # 3. Disparar Bot Relatorio (depende do Conferencia)
        params_rel = {**parametros, "predecessor_task_id": getattr(task_conf, 'id', ''), "cadeia_execucao": list(cadeia_execucao)}
        task_rel = self._disparar_bot(BOT_RELATORIO, params_rel)
        if not task_rel: return None
        cadeia_execucao.append({"bot": BOT_RELATORIO, "task_id": getattr(task_rel, 'id', 'N/A')})

        logger.info("Pipeline orquestrado com sucesso. Cadeia: %s", cadeia_execucao)
        return getattr(task_rel, 'id', None)

    def _disparar_bot(self, bot_label: str, parametros: dict[str, Any]) -> Any | None:
        try:
            task = self.maestro.create_task(activity_label=bot_label, parameters=parametros, test=False)
            logger.info("Task criada para %s. Task ID: %s", bot_label, getattr(task, 'id', 'N/A'))
            return task
        except Exception as e:
            logger.error("Erro ao criar task para %s: %s", bot_label, e)
            return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    maestro = BotMaestroSDK()
    maestro.RAISE_NOT_CONNECTED = False
    maestro.login(server=os.getenv("MAESTRO_SERVER_URL", "https://lgcmd.botcity.dev"), login=os.getenv("MAESTRO_LOGIN", ""), key=os.getenv("MAESTRO_API_KEY", ""))
    OrquestradorMultiBot(maestro).executar_pipeline({"fonte": "orquestrador_cli", "s10b": True})
