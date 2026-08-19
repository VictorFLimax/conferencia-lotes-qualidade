"""
gerar_relatorio.py — Aula 22 (AX Academy)

Lê a planilha de inspeção de 10 dias, valida cada registro (RN01–RN12) e gera
o Excel `relatorio_conferencia_lotes.xlsx` com dashboard nativo (openpyxl.chart).

Uso:
  python gerar_relatorio.py

Variáveis de ambiente (.env):
  INPUT_FILE   — planilha de entrada (default: dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx)
  OUTPUT_FILE  — Excel de saída (default: relatorio_conferencia_lotes.xlsx na raiz)
  LOG_FILE     — log texto (default: logs/relatorio_aula22.log)
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openpyxl import Workbook
from openpyxl.chart import DoughnutChart, LineChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.series import DataPoint
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils.dataframe import dataframe_to_rows

from src.validacao_aula22 import (
    CLASSIFICACAO_AMBIGUO,
    CLASSIFICACAO_DIVERGENCIA,
    CLASSIFICACAO_ERRO,
    CLASSIFICACAO_VALIDO,
    RegistroValidado,
    validar_registro,
)

RAIZ = Path(__file__).resolve().parent
PADRAO_ABA_DIARIA = re.compile(r"^Insp_(\d{2})_(\d{2})_2026$")
COLUNAS_DIARIAS = [
    "lote_id",
    "produto",
    "linha",
    "turno",
    "status",
    "responsavel",
    "data",
    "observacao",
]


def _carregar_caminhos() -> tuple[Path, Path, Path]:
    """Resolve INPUT_FILE / OUTPUT_FILE / LOG_FILE a partir do .env."""
    load_dotenv(RAIZ / ".env", override=False)

    entrada = Path(
        os.getenv(
            "INPUT_FILE",
            "dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx",
        )
    )
    saida = Path(os.getenv("OUTPUT_FILE", "relatorio_conferencia_lotes.xlsx"))
    log = Path(os.getenv("LOG_FILE", "logs/relatorio_aula22.log"))

    if not entrada.is_absolute():
        entrada = RAIZ / entrada
    if not saida.is_absolute():
        saida = RAIZ / saida
    if not log.is_absolute():
        log = RAIZ / log

    return entrada, saida, log


def _data_referencia_da_aba(nome_aba: str) -> str:
    """Extrai DD/MM/AAAA a partir de Insp_DD_MM_2026."""
    m = PADRAO_ABA_DIARIA.match(nome_aba)
    if not m:
        raise ValueError(f"Nome de aba diária inválido: {nome_aba}")
    dia, mes = m.group(1), m.group(2)
    return f"{dia}/{mes}/2026"


def carregar_base_referencia(caminho: Path) -> set[str]:
    """Lê a aba Base_Referencia (cabeçalho=linha 2, dados a partir da linha 3)."""
    df = pd.read_excel(
        caminho,
        sheet_name="Base_Referencia",
        header=1,  # linha 2 do Excel (0-indexed)
        dtype=str,
    )
    if "lote_id" not in df.columns:
        raise ValueError("Base_Referencia sem coluna lote_id.")

    lotes: set[str] = set()
    for valor in df["lote_id"].tolist():
        if valor is None or (isinstance(valor, float) and pd.isna(valor)):
            continue
        texto = str(valor).strip()
        if not texto or texto.lower() == "nan":
            continue
        # Ignora rodapé / avisos (ex.: linhas sem padrão de lote)
        if texto.upper().startswith("LG-"):
            lotes.add(texto)
    return lotes


def listar_abas_diarias(caminho: Path) -> list[str]:
    """Descobre abas Insp_DD_MM_2026 via regex (sem hardcode da lista)."""
    xl = pd.ExcelFile(caminho)
    abas = [nome for nome in xl.sheet_names if PADRAO_ABA_DIARIA.match(nome)]
    if not abas:
        raise ValueError("Nenhuma aba diária Insp_DD_MM_2026 encontrada.")
    return abas


def carregar_registros_dia(caminho: Path, nome_aba: str) -> list[dict]:
    """Lê uma aba diária: título=l1, metadados=l2, cabeçalho=l3, dados a partir da l4."""
    df = pd.read_excel(
        caminho,
        sheet_name=nome_aba,
        header=2,  # linha 3 do Excel
        dtype=str,
    )
    # Garante colunas esperadas
    for col in COLUNAS_DIARIAS:
        if col not in df.columns:
            df[col] = None

    registros: list[dict] = []
    for _, row in df.iterrows():
        bruto = {col: row.get(col) for col in COLUNAS_DIARIAS}
        # Descarta linhas totalmente vazias e o rodapé "Total de registros"
        valores = []
        for v in bruto.values():
            if v is None or (isinstance(v, float) and pd.isna(v)):
                valores.append("")
            else:
                valores.append(str(v).strip())
        if not any(valores):
            continue
        lote = valores[0]
        if lote.lower().startswith("total de registros"):
            continue
        registros.append(bruto)
    return registros


def processar(
    caminho_entrada: Path,
) -> tuple[list[RegistroValidado], dict[str, int]]:
    """Lê abas, deduplica por Counter por dia e valida cada linha."""
    lotes_ref = carregar_base_referencia(caminho_entrada)
    abas = listar_abas_diarias(caminho_entrada)

    validados: list[RegistroValidado] = []
    for aba in abas:
        data_ref = _data_referencia_da_aba(aba)
        registros = carregar_registros_dia(caminho_entrada, aba)

        # Contador de ocorrências do lote_id no DIA (antes de validar).
        # Lote vazio não entra na deduplicação: RN01 tem precedência sobre RN11.
        contagem: Counter[str] = Counter()
        ocorrencias: list[int] = []
        for reg in registros:
            if chave_nao_vazia(reg):
                chave = str(reg.get("lote_id")).strip()
                contagem[chave] += 1
                ocorrencias.append(contagem[chave])
            else:
                ocorrencias.append(1)

        for reg, ocorrencia in zip(registros, ocorrencias):
            resultado = validar_registro(
                reg,
                lotes_referencia=lotes_ref,
                data_referencia=data_ref,
                ocorrencia_no_dia=ocorrencia,
            )
            validados.append(resultado)

    return validados, _contar_por_regra(validados)


def chave_nao_vazia(reg: dict) -> bool:
    lote = reg.get("lote_id")
    if lote is None or (isinstance(lote, float) and pd.isna(lote)):
        return False
    return str(lote).strip() != ""


def _contar_por_regra(validados: list[RegistroValidado]) -> dict[str, int]:
    """Conta registros por código de regra (primeira regra quando há várias)."""
    contagem: Counter[str] = Counter()
    for r in validados:
        # Pode haver "RN01, RN02" em Erro de Entrada — conta cada código
        for parte in r.regra.split(","):
            codigo = parte.strip().split()[0] if parte.strip() else "—"
            # Para erros compostos, conta o registro inteiro só na classificação;
            # aqui contamos cada RN citada para diagnóstico.
            contagem[codigo] += 1
    return dict(sorted(contagem.items()))


def _contar_classificacoes(validados: list[RegistroValidado]) -> dict[str, int]:
    return {
        CLASSIFICACAO_VALIDO: sum(
            1 for r in validados if r.classificacao == CLASSIFICACAO_VALIDO
        ),
        CLASSIFICACAO_DIVERGENCIA: sum(
            1 for r in validados if r.classificacao == CLASSIFICACAO_DIVERGENCIA
        ),
        CLASSIFICACAO_AMBIGUO: sum(
            1 for r in validados if r.classificacao == CLASSIFICACAO_AMBIGUO
        ),
        CLASSIFICACAO_ERRO: sum(
            1 for r in validados if r.classificacao == CLASSIFICACAO_ERRO
        ),
    }


def _df_de(validados: list[RegistroValidado]) -> pd.DataFrame:
    if not validados:
        return pd.DataFrame()
    return pd.DataFrame([r.to_dict() for r in validados])


def _validar_soma_abas(totais: dict[str, int], total: int) -> None:
    """Aceite: soma das 4 classificações == total processado."""
    soma = (
        totais[CLASSIFICACAO_VALIDO]
        + totais[CLASSIFICACAO_DIVERGENCIA]
        + totais[CLASSIFICACAO_AMBIGUO]
        + totais[CLASSIFICACAO_ERRO]
    )
    if soma != total:
        raise RuntimeError(
            f"Inconsistência de classificação: "
            f"Válidos({totais[CLASSIFICACAO_VALIDO]}) + "
            f"Divergências({totais[CLASSIFICACAO_DIVERGENCIA]}) + "
            f"Ambíguos({totais[CLASSIFICACAO_AMBIGUO]}) + "
            f"Erros({totais[CLASSIFICACAO_ERRO]}) = {soma}, "
            f"mas o total processado é {total}."
        )


def _estilo_cabecalho(ws, ncols: int) -> None:
    fill = PatternFill("solid", fgColor="1F4E79")
    font = Font(color="FFFFFF", bold=True)
    for col in range(1, ncols + 1):
        cell = ws.cell(1, col)
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center", wrap_text=True)


def _escrever_dataframe(ws, df: pd.DataFrame) -> None:
    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=1):
        for c_idx, value in enumerate(row, start=1):
            ws.cell(r_idx, c_idx, value)
    if df.shape[1]:
        _estilo_cabecalho(ws, df.shape[1])
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col[:50]:
                if cell.value is not None:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = min(max(max_len + 2, 12), 40)


def _montar_resumo(
    wb: Workbook,
    totais: dict[str, int],
    total: int,
    validados: list[RegistroValidado],
) -> None:
    """Aba Resumo: indicadores + DoughnutChart + LineChart (nativos)."""
    ws = wb.create_sheet("Resumo", 0)

    titulo = Font(name="Calibri", size=16, bold=True, color="1F4E79")
    rotulo = Font(name="Calibri", size=11, bold=True)
    numero = Font(name="Calibri", size=14, bold=True)
    fino = Border(
        left=Side(style="thin", color="B0B0B0"),
        right=Side(style="thin", color="B0B0B0"),
        top=Side(style="thin", color="B0B0B0"),
        bottom=Side(style="thin", color="B0B0B0"),
    )

    ws["A1"] = "Conferência de Lotes — Dashboard"
    ws["A1"].font = titulo
    ws.merge_cells("A1:D1")

    ws["A2"] = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    ws["A2"].font = Font(name="Calibri", size=10, italic=True, color="666666")

    # --- Indicadores ---
    ws["A4"] = "Indicadores"
    ws["A4"].font = Font(name="Calibri", size=12, bold=True, color="1F4E79")

    headers = ["Classificação", "Quantidade", "Percentual"]
    for i, h in enumerate(headers, start=1):
        cell = ws.cell(5, i, h)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.border = fino

    ordem = [
        CLASSIFICACAO_VALIDO,
        CLASSIFICACAO_DIVERGENCIA,
        CLASSIFICACAO_AMBIGUO,
        CLASSIFICACAO_ERRO,
    ]
    cores_linhas = {
        CLASSIFICACAO_VALIDO: "C6EFCE",
        CLASSIFICACAO_DIVERGENCIA: "FFC7CE",
        CLASSIFICACAO_AMBIGUO: "FFEB9C",
        CLASSIFICACAO_ERRO: "D9D9D9",
    }

    for i, classe in enumerate(ordem):
        qtd = totais[classe]
        pct = (qtd / total * 100) if total else 0.0
        row = 6 + i
        ws.cell(row, 1, classe).border = fino
        ws.cell(row, 2, qtd).border = fino
        ws.cell(row, 2).font = numero
        ws.cell(row, 3, round(pct, 1) / 100).border = fino
        ws.cell(row, 3).number_format = "0.0%"
        fill = PatternFill("solid", fgColor=cores_linhas[classe])
        for c in range(1, 4):
            ws.cell(row, c).fill = fill

    ws.cell(10, 1, "Total de registros").font = rotulo
    ws.cell(10, 2, total).font = numero
    ws.cell(10, 1).border = fino
    ws.cell(10, 2).border = fino

    # --- Gráfico de rosca (dados em A5:B9) ---
    doughnut = DoughnutChart()
    doughnut.title = "Distribuição por classificação"
    labels = Reference(ws, min_col=1, min_row=6, max_row=9)
    data = Reference(ws, min_col=2, min_row=5, max_row=9)
    doughnut.add_data(data, titles_from_data=True)
    doughnut.set_categories(labels)
    doughnut.dataLabels = DataLabelList()
    doughnut.dataLabels.showPercent = True
    doughnut.dataLabels.showVal = False
    doughnut.dataLabels.showCatName = False
    doughnut.style = 10
    doughnut.width = 12
    doughnut.height = 8

    # Cores dos pontos da rosca
    series = doughnut.series[0]
    hex_cores = ["548235", "C00000", "BF8F00", "7F7F7F"]
    for idx, hex_cor in enumerate(hex_cores):
        pt = DataPoint(idx=idx)
        pt.graphicalProperties.solidFill = hex_cor
        series.data_points.append(pt)

    ws.add_chart(doughnut, "E4")

    # --- Tabela auxiliar temporal (alimenta o LineChart) ---
    ws["A13"] = "Evolução diária (tabela auxiliar do gráfico)"
    ws["A13"].font = Font(name="Calibri", size=12, bold=True, color="1F4E79")

    # Agrega por data_referencia
    por_dia: dict[str, Counter] = {}
    for r in validados:
        if r.data_referencia not in por_dia:
            por_dia[r.data_referencia] = Counter()
        por_dia[r.data_referencia][r.classificacao] += 1
        por_dia[r.data_referencia]["Total"] += 1

    def _chave_data(d: str) -> tuple[int, int, int]:
        partes = d.split("/")
        return (int(partes[2]), int(partes[1]), int(partes[0]))

    dias_ordenados = sorted(por_dia.keys(), key=_chave_data)

    ws["A14"] = "Data"
    ws["B14"] = "Total"
    ws["C14"] = "Divergências"
    ws["D14"] = "Ambíguos"
    ws["E14"] = "Divergências + Ambíguos"
    for col in range(1, 6):
        cell = ws.cell(14, col)
        cell.font = Font(color="FFFFFF", bold=True)
        cell.fill = PatternFill("solid", fgColor="1F4E79")
        cell.border = fino

    for i, dia in enumerate(dias_ordenados):
        row = 15 + i
        c = por_dia[dia]
        div = c[CLASSIFICACAO_DIVERGENCIA]
        amb = c[CLASSIFICACAO_AMBIGUO]
        ws.cell(row, 1, dia).border = fino
        ws.cell(row, 2, c["Total"]).border = fino
        ws.cell(row, 3, div).border = fino
        ws.cell(row, 4, amb).border = fino
        ws.cell(row, 5, div + amb).border = fino

    ultima_linha = 14 + len(dias_ordenados)

    linha = LineChart()
    linha.title = "Evolução dos registros (Divergências + Ambíguos)"
    linha.style = 10
    linha.y_axis.title = "Quantidade"
    linha.x_axis.title = "Dia"
    linha.width = 15
    linha.height = 8

    dados_linha = Reference(ws, min_col=5, min_row=14, max_row=ultima_linha)
    cats_linha = Reference(ws, min_col=1, min_row=15, max_row=ultima_linha)
    linha.add_data(dados_linha, titles_from_data=True)
    linha.set_categories(cats_linha)
    ws.add_chart(linha, "E18")

    # Larguras
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 14
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 12
    ws.column_dimensions["E"].width = 24


def gerar_excel(
    validados: list[RegistroValidado],
    totais: dict[str, int],
    caminho_saida: Path,
    linhas_log: list[str],
) -> None:
    """Gera o Excel com 6 abas obrigatórias + aba Log opcional."""
    total = len(validados)
    _validar_soma_abas(totais, total)

    df_todos = _df_de(validados)
    df_validos = _df_de([r for r in validados if r.classificacao == CLASSIFICACAO_VALIDO])
    df_div = _df_de(
        [r for r in validados if r.classificacao == CLASSIFICACAO_DIVERGENCIA]
    )
    df_amb = _df_de([r for r in validados if r.classificacao == CLASSIFICACAO_AMBIGUO])
    df_erro = _df_de([r for r in validados if r.classificacao == CLASSIFICACAO_ERRO])

    # Aceite extra: nenhuma aba mistura classificações
    for nome, df, esperada in (
        ("Válidos", df_validos, CLASSIFICACAO_VALIDO),
        ("Divergências", df_div, CLASSIFICACAO_DIVERGENCIA),
        ("Ambíguos", df_amb, CLASSIFICACAO_AMBIGUO),
        ("Erros de Entrada", df_erro, CLASSIFICACAO_ERRO),
    ):
        if not df.empty and set(df["Classificação"].unique()) - {esperada}:
            raise RuntimeError(f"Aba '{nome}' mistura classificações.")

    wb = Workbook()
    # remove sheet padrão; Resumo será criada em _montar_resumo
    padrao = wb.active
    wb.remove(padrao)

    _montar_resumo(wb, totais, total, validados)

    abas_dados = [
        ("Todos", df_todos),
        ("Válidos", df_validos),
        ("Divergências", df_div),
        ("Ambíguos", df_amb),
        ("Erros de Entrada", df_erro),
    ]
    for nome, df in abas_dados:
        ws = wb.create_sheet(nome)
        _escrever_dataframe(ws, df)

    # Aba Log (opcional, pedida no PASSO 6)
    ws_log = wb.create_sheet("Log")
    ws_log["A1"] = "Log de execução"
    ws_log["A1"].font = Font(bold=True, size=12, color="1F4E79")
    for i, linha in enumerate(linhas_log, start=3):
        ws_log.cell(i, 1, linha)
    ws_log.column_dimensions["A"].width = 100

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho_saida)


def gravar_log(
    caminho_log: Path,
    totais: dict[str, int],
    total: int,
    por_regra: dict[str, int],
) -> list[str]:
    """Grava log texto em logs/ e devolve as linhas para a aba Log."""
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linhas = [
        f"Data/hora da execução: {agora}",
        f"Total de registros processados: {total}",
        f"Válidos: {totais[CLASSIFICACAO_VALIDO]}",
        f"Divergências: {totais[CLASSIFICACAO_DIVERGENCIA]}",
        f"Ambíguos: {totais[CLASSIFICACAO_AMBIGUO]}",
        f"Erros de Entrada: {totais[CLASSIFICACAO_ERRO]}",
        (
            "Checagem de soma: "
            f"{totais[CLASSIFICACAO_VALIDO]}+"
            f"{totais[CLASSIFICACAO_DIVERGENCIA]}+"
            f"{totais[CLASSIFICACAO_AMBIGUO]}+"
            f"{totais[CLASSIFICACAO_ERRO]} = {total}"
        ),
        "Quebra por regra (códigos citados): "
        + ", ".join(f"{k}={v}" for k, v in por_regra.items()),
    ]
    caminho_log.parent.mkdir(parents=True, exist_ok=True)
    caminho_log.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return linhas


def main() -> int:
    entrada, saida, log_path = _carregar_caminhos()

    if not entrada.exists():
        print(f"ERRO: arquivo de entrada não encontrado: {entrada}", file=sys.stderr)
        print(
            "Defina INPUT_FILE no .env ou coloque a planilha no caminho padrão.",
            file=sys.stderr,
        )
        return 1

    print(f"Entrada: {entrada}")
    print(f"Saída:   {saida}")

    validados, por_regra = processar(entrada)
    totais = _contar_classificacoes(validados)
    total = len(validados)

    _validar_soma_abas(totais, total)

    # Quebra específica de Divergências por RN (RN05, RN10, RN11)
    div_por_rn = Counter()
    for r in validados:
        if r.classificacao == CLASSIFICACAO_DIVERGENCIA:
            div_por_rn[r.regra] += 1

    linhas_log = gravar_log(log_path, totais, total, por_regra)
    gerar_excel(validados, totais, saida, linhas_log)

    print("--- Resultado ---")
    print(f"Total processado: {total}")
    for k, v in totais.items():
        pct = (v / total * 100) if total else 0
        print(f"  {k}: {v} ({pct:.1f}%)")
    print(
        f"Soma abas filtradas: "
        f"{totais[CLASSIFICACAO_VALIDO]}+"
        f"{totais[CLASSIFICACAO_DIVERGENCIA]}+"
        f"{totais[CLASSIFICACAO_AMBIGUO]}+"
        f"{totais[CLASSIFICACAO_ERRO]} = {total}  OK"
    )
    print(f"Divergências por RN: {dict(div_por_rn)}")
    print(f"Log: {log_path}")
    print(f"Relatório: {saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
