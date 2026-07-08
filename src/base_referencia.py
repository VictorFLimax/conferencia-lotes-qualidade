"""Consulta à base de referência de lotes."""

from __future__ import annotations

from typing import Any

from src.config import Config


class BaseReferencia:
  """Cliente para consulta de lotes na base de referência."""

  def __init__(self, config: Config) -> None:
    """
    Inicializa o cliente da base de referência.

    Args:
      config: Configurações da aplicação.
    """
    self._config = config
    self._mock: dict[str, dict[str, Any]] = self._carregar_mock()

  def _carregar_mock(self) -> dict[str, dict[str, Any]]:
    """
  Carrega dados mock para desenvolvimento e testes.

  Returns:
    Dicionário indexado por número de lote com dados de referência.
  """
    return {
      "LOTE-001": {
        "numero_lote": "LOTE-001",
        "codigo_produto": "PROD-A",
        "quantidade": 100.0,
        "data_fabricacao": "2026-01-15",
        "data_validade": "2027-01-15",
        "status": "APROVADO",
      },
      "LOTE-002": {
        "numero_lote": "LOTE-002",
        "codigo_produto": "PROD-B",
        "quantidade": 250.0,
        "data_fabricacao": "2026-02-01",
        "data_validade": "2027-02-01",
        "status": "APROVADO",
      },
    }

  def buscar_lote(self, numero_lote: str) -> dict[str, Any] | None:
    """
    Busca um lote na base de referência pelo número.

    Args:
      numero_lote: Identificador único do lote.

    Returns:
      Dicionário com os dados do lote ou `None` se não encontrado.
    """
    if self._config.caminho_base_referencia is not None:
      return self._buscar_em_arquivo(numero_lote)

    return self._mock.get(numero_lote)

  def _buscar_em_arquivo(self, numero_lote: str) -> dict[str, Any] | None:
    """
    Consulta a base de referência a partir de arquivo externo.

    Args:
      numero_lote: Identificador único do lote.

    Returns:
      Dados do lote ou `None` se não encontrado.

    Raises:
      NotImplementedError: Integração com arquivo real ainda não implementada.
    """
    raise NotImplementedError(
      "Consulta à base de referência via arquivo ainda não implementada."
    )

  def listar_lotes(self) -> list[dict[str, Any]]:
    """
    Retorna todos os lotes disponíveis na base (mock ou arquivo).

    Returns:
      Lista de registros de lotes.
    """
    return list(self._mock.values())
