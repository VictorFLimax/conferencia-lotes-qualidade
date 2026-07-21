"""Consulta à base de referência de lotes."""
from __future__ import annotations
from typing import Any
from src.config import Config

class BaseReferencia:
    def __init__(self, config: Config) -> None:
        self._config = config
        self._mock: dict[str, dict[str, Any]] = self._carregar_mock()

    def _carregar_mock(self) -> dict[str, dict[str, Any]]:
        return {
            "LOTE-001": {"numero_lote": "LOTE-001", "codigo_produto": "PROD-A", "quantidade": 100.0, "data_fabricacao": "2026-01-15", "data_validade": "2027-01-15", "status": "APROVADO"},
            "LOTE-002": {"numero_lote": "LOTE-002", "codigo_produto": "PROD-B", "quantidade": 250.0, "data_fabricacao": "2026-02-01", "data_validade": "2027-02-01", "status": "APROVADO"},
        }

    def buscar_lote(self, numero_lote: str) -> dict[str, Any] | None:
        if self._config.caminho_base_referencia is not None:
            return self._buscar_em_arquivo(numero_lote)
        return self._mock.get(numero_lote)

    def _buscar_em_arquivo(self, numero_lote: str) -> dict[str, Any] | None:
        raise NotImplementedError("Consulta à base de referência via arquivo ainda não implementada.")

    def listar_lotes(self) -> list[dict[str, Any]]:
        return list(self._mock.values())
