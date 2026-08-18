from pathlib import Path
from types import SimpleNamespace
import pandas as pd
import pytest

from src.relatorio import (
    _divergencias_para_dataframe,
    gerar_relatorio_divergencias,
)


@pytest.fixture
def mock_resultado_com_divergencias():
    # Cria estrutura em conformidade com as classes ResultadoValidacao e Divergencia
    div1 = SimpleNamespace(
        regra="REGRA_01",
        mensagem="Divergência de código",
        valor_esperado="PROD_A",
        valor_encontrado="PROD_B",
    )
    div2 = SimpleNamespace(
        regra="REGRA_02",
        mensagem="Quantidade fora do limite",
        valor_esperado=100,
        valor_encontrado=50,
    )

    registro = SimpleNamespace(
        numero_lote="LOTE_100",
        codigo_produto="PROD_B",
    )

    resultado = SimpleNamespace(
        registro=registro,
        divergencias=[div1, div2],
    )
    return [resultado]


@pytest.fixture
def mock_resultado_sem_divergencias():
    registro = SimpleNamespace(
        numero_lote="LOTE_101",
        codigo_produto="PROD_OK",
    )
    return [SimpleNamespace(registro=registro, divergencias=[])]


# --- Testes Unitários ---


@pytest.mark.unit
def test_divergencias_para_dataframe(mock_resultado_com_divergencias):
    df = _divergencias_para_dataframe(mock_resultado_com_divergencias)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == [
        "numero_lote",
        "codigo_produto",
        "regra",
        "mensagem",
        "valor_esperado",
        "valor_encontrado",
    ]
    assert df.iloc[0]["numero_lote"] == "LOTE_100"
    assert df.iloc[0]["regra"] == "REGRA_01"


@pytest.mark.unit
def test_gerar_relatorio_divergencias_sucesso(
    mock_resultado_com_divergencias, tmp_path
):
    caminho_excel = tmp_path / "subpasta" / "relatorio_divergencias.xlsx"

    # Executa a geração do relatório
    resultado_path = gerar_relatorio_divergencias(
        mock_resultado_com_divergencias, caminho_excel
    )

    assert resultado_path.exists()
    assert resultado_path == caminho_excel

    # Lê o Excel gerado para confirmar o conteúdo salvo
    df_lido = pd.read_excel(caminho_excel, engine="openpyxl")
    assert len(df_lido) == 2
    assert df_lido.iloc[0]["numero_lote"] == "LOTE_100"


@pytest.mark.unit
def test_gerar_relatorio_divergencias_sem_resultados():
    with pytest.raises(
        ValueError, match="Nenhum resultado fornecido para geração do relatório."
    ):
        gerar_relatorio_divergencias([], Path("relatorio.xlsx"))


@pytest.mark.unit
def test_gerar_relatorio_divergencias_sem_nenhuma_divergencia(
    mock_resultado_sem_divergencias, tmp_path
):
    caminho_excel = tmp_path / "relatorio.xlsx"
    with pytest.raises(
        ValueError, match="Nenhuma divergência encontrada nos resultados."
    ):
        gerar_relatorio_divergencias(
            mock_resultado_sem_divergencias, caminho_excel
        )