"""Validação da Aula 22 (AX Academy) — RN01 a RN12.

Módulo isolado do performer BotCity (`src/validacao.py`). Cada registro recebe
EXATAMENTE UMA classificação: Válido | Divergência | Ambíguo | Erro de Entrada.

Precedência (um registro pode violar várias RNs; só a primeira classificação vale):
  1) Erro de Entrada — RN01–RN04 (campos vazios) e RN12 (data inválida)
  2) Divergência por duplicidade no dia — RN11
  3) Divergência por lote ausente na base — RN05
  4) Normalização de status — RN06 (OK→APROVADO) / RN07 (NOK→REPROVADO)
  5) Ambíguo — RN09 (status desconhecido / não normalizável)
  6) Divergência — RN10 (REPROVADO/NOK sem observação)
  7) Válido — RN08 (status padronizado APROVADO/REPROVADO/PENDENTE)
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

CLASSIFICACAO_VALIDO = "Válido"
CLASSIFICACAO_DIVERGENCIA = "Divergência"
CLASSIFICACAO_AMBIGUO = "Ambíguo"
CLASSIFICACAO_ERRO = "Erro de Entrada"

STATUS_PADRAO = frozenset({"APROVADO", "REPROVADO", "PENDENTE"})
STATUS_NORMALIZAVEIS = {"OK": "APROVADO", "NOK": "REPROVADO"}

# Formato estrito DD/MM/AAAA (dia e mês com 2 dígitos, ano com 4)
_RE_DATA_DD_MM_AAAA = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _vazio(valor: Any) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float):
        # pandas/NaN
        try:
            import math

            if math.isnan(valor):
                return True
        except (TypeError, ValueError):
            pass
    texto = str(valor).strip()
    return texto == "" or texto.lower() == "nan"


def _texto(valor: Any) -> str:
    if _vazio(valor):
        return ""
    return str(valor).strip()


@dataclass
class RegistroValidado:
    """Resultado da validação de um registro de inspeção (Aula 22)."""

    lote_id: str
    produto: str
    linha: str
    turno: str
    status_original: str
    status_normalizado: str
    responsavel: str
    data: str
    observacao: str
    data_referencia: str
    classificacao: str
    regra: str
    mensagem: str
    regra_aplicada: str

    def to_dict(self) -> dict[str, Any]:
        """Dicionário amigável para DataFrame / Excel (sem jargão técnico interno)."""
        return {
            "Lote": self.lote_id,
            "Produto": self.produto,
            "Linha": self.linha,
            "Turno": self.turno,
            "Status original": self.status_original,
            "Status": self.status_normalizado,
            "Responsável": self.responsavel,
            "Data inspeção": self.data,
            "Observação": self.observacao,
            "Data referência": self.data_referencia,
            "Classificação": self.classificacao,
            "Regra": self.regra,
            "Mensagem": self.mensagem,
        }


def _montar(
    bruto: dict[str, Any],
    *,
    data_referencia: str,
    status_normalizado: str,
    classificacao: str,
    regra: str,
    mensagem: str,
) -> RegistroValidado:
    return RegistroValidado(
        lote_id=_texto(bruto.get("lote_id")),
        produto=_texto(bruto.get("produto")),
        linha=_texto(bruto.get("linha")),
        turno=_texto(bruto.get("turno")),
        status_original=_texto(bruto.get("status")),
        status_normalizado=status_normalizado,
        responsavel=_texto(bruto.get("responsavel")),
        data=_texto(bruto.get("data")),
        observacao=_texto(bruto.get("observacao")),
        data_referencia=data_referencia,
        classificacao=classificacao,
        regra=regra,
        mensagem=mensagem,
        regra_aplicada=regra,
    )


def validar_registro(
    registro: dict[str, Any],
    lotes_referencia: set[str],
    data_referencia: str,
    ocorrencia_no_dia: int = 1,
) -> RegistroValidado:
    """Classifica um registro segundo RN01–RN12 com a precedência documentada no módulo.

    Args:
        registro: dict com as colunas da planilha diária.
        lotes_referencia: conjunto de lote_id presentes em Base_Referencia.
        data_referencia: data extraída do nome da aba (DD/MM/AAAA).
        ocorrencia_no_dia: 1ª ocorrência do lote no dia = 1; a partir de 2 → RN11.
    """
    lote_id = _texto(registro.get("lote_id"))
    produto = _texto(registro.get("produto"))
    linha = _texto(registro.get("linha"))
    status_original = _texto(registro.get("status"))
    data = _texto(registro.get("data"))
    observacao = _texto(registro.get("observacao"))

    # --- 1) Erro de Entrada: RN01–RN04 (campos obrigatórios vazios) ---
    erros: list[tuple[str, str]] = []
    if _vazio(lote_id):
        erros.append(("RN01", "lote_id vazio"))
    if _vazio(produto):
        erros.append(("RN02", "produto vazio"))
    if _vazio(linha):
        erros.append(("RN03", "linha vazia"))
    if _vazio(status_original):
        erros.append(("RN04", "status vazio"))

    # RN12: data ausente ou fora de DD/MM/AAAA
    if _vazio(data) or not _RE_DATA_DD_MM_AAAA.match(data):
        erros.append(
            (
                "RN12",
                "data de inspeção ausente ou fora do formato DD/MM/AAAA",
            )
        )

    if erros:
        regras = ", ".join(codigo for codigo, _ in erros)
        msgs = "; ".join(msg for _, msg in erros)
        return _montar(
            registro,
            data_referencia=data_referencia,
            status_normalizado=status_original,
            classificacao=CLASSIFICACAO_ERRO,
            regra=regras,
            mensagem=msgs,
        )

    # --- 2) Divergência: RN11 (duplicidade no mesmo dia, a partir da 2ª) ---
    if ocorrencia_no_dia >= 2:
        return _montar(
            registro,
            data_referencia=data_referencia,
            status_normalizado=status_original,
            classificacao=CLASSIFICACAO_DIVERGENCIA,
            regra="RN11",
            mensagem=(
                f"lote duplicado no mesmo dia "
                f"(ocorrência {ocorrencia_no_dia})"
            ),
        )

    # --- 3) Divergência: RN05 (lote inexistente na Base_Referencia) ---
    if lote_id not in lotes_referencia:
        return _montar(
            registro,
            data_referencia=data_referencia,
            status_normalizado=status_original,
            classificacao=CLASSIFICACAO_DIVERGENCIA,
            regra="RN05",
            mensagem="lote_id não encontrado na Base_Referencia",
        )

    # --- 4) Normalização RN06 / RN07 ---
    status_upper = status_original.upper()
    status_normalizado = STATUS_NORMALIZAVEIS.get(status_upper, status_upper)

    # --- 5) Ambíguo: RN09 (status desconhecido e não normalizável) ---
    if status_normalizado not in STATUS_PADRAO:
        return _montar(
            registro,
            data_referencia=data_referencia,
            status_normalizado=status_normalizado,
            classificacao=CLASSIFICACAO_AMBIGUO,
            regra="RN09",
            mensagem=f"status desconhecido para revisão humana: '{status_original}'",
        )

    # --- 6) Divergência: RN10 (REPROVADO sem observação) ---
    # NOK já foi normalizado para REPROVADO no passo 4.
    if status_normalizado == "REPROVADO" and _vazio(observacao):
        return _montar(
            registro,
            data_referencia=data_referencia,
            status_normalizado=status_normalizado,
            classificacao=CLASSIFICACAO_DIVERGENCIA,
            regra="RN10",
            mensagem="lote REPROVADO sem observação preenchida",
        )

    # --- 7) Válido: RN08 (status padronizado aceito) ---
    return _montar(
        registro,
        data_referencia=data_referencia,
        status_normalizado=status_normalizado,
        classificacao=CLASSIFICACAO_VALIDO,
        regra="RN08",
        mensagem="registro válido",
    )
