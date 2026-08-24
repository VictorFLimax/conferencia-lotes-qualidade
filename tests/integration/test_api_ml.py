"""Testes da API FastAPI de predição (Exercício 24-A)."""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api_ml.confianca import LIMIAR_ALTA, LIMIAR_MEDIA, nivel_confianca
from api_ml.encoding import CLASSES_SAIDA
from api_ml.main import app

CAMINHO_MODELO = Path(__file__).resolve().parents[2] / "models" / "classificador_lotes.pkl"


def _payload(**overrides):
    base = {
        "lote_id": "LG-2026-00999",
        "status_raw": "EM AJUSTE",
        "turno": "manhã",
        "tem_obs": True,
    }
    base.update(overrides)
    return base


@pytest.fixture(scope="module")
def client():
    if not CAMINHO_MODELO.exists():
        pytest.skip("Modelo não treinado. Rode: python train_model.py")
    with TestClient(app) as test_client:
        yield test_client


@pytest.mark.integration
def test_predict_payload_valido_retorna_prediction_output(client: TestClient) -> None:
    resposta = client.post("/predict", json=_payload())
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["lote_id"] == "LG-2026-00999"
    assert corpo["classe"] in CLASSES_SAIDA
    assert 0.0 <= corpo["probabilidade"] <= 1.0
    esperado = nivel_confianca(corpo["probabilidade"])
    assert corpo["nivel_confianca"] == esperado
    if corpo["probabilidade"] >= LIMIAR_ALTA:
        assert esperado == "alta"
    elif corpo["probabilidade"] >= LIMIAR_MEDIA:
        assert esperado == "média"
    else:
        assert esperado == "baixa"


@pytest.mark.integration
def test_predict_turno_invalido_retorna_422(client: TestClient) -> None:
    resposta = client.post("/predict", json=_payload(turno="madrugada"))
    assert resposta.status_code == 422


@pytest.mark.integration
def test_health_modelo_carregado(client: TestClient) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["modelo_carregado"] is True
