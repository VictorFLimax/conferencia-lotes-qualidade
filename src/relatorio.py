"""Geração do relatório de divergências em Excel."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.validacao import Divergencia, ResultadoValidacao


def _divergencias_para_dataframe(
  resultados: list[ResultadoValidacao],
) -> pd.DataFrame:
  """
  Converte resultados com divergências em um DataFrame tabular.

  Args:
    resultados: Lista de resultados de validação com falhas.

  Returns:
    DataFrame pronto para exportação.
  """
  linhas: list[dict[str, object]] = []

  for resultado in resultados:
    for div in resultado.divergencias:
      linhas.append({
        "numero_lote": resultado.registro.numero_lote,
        "codigo_produto": resultado.registro.codigo_produto,
        "regra": div.regra,
        "mensagem": div.mensagem,
        "valor_esperado": div.valor_esperado,
        "valor_encontrado": div.valor_encontrado,
      })

  colunas = [
    "numero_lote",
    "codigo_produto",
    "regra",
    "mensagem",
    "valor_esperado",
    "valor_encontrado",
  ]
  return pd.DataFrame(linhas, columns=colunas)


def gerar_relatorio_divergencias(
  resultados: list[ResultadoValidacao],
  caminho_saida: Path,
) -> Path:
  """
  Gera o arquivo `divergencias.xlsx` com os registros que falharam na validação.

  Args:
    resultados: Resultados de validação contendo divergências.
    caminho_saida: Caminho completo do arquivo Excel de saída.

  Returns:
    Caminho do arquivo gerado.

  Raises:
    ValueError: Se a lista de resultados estiver vazia ou sem divergências.
  """
  if not resultados:
    raise ValueError("Nenhum resultado fornecido para geração do relatório.")

  com_divergencias = [r for r in resultados if r.divergencias]
  if not com_divergencias:
    raise ValueError("Nenhuma divergência encontrada nos resultados.")

  caminho_saida.parent.mkdir(parents=True, exist_ok=True)
  df = _divergencias_para_dataframe(com_divergencias)
  df.to_excel(caminho_saida, index=False, engine="openpyxl")

  return caminho_saida


def formatar_mensagem_divergencia(divergencia: Divergencia) -> str:
  """
  Formata uma divergência para exibição em log ou relatório textual.

  Args:
    divergencia: Instância de divergência.

  Returns:
    Mensagem formatada.
  """
  return f"[{divergencia.regra}] {divergencia.mensagem}"
