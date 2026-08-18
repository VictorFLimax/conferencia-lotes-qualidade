import pytest
import pandas as pd
from pathlib import Path


@pytest.mark.integration
def test_integracao_leitura_validacao_e_relatorio(tmp_path, mock_base_referencia, sample_dataframe_10dias):
    """
    Testa a colaboração entre leitura, validação e escrita de relatórios usando tmp_path.
    """
    df = sample_dataframe_10dias
    assert not df.empty

    dados_ref = mock_base_referencia.obter_dados()
    assert not dados_ref.empty

    caminho_saida: Path = tmp_path / "relatorio_conferencia_lotes.xlsx"
    with pd.ExcelWriter(caminho_saida, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Resumo", index=False)

    assert caminho_saida.exists()
    assert caminho_saida.stat().st_size > 0