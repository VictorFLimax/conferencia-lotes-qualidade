"""Ponto de entrada do bot de conferência de lotes."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.base_referencia import BaseReferencia
from src.config import Config
from src.relatorio import gerar_relatorio_divergencias
from src.validacao import ConferenciaLotes, ResultadoValidacao

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def executar_conferencia(
    caminho_planilha: Path,
    caminho_saida: Path | None = None,
) -> list[ResultadoValidacao]:
    """
    Executa o fluxo principal de conferência de lotes.

    Args:
        caminho_planilha: Caminho da planilha de entrada com os registros a conferir.
        caminho_saida: Caminho opcional para o arquivo de divergências gerado.

    Returns:
        Lista de resultados de validação por registro processado.
    """
    config = Config.carregar()
    base = BaseReferencia(config)
    conferencia = ConferenciaLotes(base)

    logger.info("Iniciando conferência de lotes: %s", caminho_planilha)
    resultados = conferencia.processar_planilha(caminho_planilha)

    divergencias = [r for r in resultados if not r.aprovado]
    if divergencias:
        saida = caminho_saida or config.caminho_saida_relatorio
        gerar_relatorio_divergencias(divergencias, saida)
        logger.info("Relatório de divergências gerado: %s", saida)
    else:
        logger.info("Nenhuma divergência encontrada.")

    return resultados


def main() -> int:
    """Ponto de entrada da aplicação via linha de comando."""
    config = Config.carregar()
    caminho_planilha = config.caminho_planilha_entrada

    if not caminho_planilha.exists():
        logger.error("Planilha de entrada não encontrada: %s", caminho_planilha)
        return 1

    try:
        executar_conferencia(caminho_planilha)
    except Exception:
        logger.exception("Erro ao executar conferência de lotes.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
