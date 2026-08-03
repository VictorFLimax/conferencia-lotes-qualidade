"""Performer: processa itens da fila com as regras de negócio."""
from __future__ import annotations

import logging
from typing import Any

from botcity.maestro import DataPoolEntry, ErrorType

from src.base_referencia import BaseReferencia
from src.config import Config
from src.validacao import CamposObrigatoriosVaziosError, ConferenciaLotes, registro_de_linha

logger = logging.getLogger(__name__)


def _fields_entry(entry: DataPoolEntry) -> dict[str, Any]:
    values = getattr(entry, "values", None) or {}
    return dict(values)


def process_item(entry: DataPoolEntry, config: Config) -> dict:
    """
    Valida um item do DataPool.

    Retorna dict com: aprovado (bool), fields (dict), mensagem (str).
    """
    fields = _fields_entry(entry)
    numero_lote = (
        fields.get("numero_lote")
        or fields.get("lote_id")
        or entry.get_value("numero_lote")
        or entry.get_value("lote_id")
        or "DESCONHECIDO"
    )
    logger.info("Iniciando validação do lote: %s", numero_lote)

    try:
        registro = registro_de_linha(fields)
        base = BaseReferencia(config)
        conferencia = ConferenciaLotes(base)
        resultado = conferencia.validar_registro(registro)

        if resultado.aprovado:
            logger.info("Lote %s aprovado.", numero_lote)
            entry.report_done(finish_message="APROVADO")
            return {
                "aprovado": True,
                "numero_lote": numero_lote,
                "fields": fields,
                "mensagem": "APROVADO",
            }

        msgs = [f"[{d.regra}] {d.mensagem}" for d in resultado.divergencias]
        erro_msg = " | ".join(msgs)
        logger.warning("Lote %s reprovado: %s", numero_lote, erro_msg)
        entry.report_error(error_type=ErrorType.BUSINESS, finish_message=erro_msg)
        return {
            "aprovado": False,
            "numero_lote": numero_lote,
            "fields": fields,
            "mensagem": erro_msg,
        }

    except CamposObrigatoriosVaziosError as exc:
        logger.warning("ValidationError no lote %s: %s", numero_lote, exc)
        entry.report_error(error_type=ErrorType.BUSINESS, finish_message=str(exc))
        return {
            "aprovado": False,
            "numero_lote": numero_lote,
            "fields": fields,
            "mensagem": str(exc),
        }

    except Exception as exc:
        logger.error("AppError no lote %s: %s", numero_lote, exc, exc_info=True)
        entry.report_error(error_type=ErrorType.SYSTEM, finish_message=f"Falha: {exc}")
        return {
            "aprovado": False,
            "numero_lote": numero_lote,
            "fields": fields,
            "mensagem": str(exc),
        }
