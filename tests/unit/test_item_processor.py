"""Testes do encaminhamento de ambíguos (fallback que nunca para o bot)."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.item_processor import (
    REVISAO_ML_OFFLINE,
    DecisaoML,
    encaminhar,
    processar_ambiguos_com_ml,
)
from src.ml_client import PredictionResult
from src.validacao_aula22 import (
    CLASSIFICACAO_AMBIGUO,
    CLASSIFICACAO_VALIDO,
    RegistroValidado,
)


def _registro(lote: str, classificacao: str = CLASSIFICACAO_AMBIGUO) -> RegistroValidado:
    return RegistroValidado(
        lote_id=lote,
        produto="TV55-4K-B",
        linha="L1",
        turno="A",
        status_original="EM AJUSTE",
        status_normalizado="EM AJUSTE",
        responsavel="Ana",
        data="15/06/2026",
        observacao="checar",
        data_referencia="15/06/2026",
        classificacao=classificacao,
        regra="RN09",
        mensagem="teste",
        regra_aplicada="RN09",
    )


@pytest.mark.unit
def test_processar_ambiguos_fallback_offline_quando_pred_none(tmp_path) -> None:
    cliente = MagicMock()
    cliente.classificar.return_value = None
    registros = [
        _registro("L1"),
        _registro("L2", CLASSIFICACAO_VALIDO),
        _registro("L3"),
    ]
    jsonl = tmp_path / "decisoes_ml.jsonl"

    decisoes = processar_ambiguos_com_ml(registros, cliente=cliente, caminho_jsonl=jsonl)

    assert len(decisoes) == 2
    assert all(d.acao == REVISAO_ML_OFFLINE for d in decisoes)
    assert all(d.offline for d in decisoes)
    assert cliente.classificar.call_count == 2
    texto = jsonl.read_text(encoding="utf-8")
    assert "REVISAO_ML_OFFLINE" in texto
    assert texto.count("\n") == 2


@pytest.mark.unit
def test_encaminhar_alta_aplica_classe_prevista() -> None:
    pred = PredictionResult(
        lote_id="L1",
        classe="valido_automatico",
        probabilidade=0.92,
        nivel_confianca="alta",
        latencia_ms=8.0,
        acao="valido_automatico",
    )
    decisao = encaminhar(pred, _registro("L1"))
    assert decisao.acao == "valido_automatico"
    assert decisao.offline is False
    assert isinstance(decisao, DecisaoML)


@pytest.mark.unit
def test_encaminhar_media_e_baixa_vao_para_revisao() -> None:
    media = PredictionResult(
        lote_id="L2",
        classe="valido_automatico",
        probabilidade=0.70,
        nivel_confianca="média",
        latencia_ms=9.0,
    )
    baixa = PredictionResult(
        lote_id="L3",
        classe="recusar_automatico",
        probabilidade=0.40,
        nivel_confianca="baixa",
        latencia_ms=11.0,
    )
    assert encaminhar(media, _registro("L2")).acao == "revisar"
    assert encaminhar(baixa, _registro("L3")).acao == "revisar_prioritario"


@pytest.mark.unit
def test_encaminhar_nivel_desconhecido_e_excecao_do_cliente() -> None:
    pred = PredictionResult(
        lote_id="L4",
        classe="revisar",
        probabilidade=0.50,
        nivel_confianca="desconhecido",
        latencia_ms=1.0,
    )
    decisao = encaminhar(pred, _registro("L4"))
    assert decisao.acao == "revisar"
    assert "L4" in decisao.to_dict()["lote_id"]

    cliente = MagicMock()
    cliente.classificar.side_effect = RuntimeError("falha inesperada")
    saida = processar_ambiguos_com_ml([_registro("L5")], cliente=cliente)
    assert len(saida) == 1
    assert saida[0].acao == REVISAO_ML_OFFLINE
    assert saida[0].offline is True


@pytest.mark.unit
def test_processar_ambiguos_fecha_cliente_proprio() -> None:
    with patch("src.item_processor.MLClient") as mock_cls:
        inst = MagicMock()
        inst.classificar.return_value = None
        mock_cls.return_value = inst
        processar_ambiguos_com_ml([_registro("L9")])
        inst.fechar.assert_called_once()

