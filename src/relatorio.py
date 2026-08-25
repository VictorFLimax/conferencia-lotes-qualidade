"""Geração do relatório de divergências em Excel com rastreabilidade de ML (S10-B)."""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any

def gerar_relatorio_divergencias(resultados: List[Dict[str, Any]], caminho_saida: Path) -> Path:
    if not resultados:
        raise ValueError("Nenhum resultado fornecido para geração do relatório.")

    com_divergencias = [r for r in resultados if not r.get("aprovado", True)]
    
    colunas = [
        "numero_lote", "codigo_produto", "regra", "mensagem", 
        "valor_esperado", "valor_encontrado", "origem_decisao", "confianca_ml"
    ]

    if not com_divergencias:
        df = pd.DataFrame(columns=colunas)
    else:
        linhas = []
        for r in com_divergencias:
            divergencias = r.get("divergencias") or [{"regra": "GERAL", "mensagem": r.get("mensagem", ""), "valor_esperado": "", "valor_encontrado": ""}]
            for div in divergencias:
                linhas.append({
                    "numero_lote": r.get("numero_lote", "DESCONHECIDO"),
                    "codigo_produto": r.get("codigo_produto", "DESCONHECIDO"),
                    "regra": div.get("regra", "GERAL"),
                    "mensagem": div.get("mensagem", r.get("mensagem", "")),
                    "valor_esperado": div.get("valor_esperado", ""),
                    "valor_encontrado": div.get("valor_encontrado", ""),
                    "origem_decisao": r.get("origem_decisao", "fallback"),
                    "confianca_ml": r.get("confianca_ml", 0.0)
                })
        df = pd.DataFrame(linhas, columns=colunas)

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(caminho_saida, index=False, engine="openpyxl")
    return caminho_saida
