import pytest
import pandas as pd
from unittest.mock import MagicMock
from src.validacao import (
    valida_estrutura,
    valida_campos_obrigatorios,
    CamposObrigatoriosVaziosError,
    registro_de_linha,
    ConferenciaLotes,
    RegistroLote,
    rn01_lote_existe,
    rn02_produto_corresponde,
    rn03_quantidade_valida,
    rn05_status_permitido,
    _valor_vazio,
)


@pytest.mark.unit
def test_valor_vazio_auxiliar():
    """Valida a lógica interna de identificação de valores vazios."""
    assert _valor_vazio(None) is True
    assert _valor_vazio("") is True
    assert _valor_vazio("   ") is True
    assert _valor_vazio(float("nan")) is True
    assert _valor_vazio("Texto Valido") is False


@pytest.mark.unit
def test_valida_estrutura_dataframe():
    """Testa validação de estrutura completa e incompleta."""
    df_valido = pd.DataFrame(
        columns=["lote_id", "produto", "linha", "turno", "status", "responsavel"]
    )
    resultado = valida_estrutura(df_valido)
    assert resultado.estrutura_completa is True
    assert len(resultado.colunas_ausentes) == 0

    df_invalido = pd.DataFrame(columns=["lote_id", "produto"])
    resultado_inv = valida_estrutura(df_invalido)
    assert resultado_inv.estrutura_completa is False
    assert "linha" in resultado_inv.colunas_ausentes


@pytest.mark.unit
def test_valida_campos_obrigatorios_sucesso_e_erro():
    """Testa exceção CamposObrigatoriosVaziosError quando há campos faltantes."""
    dados_ok = {
        "lote_id": "L1",
        "produto": "P1",
        "linha": "L1",
        "turno": "T1",
        "status": "APROVADO",
        "responsavel": "User",
    }
    # Nao deve lançar exceção
    valida_campos_obrigatorios(dados_ok)

    dados_incompletos = dados_ok.copy()
    dados_incompletos["status"] = ""

    with pytest.raises(CamposObrigatoriosVaziosError) as exc_info:
        valida_campos_obrigatorios(dados_incompletos)

    assert "status" in exc_info.value.campos_vazios


@pytest.mark.unit
def test_registro_de_linha_conversao():
    """Testa conversão de dicionário e Pandas Series para RegistroLote."""
    dict_dados = {
        "numero_lote": "LOTE123",
        "codigo_produto": "PROD01",
        "quantidade": 150.0,
        "data_fabricacao": "2026-01-01",
        "data_validade": "2026-12-31",
        "status": "APROVADO",
    }
    reg = registro_de_linha(dict_dados)
    assert reg.numero_lote == "LOTE123"
    assert reg.quantidade == 150.0
    assert reg.dados_extras["origem"] == "datapool"

    series_dados = pd.Series(dict_dados)
    reg_series = registro_de_linha(series_dados)
    assert reg_series.dados_extras["origem"] == "pandas"


@pytest.mark.unit
def test_regras_negocio_individuais():
    """Testa regras individuais de lote, produto, quantidade e status."""
    reg = RegistroLote(
        numero_lote="L1",
        codigo_produto="P1",
        quantidade=10,
        data_fabricacao="",
        data_validade="",
        status="INVALIDO",
    )

    # RN01: Lote inexistente na base
    assert len(rn01_lote_existe(reg, None)) == 1

    # RN02: Divergência de produto
    ref = {"codigo_produto": "P2", "quantidade": 10}
    assert len(rn02_produto_corresponde(reg, ref)) == 1

    # RN03: Divergência de quantidade
    assert len(rn03_quantidade_valida(reg, ref)) == 0  # quantidade confere

    # RN05: Status não permitido
    assert len(rn05_status_permitido(reg, None)) == 1


@pytest.mark.unit
def test_conferencia_lotes_fluxo_completo():
    """Testa orquestrador ConferenciaLotes com mock da base de referência."""
    mock_base = MagicMock()
    mock_base.buscar_lote.return_value = {"codigo_produto": "PROD01", "quantidade": 100.0}

    conferencia = ConferenciaLotes(mock_base)

    reg_valido = RegistroLote(
        numero_lote="LOTE001",
        codigo_produto="PROD01",
        quantidade=100.0,
        data_fabricacao="2026-01-01",
        data_validade="2026-12-31",
        status="APROVADO",
    )

    resultado = conferencia.validar_registro(reg_valido)
    assert resultado.aprovado is True
    assert len(resultado.divergencias) == 0