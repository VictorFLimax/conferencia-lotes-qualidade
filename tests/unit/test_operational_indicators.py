"""Testes unitários da camada de indicadores operacionais (Aula 24)."""
from __future__ import annotations

import pytest

from src.operational_indicators import (
    TEMPO_AUTOMATIZADO_SEGUNDOS_POR_REGISTRO,
    TEMPO_MANUAL_SEGUNDOS_POR_REGISTRO,
    _percentual,
    calcular_indicadores,
)
from src.validacao_aula22 import (
    CLASSIFICACAO_AMBIGUO,
    CLASSIFICACAO_DIVERGENCIA,
    CLASSIFICACAO_ERRO,
    CLASSIFICACAO_VALIDO,
    RegistroValidado,
)


def _registro(
    classificacao: str,
    regra_aplicada: str,
    lote_id: str = "LG-2026-00001",
) -> RegistroValidado:
    return RegistroValidado(
        lote_id=lote_id,
        produto="TV55-4K-B",
        linha="L1",
        turno="A",
        status_original="APROVADO",
        status_normalizado="APROVADO",
        responsavel="Ana",
        data="15/06/2026",
        observacao="",
        data_referencia="15/06/2026",
        classificacao=classificacao,
        regra=regra_aplicada,
        mensagem="teste",
        regra_aplicada=regra_aplicada,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "parte, total, esperado",
    [
        (25, 100, 25.0),
        (1, 4, 25.0),
        (0, 10, 0.0),
        (5, 0, 0.0),
        (0, 0, 0.0),
    ],
    ids=["normal", "fracao", "parte_zero", "total_zero", "ambos_zero"],
)
def test_percentual_casos(parte: float, total: float, esperado: float) -> None:
    assert _percentual(parte, total) == esperado


@pytest.mark.unit
def test_percentual_divisao_por_zero_nao_levanta() -> None:
    assert _percentual(10, 0) == 0.0


def _conjunto_conhecido() -> list[RegistroValidado]:
    """10 registros: 5 válidos, 2 divergências, 1 ambíguo, 2 erros."""
    return [
        _registro(CLASSIFICACAO_VALIDO, "RN08", "L1"),
        _registro(CLASSIFICACAO_VALIDO, "RN08", "L2"),
        _registro(CLASSIFICACAO_VALIDO, "RN08", "L3"),
        _registro(CLASSIFICACAO_VALIDO, "RN08", "L4"),
        _registro(CLASSIFICACAO_VALIDO, "RN08", "L5"),
        _registro(CLASSIFICACAO_DIVERGENCIA, "RN11", "L6"),
        _registro(CLASSIFICACAO_DIVERGENCIA, "RN10", "L7"),
        _registro(CLASSIFICACAO_AMBIGUO, "RN09", "L8"),
        _registro(CLASSIFICACAO_ERRO, "RN12", "L9"),
        _registro(CLASSIFICACAO_ERRO, "RN01, RN12", "L10"),
    ]


@pytest.mark.unit
def test_dez_indicadores_conjunto_conhecido() -> None:
    indicadores = calcular_indicadores(_conjunto_conhecido())

    # 1 total
    assert indicadores.total_registros == 10
    # 2 válidos
    assert indicadores.validos_qtd == 5
    assert indicadores.validos_pct == _percentual(5, 10)
    # 3 divergências
    assert indicadores.divergencias_qtd == 2
    assert indicadores.divergencias_pct == _percentual(2, 10)
    # 4 ambíguos
    assert indicadores.ambiguos_qtd == 1
    assert indicadores.ambiguos_pct == _percentual(1, 10)
    # 5 erros
    assert indicadores.erros_qtd == 2
    assert indicadores.erros_pct == _percentual(2, 10)
    # 6 regra mais acionada (mesmo Counter do ranking)
    assert indicadores.regra_mais_acionada_codigo == "RN08"
    assert indicadores.regra_mais_acionada_qtd == 5
    assert indicadores.ranking_regras[0].codigo == indicadores.regra_mais_acionada_codigo
    assert indicadores.contagem_regras.most_common(1)[0][0] == "RN08"
    # RN12 aparece no erro simples e no composto
    assert indicadores.contagem_regras["RN12"] == 2
    # 7 qualidade da entrada
    assert indicadores.taxa_qualidade_entrada == _percentual(8, 10)
    # 8 revisão humana
    assert indicadores.taxa_revisao_humana == _percentual(1, 10)
    # 9 retrabalho
    assert indicadores.taxa_retrabalho == _percentual(2, 10)
    # 10 ganho de tempo
    esperado_ganho = 10 * (
        TEMPO_MANUAL_SEGUNDOS_POR_REGISTRO - TEMPO_AUTOMATIZADO_SEGUNDOS_POR_REGISTRO
    )
    assert indicadores.ganho_tempo_segundos == esperado_ganho
    assert indicadores.tempo_manual_segundos == TEMPO_MANUAL_SEGUNDOS_POR_REGISTRO
    assert indicadores.tempo_automatizado_segundos == TEMPO_AUTOMATIZADO_SEGUNDOS_POR_REGISTRO


@pytest.mark.unit
def test_indicadores_lista_vazia() -> None:
    indicadores = calcular_indicadores([])
    assert indicadores.total_registros == 0
    assert indicadores.validos_pct == 0.0
    assert indicadores.divergencias_pct == 0.0
    assert indicadores.ambiguos_pct == 0.0
    assert indicadores.erros_pct == 0.0
    assert indicadores.taxa_qualidade_entrada == 0.0
    assert indicadores.taxa_revisao_humana == 0.0
    assert indicadores.taxa_retrabalho == 0.0
    assert indicadores.ganho_tempo_segundos == 0.0
    assert indicadores.regra_mais_acionada_codigo == ""
    assert indicadores.ranking_regras == []


@pytest.mark.unit
def test_extrair_codigos_regra_vazia() -> None:
    from src.operational_indicators import extrair_codigos_regra

    assert extrair_codigos_regra("") == []
    assert extrair_codigos_regra("sem codigo") == []
