"""Processamento de itens com decisão híbrida RPA + ML (S10-B)."""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

from src.config import Config
from src.base_referencia import BaseReferencia
from src.validacao import ConferenciaLotes, registro_de_linha, CamposObrigatoriosVaziosError
from src.classificador_divergencia import ClassificadorDivergencia, ResultadoClassificacao

logger = logging.getLogger(__name__)

@dataclass
class ResultadoProcessamento:
    numero_lote: str
    aprovado: bool
    mensagem: str
    causa_provavel: str = "nao_aplicavel"
    origem_decisao: str = "nao_aplicavel"
    confianca_ml: float = 0.0
    divergencias: list[dict] = None  # Para compatibilidade com o relatório

def processar_item(fields: dict[str, Any], config: Config) -> ResultadoProcessamento:
    numero_lote = str(fields.get("numero_lote") or fields.get("lote_id") or "DESCONHECIDO")
    logger.info("Iniciando processamento do lote: %s", numero_lote)

    try:
        # 1. Decisão de negócio APENAS pelas regras RN01-RN03
        registro = registro_de_linha(fields)
        base = BaseReferencia(config)
        conferencia = ConferenciaLotes(base)
        resultado_validacao = conferencia.validar_registro(registro)

        if resultado_validacao.aprovado:
            logger.info("Lote %s APROVADO pelas regras de negócio.", numero_lote)
            return ResultadoProcessamento(
                numero_lote=numero_lote, aprovado=True, mensagem="APROVADO",
                causa_provavel="nao_aplicavel", origem_decisao="regras", confianca_ml=1.0, divergencias=[]
            )

        # 2. Se houver divergência, aciona o ClassificadorDivergencia (ML)
        divergencias_dict = [{"regra": d.regra, "mensagem": d.mensagem, "valor_esperado": d.valor_esperado, "valor_encontrado": d.valor_encontrado} for d in resultado_validacao.divergencias]
        msgs = [f"[{d.regra}] {d.mensagem}" for d in resultado_validacao.divergencias]
        erro_msg = " | ".join(msgs)
        logger.warning("Lote %s com DIVERGÊNCIA: %s", numero_lote, erro_msg)

        classificador = ClassificadorDivergencia()
        try:
            observacao = str(fields.get("observacao", ""))
            classificacao: ResultadoClassificacao = classificador.classificar(
                observacao=observacao, regras_violadas=erro_msg
            )
        finally:
            classificador.close()

        return ResultadoProcessamento(
            numero_lote=numero_lote, aprovado=False, mensagem=erro_msg,
            causa_provavel=classificacao.causa_provavel,
            origem_decisao=classificacao.origem_decisao,
            confianca_ml=classificacao.confianca_ml,
            divergencias=divergencias_dict
        )

    except CamposObrigatoriosVaziosError as exc:
        logger.warning("ValidationError no lote %s: %s", numero_lote, exc)
        return ResultadoProcessamento(
            numero_lote=numero_lote, aprovado=False, mensagem=str(exc),
            causa_provavel="erro_validacao", origem_decisao="fallback", confianca_ml=0.0, divergencias=[]
        )
    except Exception as exc:
        logger.error("Erro inesperado no lote %s: %s", numero_lote, exc, exc_info=True)
        return ResultadoProcessamento(
            numero_lote=numero_lote, aprovado=False, mensagem=f"Falha sistêmica: {exc}",
            causa_provavel="erro_sistemico", origem_decisao="fallback", confianca_ml=0.0, divergencias=[]
        )
