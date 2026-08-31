"""
Bot 04: Classificador Híbrido ML (LG_Classificador_ML_V1).
Enriquecimento semântico de causas de divergência.
Princípio Cardeal: ML NUNCA decide o STATUS final do item, apenas enriquece com causa_sugerida.
Totalmente isolado: qualquer falha ativa Fallback Determinístico sem propagar exceção.
The DX Way.
"""

import logging
from typing import Any, Dict, List, Optional
import httpx
from core.config import settings
from core.resilience import CircuitBreaker

logger = logging.getLogger("bots.ml_classifier")


class MLClassifierBot:
    """
    Bot 04 - Classificador NLP/ML para enriquecimento de causa provável.
    Controlado por feature flag e limiar mínimo de confiança.
    """

    def __init__(self, api_url: Optional[str] = None):
        self.bot_id = "LG_Classificador_ML_V1"
        self.api_url = api_url or settings.ML_API_URL
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

    def run(self, consolidator_result: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.bot_id}] Iniciando enriquecimento de causa provável com ML...")

        itens = consolidator_result.get("itens", [])
        itens_enriquecidos = []

        for item in itens:
            enriquecido = dict(item)

            # Se for OK ou não exigir análise de ML, mantém direto
            if not item.get("exige_analise_ml", False):
                enriquecido["causa_divergencia"] = "CONFORME_SEM_DIVERGENCIA"
                enriquecido["origem_decisao"] = "REGRA_DETERMINISTICA"
                enriquecido["confianca_ml"] = 1.0
                itens_enriquecidos.append(enriquecido)
                continue

            # Verificação de Feature Flag
            if not settings.ML_ENABLED:
                logger.info(f"[{self.bot_id}] ML desativado via Feature Flag. Aplicando fallback determinístico.")
                enriquecido["causa_divergencia"] = "REVISAO_MANUAL_REGRA_PADRAO"
                enriquecido["origem_decisao"] = "FALLBACK_DETERMINISTICO"
                enriquecido["confianca_ml"] = 0.0
                itens_enriquecidos.append(enriquecido)
                continue

            # Chamada protegida ao modelo de ML (Isolamento Universal)
            predicao = self._chamar_modelo_com_fallback(item.get("observacao", ""))
            enriquecido["causa_divergencia"] = predicao["causa_sugerida"]
            enriquecido["origem_decisao"] = predicao["origem_decisao"]
            enriquecido["confianca_ml"] = predicao["confianca_ml"]
            itens_enriquecidos.append(enriquecido)

        logger.info(f"[{self.bot_id}] Enriquecimento concluído para {len(itens_enriquecidos)} itens.")

        return {
            "bot_id": self.bot_id,
            "status": "COMPLETED",
            "itens": itens_enriquecidos,
        }

    def _chamar_modelo_com_fallback(self, texto_observacao: str) -> Dict[str, Any]:
        """
        Isolamento absoluto: NENHUMA exceção pode escapar desta função.
        Se ocorrer timeout, erro 500, conexão recusada, payload quebrado ou confiança < limiar:
        retorna FALLBACK_DETERMINISTICO.
        """
        fallback_resultado = {
            "causa_sugerida": "REVISAO_MANUAL_REGRA_PADRAO",
            "origem_decisao": "FALLBACK_DETERMINISTICO",
            "confianca_ml": 0.0,
        }

        if not self.circuit_breaker.allow_request():
            logger.warning(f"[{self.bot_id}] Circuit Breaker aberto. Desviando para fallback determinístico.")
            return fallback_resultado

        url = f"{self.api_url}/predict/divergencia"
        try:
            with httpx.Client(timeout=settings.ML_TIMEOUT_SECONDS) as client:
                resp = client.post(url, json={"observacao": texto_observacao})

                if resp.status_code != 200:
                    self.circuit_breaker.record_failure()
                    logger.warning(
                        f"[{self.bot_id}] API de ML retornou HTTP {resp.status_code}. Aplicando fallback."
                    )
                    return fallback_resultado

                data = resp.json()
                categoria = data.get("categoria_provavel")
                confianca = float(data.get("confianca", 0.0))

                # Validação de payload bem-formado
                if not categoria or confianca is None:
                    self.circuit_breaker.record_failure()
                    logger.warning(f"[{self.bot_id}] Resposta do ML malformada. Aplicando fallback.")
                    return fallback_resultado

                # Validação de Limiar de Confiança Mínima
                if confianca < settings.ML_MIN_CONFIDENCE:
                    logger.info(
                        f"[{self.bot_id}] Confiança {confianca:.2f} < limiar {settings.ML_MIN_CONFIDENCE}. "
                        f"Descartando predição e aplicando fallback."
                    )
                    return fallback_resultado

                # Sucesso na predição
                self.circuit_breaker.record_success()
                return {
                    "causa_sugerida": categoria,
                    "origem_decisao": "ML_HYBRID",
                    "confianca_ml": round(confianca, 2),
                }

        except (httpx.TimeoutException, httpx.RequestError, Exception) as exc:
            self.circuit_breaker.record_failure()
            logger.warning(f"[{self.bot_id}] Exceção na inferência do ML ({exc}). Aplicando fallback determinístico.")
            return fallback_resultado
