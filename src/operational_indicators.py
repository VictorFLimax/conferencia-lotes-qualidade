"""Camada de consolidação operacional (Aula 24).

Recebe a lista de RegistroValidado já classificada e calcula os 10 indicadores.
Não conhece Excel, Markdown nem pytest — é a única fonte de verdade numérica.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from src.validacao_aula22 import (
    CLASSIFICACAO_AMBIGUO,
    CLASSIFICACAO_DIVERGENCIA,
    CLASSIFICACAO_ERRO,
    CLASSIFICACAO_VALIDO,
    RegistroValidado,
)

# Premissas didáticas do ganho de tempo (indicador 10). NÃO são cronometragens
# de produção: seriam reais apenas com medição de tempo por lote em operação.
TEMPO_MANUAL_SEGUNDOS_POR_REGISTRO = 120.0  # 2 minutos por registro, conferência manual
TEMPO_AUTOMATIZADO_SEGUNDOS_POR_REGISTRO = 5.0  # 5 segundos por registro no fluxo automático

# Limiares apenas para sinal visual no dashboard (não são critério de aceite).
META_QUALIDADE_ENTRADA_PCT = 80.0
META_REVISAO_HUMANA_PCT = 15.0
META_RETRABALHO_PCT = 6.0

_RE_CODIGO_RN = re.compile(r"RN\d+")

NOMES_REGRAS: dict[str, str] = {
    "RN01": "Lote sem identificação",
    "RN02": "Produto não informado",
    "RN03": "Linha de produção não informada",
    "RN04": "Status não informado",
    "RN05": "Lote ausente na base de referência",
    "RN06": "Normalização de OK para APROVADO",
    "RN07": "Normalização de NOK para REPROVADO",
    "RN08": "Registro aceito com status padronizado",
    "RN09": "Status ambíguo (revisão humana)",
    "RN10": "Reprovado sem observação",
    "RN11": "Lote duplicado no mesmo dia",
    "RN12": "Data de inspeção ausente ou fora do formato",
}


def _percentual(parte: float, total: float) -> float:
    """(parte / total) * 100, retornando 0.0 quando total == 0 (sem exceção)."""
    if total == 0:
        return 0.0
    return (parte / total) * 100


def extrair_codigos_regra(regra_aplicada: str) -> list[str]:
    """Extrai códigos RN a partir de regra_aplicada (ex.: 'RN01, RN12' → dois códigos)."""
    if not regra_aplicada:
        return []
    return _RE_CODIGO_RN.findall(regra_aplicada)


def nome_da_regra(codigo: str) -> str:
    return NOMES_REGRAS.get(codigo, codigo)


@dataclass(frozen=True)
class RankingRegra:
    codigo: str
    nome: str
    ocorrencias: int
    percentual: float


@dataclass
class OperationalIndicators:
    """Os 10 indicadores operacionais de uma execução."""

    total_registros: int
    validos_qtd: int
    validos_pct: float
    divergencias_qtd: int
    divergencias_pct: float
    ambiguos_qtd: int
    ambiguos_pct: float
    erros_qtd: int
    erros_pct: float
    regra_mais_acionada_codigo: str
    regra_mais_acionada_nome: str
    regra_mais_acionada_qtd: int
    taxa_qualidade_entrada: float
    taxa_revisao_humana: float
    taxa_retrabalho: float
    ganho_tempo_segundos: float
    tempo_manual_segundos: float
    tempo_automatizado_segundos: float
    contagem_regras: Counter[str] = field(default_factory=Counter)
    ranking_regras: list[RankingRegra] = field(default_factory=list)

    @property
    def ganho_tempo_minutos(self) -> float:
        return self.ganho_tempo_segundos / 60.0

    @property
    def ganho_tempo_horas(self) -> float:
        return self.ganho_tempo_segundos / 3600.0


def calcular_indicadores(
    registros: list[RegistroValidado],
    *,
    tempo_manual: float = TEMPO_MANUAL_SEGUNDOS_POR_REGISTRO,
    tempo_automatizado: float = TEMPO_AUTOMATIZADO_SEGUNDOS_POR_REGISTRO,
) -> OperationalIndicators:
    """Consolida os 10 indicadores a partir da lista já validada.

    A contagem por regra (indicador 6 e ranking) usa um único Counter
    alimentado pelo campo regra_aplicada de cada registro.
    """
    total = len(registros)
    validos = sum(1 for r in registros if r.classificacao == CLASSIFICACAO_VALIDO)
    divergencias = sum(
        1 for r in registros if r.classificacao == CLASSIFICACAO_DIVERGENCIA
    )
    ambiguos = sum(1 for r in registros if r.classificacao == CLASSIFICACAO_AMBIGUO)
    erros = sum(1 for r in registros if r.classificacao == CLASSIFICACAO_ERRO)

    contagem: Counter[str] = Counter()
    for registro in registros:
        for codigo in extrair_codigos_regra(registro.regra_aplicada):
            contagem[codigo] += 1

    ranking: list[RankingRegra] = [
        RankingRegra(
            codigo=codigo,
            nome=nome_da_regra(codigo),
            ocorrencias=qtd,
            percentual=_percentual(qtd, total),
        )
        for codigo, qtd in contagem.most_common()
    ]

    if ranking:
        topo = ranking[0]
        codigo_topo, nome_topo, qtd_topo = topo.codigo, topo.nome, topo.ocorrencias
    else:
        codigo_topo, nome_topo, qtd_topo = "", "nenhuma", 0

    return OperationalIndicators(
        total_registros=total,
        validos_qtd=validos,
        validos_pct=_percentual(validos, total),
        divergencias_qtd=divergencias,
        divergencias_pct=_percentual(divergencias, total),
        ambiguos_qtd=ambiguos,
        ambiguos_pct=_percentual(ambiguos, total),
        erros_qtd=erros,
        erros_pct=_percentual(erros, total),
        regra_mais_acionada_codigo=codigo_topo,
        regra_mais_acionada_nome=nome_topo,
        regra_mais_acionada_qtd=qtd_topo,
        taxa_qualidade_entrada=_percentual(total - erros, total),
        taxa_revisao_humana=_percentual(ambiguos, total),
        taxa_retrabalho=_percentual(divergencias, total),
        ganho_tempo_segundos=total * (tempo_manual - tempo_automatizado),
        tempo_manual_segundos=tempo_manual,
        tempo_automatizado_segundos=tempo_automatizado,
        contagem_regras=contagem,
        ranking_regras=ranking,
    )
