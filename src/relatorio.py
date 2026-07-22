"""Geração do relatório de divergências em Excel."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from src.validacao import Divergencia, ResultadoValidacao

def _divergencias_para_dataframe(resultados: list[ResultadoValidacao]) -> pd.DataFrame:
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
    return pd.DataFrame(linhas, columns=["numero_lote", "codigo_produto", "regra", "mensagem", "valor_esperado", "valor_encontrado"])

def gerar_relatorio_divergencias(resultados: list[ResultadoValidacao], caminho_saida: Path) -> Path:
    if not resultados:
        raise ValueError("Nenhum resultado fornecido para geração do relatório.")
    com_divergencias = [r for r in resultados if r.divergencias]
    if not com_divergencias:
        raise ValueError("Nenhuma divergência encontrada nos resultados.")
    
    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df = _divergencias_para_dataframe(com_divergencias)
    df.to_excel(caminho_saida, index=False, engine="openpyxl")
    return caminho_saida
