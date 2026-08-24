"""Limiares de confiança 0,85 e 0,65."""
from __future__ import annotations

import pytest

from api_ml.confianca import acao_calibrada, nivel_confianca


@pytest.mark.unit
@pytest.mark.parametrize(
    "prob, nivel, acao_se_valido",
    [
        (0.85, "alta", "valido_automatico"),
        (0.99, "alta", "valido_automatico"),
        (0.849, "média", "revisar"),
        (0.65, "média", "revisar"),
        (0.649, "baixa", "revisar_prioritario"),
        (0.10, "baixa", "revisar_prioritario"),
    ],
)
def test_calibração_limiares(prob: float, nivel: str, acao_se_valido: str) -> None:
    assert nivel_confianca(prob) == nivel
    assert acao_calibrada("valido_automatico", prob) == acao_se_valido
