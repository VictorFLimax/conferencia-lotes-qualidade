"""API FastAPI de classificação de lotes ambíguos.

O modelo é carregado uma vez no lifespan. Se o .pkl não carregar, o processo
não cai: /health responde 503 e /predict devolve erro coerente.
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from api_ml.confianca import acao_calibrada, nivel_confianca
from api_ml.encoding import CLASSES_SAIDA, turno_permitido, vetor_features

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_MODELO_PADRAO = RAIZ / "models" / "classificador_lotes.pkl"

TURNOS_MSG = "manhã, tarde, noite (ou A/B/C da planilha de inspeção)"


def _caminho_modelo() -> Path:
    bruto = os.getenv("ML_MODEL_PATH", "").strip()
    if bruto:
        return Path(bruto)
    return CAMINHO_MODELO_PADRAO


class LoteInput(BaseModel):
    lote_id: str = Field(..., min_length=1)
    status_raw: str = Field(..., min_length=1)
    turno: str
    tem_obs: bool

    @field_validator("turno")
    @classmethod
    def validar_turno(cls, valor: str) -> str:
        if not turno_permitido(valor):
            raise ValueError(
                f"turno inválido: {valor!r}. Permitidos: {TURNOS_MSG}."
            )
        return valor.strip()


class PredictionOutput(BaseModel):
    lote_id: str
    classe: str
    probabilidade: float
    nivel_confianca: Literal["alta", "média", "baixa"]
    latencia_ms: float | None = None
    acao: str | None = None


class HealthOutput(BaseModel):
    status: str
    modelo_carregado: bool
    detalhe: str | None = None


def _estado_vazio() -> dict[str, Any]:
    return {
        "modelo_carregado": False,
        "artefato": None,
        "erro": "Modelo ainda não foi inicializado.",
    }


def carregar_artefato(caminho: Path) -> dict[str, Any]:
    artefato = joblib.load(caminho)
    if not isinstance(artefato, dict) or "modelo" not in artefato:
        raise ValueError("Artefato inválido: esperado dicionário com chave 'modelo'.")
    return artefato


@asynccontextmanager
async def lifespan(app: FastAPI):
    estado = _estado_vazio()
    caminho = _caminho_modelo()
    try:
        estado["artefato"] = carregar_artefato(caminho)
        estado["modelo_carregado"] = True
        estado["erro"] = None
    except Exception as exc:  # noqa: BLE001 — degradação explícita, sem derrubar o processo
        estado["artefato"] = None
        estado["modelo_carregado"] = False
        estado["erro"] = f"Falha ao carregar modelo em {caminho}: {exc}"
    app.state.ml = estado
    yield
    app.state.ml = _estado_vazio()


app = FastAPI(
    title="API ML — Classificação de lotes ambíguos",
    version="1.0.0",
    lifespan=lifespan,
)


def _estado(request: Request) -> dict[str, Any]:
    return getattr(request.app.state, "ml", _estado_vazio())


@app.get("/health", response_model=HealthOutput)
def health(request: Request) -> HealthOutput | JSONResponse:
    estado = _estado(request)
    if estado.get("modelo_carregado"):
        return HealthOutput(status="ok", modelo_carregado=True)
    return JSONResponse(
        status_code=503,
        content={
            "status": "erro",
            "modelo_carregado": False,
            "detalhe": estado.get("erro") or "Modelo não carregado.",
        },
    )


@app.post("/predict", response_model=PredictionOutput)
def predict(payload: LoteInput, request: Request) -> PredictionOutput:
    inicio = time.perf_counter()
    estado = _estado(request)
    if not estado.get("modelo_carregado") or estado.get("artefato") is None:
        raise HTTPException(
            status_code=503,
            detail=estado.get("erro") or "Modelo não carregado.",
        )

    artefato = estado["artefato"]
    modelo = artefato["modelo"]
    mapa_status = artefato.get("mapa_status")
    mapa_turno = artefato.get("mapa_turno")

    try:
        features = np.array(
            [
                vetor_features(
                    payload.status_raw,
                    payload.turno,
                    payload.tem_obs,
                    mapa_status=mapa_status,
                    mapa_turno=mapa_turno,
                )
            ],
            dtype=float,
        )
        probas = modelo.predict_proba(features)[0]
        indice = int(np.argmax(probas))
        classe = str(modelo.classes_[indice])
        probabilidade = float(probas[indice])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=500,
            detail=f"Falha na predição: {exc}",
        ) from exc

    if classe not in CLASSES_SAIDA:
        # Contrato estável mesmo se o pickle tiver rótulo inesperado.
        classe = str(classe)

    latencia_ms = round((time.perf_counter() - inicio) * 1000.0, 3)
    nivel = nivel_confianca(probabilidade)
    acao = acao_calibrada(classe, probabilidade)
    return PredictionOutput(
        lote_id=payload.lote_id,
        classe=classe,
        probabilidade=round(probabilidade, 6),
        nivel_confianca=nivel,
        latencia_ms=latencia_ms,
        acao=acao,
    )
