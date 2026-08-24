from unittest.mock import MagicMock
import pytest

from src.base_referencia import BaseReferencia


@pytest.fixture
def mock_config_sem_arquivo():
    """Configuração onde caminho_base_referencia é None (usa dados em memória)."""
    config = MagicMock()
    config.caminho_base_referencia = None
    return config


@pytest.fixture
def mock_config_com_arquivo():
    """Configuração onde caminho_base_referencia está definido."""
    config = MagicMock()
    config.caminho_base_referencia = "caminho/para/base.xlsx"
    return config


# --- Testes Unitários ---


@pytest.mark.unit
def test_buscar_lote_existente_mock(mock_config_sem_arquivo):
    base = BaseReferencia(mock_config_sem_arquivo)
    lote = base.buscar_lote("LOTE-001")

    assert lote is not None
    assert lote["numero_lote"] == "LOTE-001"
    assert lote["codigo_produto"] == "PROD-A"
    assert lote["quantidade"] == 100.0


@pytest.mark.unit
def test_buscar_lote_inexistente_mock(mock_config_sem_arquivo):
    base = BaseReferencia(mock_config_sem_arquivo)
    lote = base.buscar_lote("LOTE-INEXISTENTE")

    assert lote is None


@pytest.mark.unit
def test_buscar_lote_em_arquivo_lança_not_implemented(mock_config_com_arquivo):
    base = BaseReferencia(mock_config_com_arquivo)

    with pytest.raises(
        NotImplementedError,
        match="Consulta à base de referência via arquivo ainda não implementada.",
    ):
        base.buscar_lote("LOTE-001")


@pytest.mark.unit
def test_listar_lotes(mock_config_sem_arquivo):
    base = BaseReferencia(mock_config_sem_arquivo)
    lotes = base.listar_lotes()

    assert isinstance(lotes, list)
    assert len(lotes) == 2
    assert lotes[0]["numero_lote"] == "LOTE-001"
    assert lotes[1]["numero_lote"] == "LOTE-002"