"""Carregamento e gerenciamento de variáveis de ambiente."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

RAIZ_PROJETO = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
  """Configurações da aplicação carregadas a partir do ambiente."""

  caminho_planilha_entrada: Path
  caminho_saida_relatorio: Path
  caminho_base_referencia: Path | None
  log_level: str

  @classmethod
  def carregar(cls, env_path: Path | None = None) -> Config:
    """
    Carrega variáveis de ambiente a partir de um arquivo `.env`.

    Args:
      env_path: Caminho opcional para o arquivo `.env`.
        Se não informado, busca `.env` na raiz do projeto.

    Returns:
      Instância imutável de `Config` com os valores resolvidos.
    """
    caminho_env = env_path or RAIZ_PROJETO / ".env"
    load_dotenv(caminho_env)

    base_ref = os.getenv("CAMINHO_BASE_REFERENCIA", "").strip()
    return cls(
      caminho_planilha_entrada=Path(
        os.getenv(
          "CAMINHO_PLANILHA_ENTRADA",
          "data/samples/planilha_lotes.xlsx",
        )
      ),
      caminho_saida_relatorio=Path(
        os.getenv(
          "CAMINHO_SAIDA_RELATORIO",
          "data/output/divergencias.xlsx",
        )
      ),
      caminho_base_referencia=Path(base_ref) if base_ref else None,
      log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
    )
