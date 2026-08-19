"""Cliente HTTP resiliente da API de ML.

Nunca lança exceção: timeout, rede, HTTP 4xx/5xx e JSON inválido viram None.
Circuit breaker abre após 5 falhas consecutivas e só volta a tentar após
reset() ou reinício do processo.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Mapping, Optional

import httpx

FALHAS_PARA_ABRIR = 5
TIMEOUT_PADRAO_S = 2.5
URL_PADRAO = "http://localhost:8000"


@dataclass(frozen=True)
class PredictionResult:
    lote_id: str
    classe: str
    probabilidade: float
    nivel_confianca: str
    latencia_ms: float | None = None
    acao: str | None = None


class MLClient:
    """Ponte entre o bot e a API. Sem lógica de predição — só HTTP + fallback."""

    def __init__(
        self,
        url: str | None = None,
        timeout: float = TIMEOUT_PADRAO_S,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.base_url = (url or os.getenv("ML_API_URL") or URL_PADRAO).rstrip("/")
        self.timeout = timeout
        self._http = http_client or httpx.Client(timeout=timeout)
        self._http_proprio = http_client is None
        self._falhas_consecutivas = 0
        self._circuito_aberto = False

    @property
    def circuito_aberto(self) -> bool:
        return self._circuito_aberto

    @property
    def falhas_consecutivas(self) -> int:
        return self._falhas_consecutivas

    def reset(self) -> None:
        """Reabre o circuito e zera o contador (reinício manual)."""
        self._falhas_consecutivas = 0
        self._circuito_aberto = False

    def fechar(self) -> None:
        if self._http_proprio:
            try:
                self._http.close()
            except Exception:
                pass

    def classificar(self, lote: Mapping[str, Any]) -> Optional[PredictionResult]:
        """Chama POST /predict. Qualquer falha → None. Circuito aberto → None imediato."""
        try:
            if self._circuito_aberto:
                return None
            payload = {
                "lote_id": str(lote.get("lote_id", "")),
                "status_raw": str(lote.get("status_raw", "")),
                "turno": str(lote.get("turno", "")),
                "tem_obs": bool(lote.get("tem_obs", False)),
            }
            resposta = self._http.post(
                f"{self.base_url}/predict",
                json=payload,
                timeout=self.timeout,
            )
            if resposta.status_code >= 400:
                self._registrar_falha()
                return None
            dados = resposta.json()
            resultado = self._parsear(dados)
            if resultado is None:
                self._registrar_falha()
                return None
            self._falhas_consecutivas = 0
            self._circuito_aberto = False
            return resultado
        except Exception:
            self._registrar_falha()
            return None

    def _registrar_falha(self) -> None:
        self._falhas_consecutivas += 1
        if self._falhas_consecutivas >= FALHAS_PARA_ABRIR:
            self._circuito_aberto = True

    @staticmethod
    def _parsear(dados: Any) -> Optional[PredictionResult]:
        if not isinstance(dados, dict):
            return None
        try:
            classe = dados["classe"]
            probabilidade = float(dados["probabilidade"])
            nivel = str(dados["nivel_confianca"])
            if not (0.0 <= probabilidade <= 1.0):
                return None
            latencia = dados.get("latencia_ms")
            return PredictionResult(
                lote_id=str(dados.get("lote_id", "")),
                classe=str(classe),
                probabilidade=probabilidade,
                nivel_confianca=nivel,
                latencia_ms=None if latencia is None else float(latencia),
                acao=None if dados.get("acao") is None else str(dados.get("acao")),
            )
        except (KeyError, TypeError, ValueError):
            return None
