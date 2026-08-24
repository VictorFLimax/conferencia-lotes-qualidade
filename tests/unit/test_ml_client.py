"""Testes do MLClient: nunca lança exceção + circuit breaker."""
from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest

from src.ml_client import FALHAS_PARA_ABRIR, MLClient, PredictionResult


def _lote() -> dict:
    return {
        "lote_id": "LG-2026-00101",
        "status_raw": "EM AJUSTE",
        "turno": "tarde",
        "tem_obs": False,
    }


def _resposta_ok() -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "lote_id": "LG-2026-00101",
        "classe": "revisar",
        "probabilidade": 0.91,
        "nivel_confianca": "alta",
        "latencia_ms": 12.5,
        "acao": "revisar",
    }
    return resp


@pytest.mark.unit
def test_mlclient_sucesso_retorna_resultado() -> None:
    http = MagicMock()
    http.post.return_value = _resposta_ok()
    cliente = MLClient(url="http://api-teste:8000", http_client=http)

    resultado = cliente.classificar(_lote())

    assert resultado is not None
    assert isinstance(resultado, PredictionResult)
    assert resultado.classe == "revisar"
    assert resultado.probabilidade == 0.91
    assert resultado.nivel_confianca == "alta"
    http.post.assert_called_once()
    cliente.fechar()


@pytest.mark.unit
def test_mlclient_api_fora_retorna_none_sem_excecao() -> None:
    http = MagicMock()
    http.post.side_effect = httpx.ConnectError("API indisponível")
    cliente = MLClient(url="http://api-caiu:8000", http_client=http)

    resultado = cliente.classificar(_lote())

    assert resultado is None
    assert cliente.falhas_consecutivas == 1
    assert cliente.circuito_aberto is False
    cliente.fechar()


@pytest.mark.unit
def test_mlclient_circuit_breaker_abre_na_sexta_sem_chamar_rede() -> None:
    http = MagicMock()
    http.post.side_effect = httpx.ReadTimeout("timeout")
    cliente = MLClient(url="http://api-lenta:8000", http_client=http)

    for _ in range(FALHAS_PARA_ABRIR):
        assert cliente.classificar(_lote()) is None

    assert cliente.circuito_aberto is True
    http.post.reset_mock()

    sexta = cliente.classificar(_lote())
    assert sexta is None
    http.post.assert_not_called()
    cliente.fechar()


@pytest.mark.unit
def test_mlclient_http_500_e_json_invalido_viram_none() -> None:
    http = MagicMock()
    resp_500 = MagicMock()
    resp_500.status_code = 500
    http.post.return_value = resp_500
    cliente = MLClient(http_client=http)
    assert cliente.classificar(_lote()) is None

    resp_json = MagicMock()
    resp_json.status_code = 200
    resp_json.json.side_effect = ValueError("json inválido")
    http.post.return_value = resp_json
    assert cliente.classificar(_lote()) is None
    cliente.fechar()


@pytest.mark.unit
def test_mlclient_sucesso_zera_falhas_e_reset_reabre() -> None:
    http = MagicMock()
    http.post.side_effect = httpx.ConnectError("falha")
    cliente = MLClient(http_client=http)
    cliente.classificar(_lote())
    assert cliente.falhas_consecutivas == 1

    http.post.side_effect = None
    http.post.return_value = _resposta_ok()
    assert cliente.classificar(_lote()) is not None
    assert cliente.falhas_consecutivas == 0
    assert cliente.circuito_aberto is False

    cliente._circuito_aberto = True
    cliente._falhas_consecutivas = FALHAS_PARA_ABRIR
    cliente.reset()
    assert cliente.circuito_aberto is False
    assert cliente.falhas_consecutivas == 0
    cliente.fechar()


@pytest.mark.unit
def test_mlclient_payload_invalido_e_fechar_sem_excecao() -> None:
    http = MagicMock()
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = ["nao", "e", "dict"]
    http.post.return_value = resp
    cliente = MLClient(http_client=http)
    assert cliente.classificar(_lote()) is None

    resp.json.return_value = {
        "classe": "revisar",
        "probabilidade": 1.5,
        "nivel_confianca": "alta",
    }
    assert cliente.classificar(_lote()) is None

    resp.json.return_value = {"probabilidade": 0.9, "nivel_confianca": "alta"}
    assert cliente.classificar(_lote()) is None

    cliente._http.close.side_effect = RuntimeError("fechar")
    cliente._http_proprio = True
    cliente.fechar()
