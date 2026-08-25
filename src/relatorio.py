"""Geração do relatório de divergências em Excel com rastreabilidade de ML (S10-B)."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import Any

# Assumindo que estas classes existem no seu src.validacao
from src.validacao import Divergencia, ResultadoValidacao

def _divergencias_para_dataframe(resultados: list[ResultadoValidacao], dados_ml: list[dict[str, Any]] | None = None) -> pd.DataFrame:
    linhas: list[dict[str, object]] = []
    
    # Mapear dados ML por numero_lote para enriquecer o relatório
    ml_map = {}
    if dados_ml:
        for item in dados_ml:
            ml_map[item.get("numero_lote")] = {
                "origem_decisao": item.get("origem_decisao", "fallback"),
                "confianca_ml": item.get("confianca_ml", 0.0)
            }

    for resultado in resultados:
        for div in resultado.divergencias:
            lote = resultado.registro.numero_lote
            ml_info = ml_map.get(lote, {"origem_decisao": "fallback", "confianca_ml": 0.0})
            
            linhas.append({
                "numero_lote": lote,
                "codigo_produto": resultado.registro.codigo_produto,
                "regra": div.regra,
                "mensagem": div.mensagem,
                "valor_esperado": div.valor_esperado,
                "valor_encontrado": div.valor_encontrado,
                "origem_decisao": ml_info["origem_decisao"],
                "confianca_ml": ml_info["confianca_ml"]
            })
            
    colunas = [
        "numero_lote", "codigo_produto", "regra", "mensagem", 
        "valor_esperado", "valor_encontrado", "origem_decisao", "confianca_ml"
    ]
    return pd.DataFrame(linhas, columns=colunas)

def gerar_relatorio_divergencias(
    resultados: list[ResultadoValidacao], 
    caminho_saida: Path, 
    dados_ml: list[dict[str, Any]] | None = None
) -> Path:
    if not resultados:
        raise ValueError("Nenhum resultado fornecido para geração do relatório.")

    com_divergencias = [r for r in resultados if r.divergencias]
    if not com_divergencias:
        raise ValueError("Nenhuma divergência encontrada nos resultados.")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df = _divergencias_para_dataframe(com_divergencias, dados_ml)
    df.to_excel(caminho_saida, index=False, engine="openpyxl")
    return caminho_saida
