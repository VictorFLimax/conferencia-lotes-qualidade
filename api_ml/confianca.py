"""Calibração de confiança do classificador (limiares de negócio, não técnicos).

Por que 0,85 e não 0,95: 0,95 reduziria falsos automáticos, mas mandaria
quase tudo para revisão humana e mataria o ganho de automação. 0,85 equilibra
risco e volume automatizado.
"""
from __future__ import annotations

LIMIAR_ALTA = 0.85
LIMIAR_MEDIA = 0.65

NIVEL_ALTA = "alta"
NIVEL_MEDIA = "média"
NIVEL_BAIXA = "baixa"

ACAO_REVISAR = "revisar"
ACAO_REVISAR_PRIORITARIO = "revisar_prioritario"


def nivel_confianca(probabilidade: float) -> str:
    """alta (≥0,85) | média ([0,65, 0,85)) | baixa (<0,65)."""
    if probabilidade >= LIMIAR_ALTA:
        return NIVEL_ALTA
    if probabilidade >= LIMIAR_MEDIA:
        return NIVEL_MEDIA
    return NIVEL_BAIXA


def acao_calibrada(classe_prevista: str, probabilidade: float) -> str:
    """Ação operacional a partir da classe prevista e da confiança.

    - alta → aplica a classe prevista automaticamente
    - média → revisar
    - baixa → revisar_prioritario
    """
    nivel = nivel_confianca(probabilidade)
    if nivel == NIVEL_ALTA:
        return classe_prevista
    if nivel == NIVEL_MEDIA:
        return ACAO_REVISAR
    return ACAO_REVISAR_PRIORITARIO
