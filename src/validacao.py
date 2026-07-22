"""Regras de negócio e orquestração da conferência de lotes."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol
import pandas as pd

if TYPE_CHECKING:
    from src.base_referencia import BaseReferencia

COLUNAS_ESPERADAS: list[str] = ["lote_id", "produto", "linha", "turno", "status", "responsavel"]
CAMPOS_OBRIGATORIOS: list[str] = list(COLUNAS_ESPERADAS)

class ErroValidacao(Exception):
    """Exceção base para erros de validação de lotes."""

class CamposObrigatoriosVaziosError(ErroValidacao):
    """Lançada quando um ou mais campos obrigatórios estão vazios."""
    def __init__(self, campos_vazios: list[str]) -> None:
        self.campos_vazios = campos_vazios
        campos = ", ".join(campos_vazios)
        super().__init__(f"Campos obrigatórios vazios: {campos}")

@dataclass(frozen=True)
class ResultadoEstrutura:
    colunas_esperadas: list[str]
    colunas_presentes: list[str]
    colunas_ausentes: list[str]
    estrutura_completa: bool

def _valor_vazio(valor: Any) -> bool:
    if valor is None: return True
    if isinstance(valor, float) and pd.isna(valor): return True
    if isinstance(valor, str) and valor.strip() == "": return True
    return False

def _obter_valor(registro: dict[str, Any] | pd.Series, campo: str) -> Any:
    if isinstance(registro, pd.Series):
        return registro.get(campo) if campo in registro.index else None
    return registro.get(campo)

def valida_estrutura(dados: pd.DataFrame) -> ResultadoEstrutura:
    colunas_presentes = [col for col in COLUNAS_ESPERADAS if col in dados.columns]
    colunas_ausentes = [col for col in COLUNAS_ESPERADAS if col not in dados.columns]
    return ResultadoEstrutura(
        colunas_esperadas=list(COLUNAS_ESPERADAS),
        colunas_presentes=colunas_presentes,
        colunas_ausentes=colunas_ausentes,
        estrutura_completa=len(colunas_ausentes) == 0,
    )

def valida_campos_obrigatorios(registro: dict[str, Any] | pd.Series) -> None:
    campos_vazios = [campo for campo in CAMPOS_OBRIGATORIOS if _valor_vazio(_obter_valor(registro, campo))]
    if campos_vazios:
        raise CamposObrigatoriosVaziosError(campos_vazios)

@dataclass(frozen=True)
class RegistroLote:
    numero_lote: str
    codigo_produto: str
    quantidade: float
    data_fabricacao: str
    data_validade: str
    status: str
    dados_extras: dict[str, Any] = field(default_factory=dict)

@dataclass
class Divergencia:
    regra: str
    mensagem: str
    valor_esperado: Any | None = None
    valor_encontrado: Any | None = None

@dataclass
class ResultadoValidacao:
    registro: RegistroLote
    aprovado: bool
    divergencias: list[Divergencia] = field(default_factory=list)

class RegraNegocio(Protocol):
    codigo: str
    def validar(self, registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]: ...

def rn01_lote_existe(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    if referencia is None:
        return [Divergencia(regra="RN01", mensagem="Lote não encontrado na base de referência.", valor_encontrado=registro.numero_lote)]
    return []

def rn02_produto_corresponde(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    if referencia and registro.codigo_produto != referencia.get("codigo_produto"):
        return [Divergencia(regra="RN02", mensagem="Código do produto não corresponde à base.", valor_esperado=referencia.get("codigo_produto"), valor_encontrado=registro.codigo_produto)]
    return []

def rn03_quantidade_valida(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    if referencia and registro.quantidade != referencia.get("quantidade"):
        return [Divergencia(regra="RN03", mensagem="Quantidade divergente da base.", valor_esperado=referencia.get("quantidade"), valor_encontrado=registro.quantidade)]
    return []

def rn04_datas_validas(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    # Lógica simplificada para exemplo
    return []

def rn05_status_permitido(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    if registro.status not in ["APROVADO", "REPROVADO", "EM_ANALISE"]:
        return [Divergencia(regra="RN05", mensagem="Status não permitido.", valor_encontrado=registro.status)]
    return []

def rn06_lote_nao_vencido(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    return []

def rn07_campos_obrigatorios(registro: RegistroLote, referencia: dict[str, Any] | None) -> list[Divergencia]:
    return []

REGRAS_NEGOCIO: list[tuple[str, Any]] = [
    ("RN01", rn01_lote_existe), ("RN02", rn02_produto_corresponde), ("RN03", rn03_quantidade_valida),
    ("RN04", rn04_datas_validas), ("RN05", rn05_status_permitido), ("RN06", rn06_lote_nao_vencido), ("RN07", rn07_campos_obrigatorios),
]

def registro_de_linha(dados: dict[str, Any] | pd.Series) -> RegistroLote:
    """Converte dict (DataPool) ou Series (Pandas) em RegistroLote."""
    get = lambda k: str(dados.get(k, "")).strip() if isinstance(dados, dict) else str(dados.get(k, ""))
    return RegistroLote(
        numero_lote=get("numero_lote"),
        codigo_produto=get("codigo_produto"),
        quantidade=float(dados.get("quantidade", 0) or 0),
        data_fabricacao=get("data_fabricacao"),
        data_validade=get("data_validade"),
        status=get("status"),
        dados_extras={"origem": "datapool" if isinstance(dados, dict) else "pandas"}
    )

class ConferenciaLotes:
    def __init__(self, base_referencia: BaseReferencia) -> None:
        self._base = base_referencia

    def validar_registro(self, registro: RegistroLote) -> ResultadoValidacao:
        referencia = self._base.buscar_lote(registro.numero_lote)
        divergencias: list[Divergencia] = []
        for codigo, funcao_regra in REGRAS_NEGOCIO:
            try:
                divergencias.extend(funcao_regra(registro, referencia))
            except NotImplementedError:
                pass
        return ResultadoValidacao(registro=registro, aprovado=len(divergencias) == 0, divergencias=divergencias)
