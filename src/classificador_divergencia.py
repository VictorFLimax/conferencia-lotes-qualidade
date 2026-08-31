"""Classificador de Divergência com Feature Flag, Timeout e Fallback (S10-B).

Este módulo implementa a camada de ML de forma isolada, garantindo que:
1. A feature flag ML_ENABLED controle a execução sem alterar o código do bot.
2. Nenhuma exceção se propague para o loop principal do bot.
3. Os campos 'origem_decisao' (ml/fallback) e 'confianca_ml' sejam sempre retornados.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)

@dataclass
class ResultadoClassificacao:
    causa_provavel: str
    origem_decisao: str  # 'ml' ou 'fallback'
    confianca_ml: float  # 0.0 a 1.0, ou 0.0 se fallback
    mensagem_fallback: str = ""

class ClassificadorDivergencia:
    def __init__(self, ml_enabled: bool, ml_confianca_minima: float, ml_api_url: str):
        self.ml_enabled = ml_enabled
        self.ml_confianca_minima = ml_confianca_minima
        self.ml_api_url = ml_api_url.rstrip("/")
        # Timeout curto para não travar o bot (requisito de resiliência)
        self._http = httpx.Client(timeout=2.5)

    def classificar(self, observacao: str, **kwargs: Any) -> ResultadoClassificacao:
        """Classifica a causa provável da divergência a partir da observação.
        NUNCA lança exceção para o chamador.
        """
        if not self.ml_enabled:
            return self._fallback("ML desativado por feature flag (ML_ENABLED=false)")

        if not observacao or not str(observacao).strip():
            return self._fallback("Observação vazia, impossível classificar")

        try:
            payload = {"texto": str(observacao).strip(), **kwargs}
            response = self._http.post(f"{self.ml_api_url}/predict", json=payload)
            
            if response.status_code >= 400:
                return self._fallback(f"Erro HTTP {response.status_code} na API de ML (Indisponibilidade)")

            data = response.json()
            confianca = float(data.get("probabilidade", 0.0))
            
            if confianca < self.ml_confianca_minima:
                return self._fallback(f"Confiança do modelo ({confianca:.2f}) abaixo do limiar configurado ({self.ml_confianca_minima})")

            return ResultadoClassificacao(
                causa_provavel=str(data.get("classe", "nao_classificado")),
                origem_decisao="ml",
                confianca_ml=confianca
            )
        except httpx.TimeoutException:
            return self._fallback("Timeout na comunicação com a API de ML")
        except httpx.RequestError as e:
            return self._fallback(f"Erro de rede na API de ML: {e}")
        except Exception as e:
            # Captura qualquer exceção inesperada para garantir que o bot não pare
            logger.exception("Erro inesperado no classificador de ML")
            return self._fallback(f"Erro inesperado no classificador: {e}")

    def _fallback(self, motivo: str) -> ResultadoClassificacao:
        logger.warning("Fallback de ML acionado: %s", motivo)
        return ResultadoClassificacao(
            causa_provavel="nao_classificado",
            origem_decisao="fallback",
            confianca_ml=0.0,
            mensagem_fallback=motivo
        )

    def close(self):
        try:
            self._http.close()
        except Exception:
            pass
