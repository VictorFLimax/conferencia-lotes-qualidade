"""Encaminhamento de lotes ambíguos via ML — sem predição no bot.

O motor de regras (validar_registro) continua dono da classificação
Válido/Divergência/Ambíguo/Erro. Aqui só os Ambíguos passam pelo MLClient.

Se a API cair no meio do lote de 10 dias, cada registro afetado recebe
REVISAO_ML_OFFLINE e o processamento segue até o fim.
"""
from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ml_client import MLClient, PredictionResult
from src.validacao_aula22 import CLASSIFICACAO_AMBIGUO, RegistroValidado

REVISAO_ML_OFFLINE = "REVISAO_ML_OFFLINE"
NIVEL_ALTA = "alta"
NIVEL_MEDIA = "média"
NIVEL_BAIXA = "baixa"
ACAO_REVISAR = "revisar"
ACAO_REVISAR_PRIORITARIO = "revisar_prioritario"

logger = logging.getLogger("auditoria_ml")


@dataclass
class DecisaoML:
    lote_id: str
    classe: str
    probabilidade: float | None
    nivel_confianca: str
    latencia_ms: float | None
    acao: str
    offline: bool
    status_raw: str = ""
    turno: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_excel_row(self) -> dict[str, Any]:
        return {
            "Lote": self.lote_id,
            "Classe prevista": self.classe,
            "Probabilidade": self.probabilidade,
            "Nível de confiança": self.nivel_confianca,
            "Latência (ms)": self.latencia_ms,
            "Ação aplicada": self.acao,
            "API indisponível": "sim" if self.offline else "não",
            "Status original": self.status_raw,
            "Turno": self.turno,
        }


def _tem_obs(registro: RegistroValidado) -> bool:
    return bool(str(registro.observacao or "").strip())


def _lote_para_api(registro: RegistroValidado) -> dict[str, Any]:
    return {
        "lote_id": registro.lote_id,
        "status_raw": registro.status_original or registro.status_normalizado,
        "turno": registro.turno,
        "tem_obs": _tem_obs(registro),
    }


def encaminhar(pred: PredictionResult | None, registro: RegistroValidado) -> DecisaoML:
    """Traduz o retorno do MLClient em ação operacional. Sem predição aqui."""
    if pred is None:
        return DecisaoML(
            lote_id=registro.lote_id,
            classe=REVISAO_ML_OFFLINE,
            probabilidade=None,
            nivel_confianca="indisponível",
            latencia_ms=None,
            acao=REVISAO_ML_OFFLINE,
            offline=True,
            status_raw=registro.status_original,
            turno=registro.turno,
        )

    nivel = (pred.nivel_confianca or "").strip().lower()
    if nivel == NIVEL_ALTA:
        acao = pred.acao or pred.classe
    elif nivel == NIVEL_MEDIA:
        acao = ACAO_REVISAR
    elif nivel == NIVEL_BAIXA:
        acao = ACAO_REVISAR_PRIORITARIO
    else:
        acao = ACAO_REVISAR

    return DecisaoML(
        lote_id=registro.lote_id or pred.lote_id,
        classe=pred.classe,
        probabilidade=pred.probabilidade,
        nivel_confianca=pred.nivel_confianca,
        latencia_ms=pred.latencia_ms,
        acao=acao,
        offline=False,
        status_raw=registro.status_original,
        turno=registro.turno,
    )


def registrar_decisao(decisao: DecisaoML, caminho_jsonl: Path | None = None) -> None:
    """Log estruturado (JSON por linha) para reconstruir a decisão sem abrir o código."""
    payload = {
        "evento": "decisao_ml",
        "lote_id": decisao.lote_id,
        "classe": decisao.classe,
        "probabilidade": decisao.probabilidade,
        "nivel_confianca": decisao.nivel_confianca,
        "latencia_ms": decisao.latencia_ms,
        "acao": decisao.acao,
        "offline": decisao.offline,
        "status_raw": decisao.status_raw,
        "turno": decisao.turno,
    }
    linha = json.dumps(payload, ensure_ascii=False)
    logger.info(linha)
    if caminho_jsonl is not None:
        caminho_jsonl.parent.mkdir(parents=True, exist_ok=True)
        with caminho_jsonl.open("a", encoding="utf-8") as fh:
            fh.write(linha + "\n")


def processar_ambiguos_com_ml(
    registros: list[RegistroValidado],
    cliente: MLClient | None = None,
    caminho_jsonl: Path | None = None,
) -> list[DecisaoML]:
    """Percorre só os ambíguos. Nunca interrompe o lote — falha vira REVISAO_ML_OFFLINE."""
    proprio = cliente is None
    ml = cliente or MLClient()
    decisoes: list[DecisaoML] = []
    try:
        for registro in registros:
            if registro.classificacao != CLASSIFICACAO_AMBIGUO:
                continue
            try:
                pred = ml.classificar(_lote_para_api(registro))
            except Exception:
                pred = None
            decisao = encaminhar(pred, registro)
            registrar_decisao(decisao, caminho_jsonl=caminho_jsonl)
            decisoes.append(decisao)
    finally:
        if proprio:
            ml.fechar()
    return decisoes
