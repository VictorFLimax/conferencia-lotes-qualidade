"""Regras de negócio e orquestração da conferência de lotes."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

import pandas as pd

if TYPE_CHECKING:
  from src.base_referencia import BaseReferencia

COLUNAS_ESPERADAS: list[str] = [
  "lote_id",
  "produto",
  "linha",
  "turno",
  "status",
  "responsavel",
]

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
  """Resultado da verificação de estrutura da planilha."""

  colunas_esperadas: list[str]
  colunas_presentes: list[str]
  colunas_ausentes: list[str]
  estrutura_completa: bool


def _valor_vazio(valor: Any) -> bool:
  """Retorna True se o valor for considerado vazio."""
  if valor is None:
    return True
  if isinstance(valor, float) and pd.isna(valor):
    return True
  if isinstance(valor, str) and valor.strip() == "":
    return True
  return False


def _obter_valor(registro: dict[str, Any] | pd.Series, campo: str) -> Any:
  """Obtém o valor de um campo a partir de dict ou Series."""
  if isinstance(registro, pd.Series):
    if campo not in registro.index:
      return None
    return registro[campo]
  return registro.get(campo)


def valida_estrutura(dados: pd.DataFrame) -> ResultadoEstrutura:
  """
  Verifica a estrutura dos dados sem interromper o fluxo se faltar coluna.

  Args:
    dados: DataFrame com os registros da planilha de entrada.

  Returns:
    Resultado indicando colunas presentes, ausentes e se a estrutura está completa.
  """
  colunas_presentes = [col for col in COLUNAS_ESPERADAS if col in dados.columns]
  colunas_ausentes = [col for col in COLUNAS_ESPERADAS if col not in dados.columns]

  return ResultadoEstrutura(
    colunas_esperadas=list(COLUNAS_ESPERADAS),
    colunas_presentes=colunas_presentes,
    colunas_ausentes=colunas_ausentes,
    estrutura_completa=len(colunas_ausentes) == 0,
  )


def valida_campos_obrigatorios(registro: dict[str, Any] | pd.Series) -> None:
  """
  Verifica se os campos obrigatórios estão preenchidos.

  Args:
    registro: Linha ou dicionário com os dados do lote.

  Raises:
    CamposObrigatoriosVaziosError: Se algum campo obrigatório estiver vazio.
  """
  campos_vazios = [
    campo
    for campo in CAMPOS_OBRIGATORIOS
    if _valor_vazio(_obter_valor(registro, campo))
  ]

  if campos_vazios:
    raise CamposObrigatoriosVaziosError(campos_vazios)


@dataclass(frozen=True)
class RegistroLote:
  """Representa um registro de lote a ser conferido."""

  numero_lote: str
  codigo_produto: str
  quantidade: float
  data_fabricacao: str
  data_validade: str
  status: str
  dados_extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class Divergencia:
  """Detalhe de uma divergência encontrada em uma regra de negócio."""

  regra: str
  mensagem: str
  valor_esperado: Any | None = None
  valor_encontrado: Any | None = None


@dataclass
class ResultadoValidacao:
  """Resultado consolidado da validação de um registro."""

  registro: RegistroLote
  aprovado: bool
  divergencias: list[Divergencia] = field(default_factory=list)


class RegraNegocio(Protocol):
  """Contrato para implementação de regras de negócio (RN01–RN07)."""

  codigo: str

  def validar(
    self,
    registro: RegistroLote,
    referencia: dict[str, Any] | None,
  ) -> list[Divergencia]:
    """
    Valida um registro contra a regra de negócio.

    Args:
      registro: Registro da planilha de entrada.
      referencia: Dados da base de referência para o lote, se existirem.

    Returns:
      Lista de divergências encontradas (vazia se aprovado).
    """
    ...


def rn01_lote_existe(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN01: Verifica se o número do lote existe na base de referência.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN01 ainda não implementada.")


def rn02_produto_corresponde(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN02: Verifica se o código do produto corresponde ao cadastrado na base.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN02 ainda não implementada.")


def rn03_quantidade_valida(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN03: Valida se a quantidade informada está dentro dos limites esperados.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN03 ainda não implementada.")


def rn04_datas_validas(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN04: Valida datas de fabricação e validade (formato e consistência).

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN04 ainda não implementada.")


def rn05_status_permitido(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN05: Verifica se o status do lote está entre os valores permitidos.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN05 ainda não implementada.")


def rn06_lote_nao_vencido(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN06: Verifica se o lote não está vencido na data da conferência.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN06 ainda não implementada.")


def rn07_campos_obrigatorios(
  registro: RegistroLote,
  referencia: dict[str, Any] | None,
) -> list[Divergencia]:
  """
  RN07: Garante que todos os campos obrigatórios estão preenchidos.

  Args:
    registro: Registro a validar.
    referencia: Dados do lote na base de referência.

  Returns:
    Divergências encontradas.
  """
  raise NotImplementedError("RN07 ainda não implementada.")


REGRAS_NEGOCIO: list[tuple[str, Any]] = [
  ("RN01", rn01_lote_existe),
  ("RN02", rn02_produto_corresponde),
  ("RN03", rn03_quantidade_valida),
  ("RN04", rn04_datas_validas),
  ("RN05", rn05_status_permitido),
  ("RN06", rn06_lote_nao_vencido),
  ("RN07", rn07_campos_obrigatorios),
]


def registro_de_linha(linha: pd.Series) -> RegistroLote:
  """
  Converte uma linha do DataFrame em um `RegistroLote`.

  Args:
    linha: Série pandas representando uma linha da planilha.

  Returns:
    Instância de `RegistroLote` mapeada a partir das colunas.
  """
  return RegistroLote(
    numero_lote=str(linha.get("numero_lote", "")),
    codigo_produto=str(linha.get("codigo_produto", "")),
    quantidade=float(linha.get("quantidade", 0)),
    data_fabricacao=str(linha.get("data_fabricacao", "")),
    data_validade=str(linha.get("data_validade", "")),
    status=str(linha.get("status", "")),
  )


class ConferenciaLotes:
  """Orquestra a leitura da planilha e aplicação das regras de negócio."""

  def __init__(self, base_referencia: BaseReferencia) -> None:
    """
    Inicializa o serviço de conferência.

    Args:
      base_referencia: Cliente de consulta à base de lotes de referência.
    """
    self._base = base_referencia

  def validar_registro(self, registro: RegistroLote) -> ResultadoValidacao:
    """
    Aplica todas as regras de negócio a um único registro.

    Args:
      registro: Registro de lote a validar.

    Returns:
      Resultado consolidado com status de aprovação e divergências.
    """
    referencia = self._base.buscar_lote(registro.numero_lote)
    divergencias: list[Divergencia] = []

    for codigo, funcao_regra in REGRAS_NEGOCIO:
      try:
        encontradas = funcao_regra(registro, referencia)
        divergencias.extend(encontradas)
      except NotImplementedError:
        pass

    return ResultadoValidacao(
      registro=registro,
      aprovado=len(divergencias) == 0,
      divergencias=divergencias,
    )

  def processar_planilha(self, caminho: Path) -> list[ResultadoValidacao]:
    """
    Lê a planilha de entrada e valida todos os registros.

    Args:
      caminho: Caminho do arquivo Excel de entrada.

    Returns:
      Lista de resultados de validação, um por linha da planilha.
    """
    df = pd.read_excel(caminho)
    return [self.validar_registro(registro_de_linha(linha)) for _, linha in df.iterrows()]
