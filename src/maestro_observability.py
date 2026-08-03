"""Observabilidade no BotCity Maestro: Execution Log + Alerts + Result Files.

Documentação oficial:
- Logs:      https://documentation.botcity.dev/maestro/maestro-sdk/log/
- Alerts:    https://documentation.botcity.dev/maestro/maestro-sdk/alerts-and-messages/
- Artifacts: https://documentation.botcity.dev/maestro/maestro-sdk/result-files/
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from botcity.maestro import AlertType, BotMaestroSDK, Column

logger = logging.getLogger(__name__)

# Label padrão do Execution Log no Orchestrator
LOG_LABEL_PADRAO = "ConferenciaLotes_Execucao"

COLUNAS_LOG = [
    Column(name="Etapa", label="etapa", width=160),
    Column(name="Status", label="status", width=100),
    Column(name="Lote", label="lote", width=140),
    Column(name="Mensagem", label="mensagem", width=400),
    Column(name="Driver", label="driver", width=100),
    Column(name="Horario", label="horario", width=160),
]


def garantir_execution_log(
    maestro: BotMaestroSDK,
    activity_label: str = LOG_LABEL_PADRAO,
) -> str:
    """
    Garante que o Execution Log exista no Orchestrator.

    Se já existir, ignora o erro de criação e continua usando o mesmo label.
    """
    try:
        maestro.new_log(activity_label=activity_label, columns=COLUNAS_LOG)
        logger.info("Execution Log criado: %s", activity_label)
    except Exception as exc:
        # Log já existente ou sem permissão — segue com o label
        logger.info(
            "Execution Log '%s' já existe ou não pôde ser criado (%s). Usando o label.",
            activity_label,
            exc,
        )
    return activity_label


def registrar_etapa(
    maestro: BotMaestroSDK | None,
    activity_label: str,
    etapa: str,
    status: str,
    mensagem: str = "",
    lote: str = "-",
    driver: str = "-",
) -> None:
    """
    Grava uma linha no Execution Log para acompanhar o processo em tempo real.

    maestro.new_log_entry(activity_label=..., values={...})
    """
    horario = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    values: dict[str, Any] = {
        "etapa": etapa[:80],
        "status": status[:40],
        "lote": (lote or "-")[:80],
        "mensagem": (mensagem or "")[:500],
        "driver": (driver or "-")[:40],
        "horario": horario,
    }

    logger.info("[%s] %s | %s | %s", etapa, status, lote, mensagem)

    if maestro is None:
        return

    try:
        maestro.new_log_entry(activity_label=activity_label, values=values)
    except Exception as exc:
        logger.warning("Falha ao gravar Execution Log (%s): %s", etapa, exc)


def emitir_alerta(
    maestro: BotMaestroSDK | None,
    titulo: str,
    mensagem: str,
    tipo: str = "INFO",
) -> None:
    """
    Emite alerta no Orchestrator (visível no menu Alerts).

    maestro.alert(task_id=..., title=..., message=..., alert_type=AlertType.INFO|WARN|ERROR)
    """
    if maestro is None:
        return

    task_id = getattr(maestro, "task_id", None)
    if not task_id:
        logger.info("Alerta local (sem task_id): %s — %s", titulo, mensagem)
        return

    mapa = {
        "INFO": AlertType.INFO,
        "WARN": AlertType.WARN,
        "WARNING": AlertType.WARN,
        "ERROR": AlertType.ERROR,
    }
    alert_type = mapa.get(tipo.upper(), AlertType.INFO)

    try:
        maestro.alert(
            task_id=task_id,
            title=titulo[:120],
            message=mensagem[:500],
            alert_type=alert_type,
        )
        logger.info("Alerta Maestro enviado: [%s] %s", tipo, titulo)
    except Exception as exc:
        logger.warning("Falha ao emitir alerta '%s': %s", titulo, exc)
