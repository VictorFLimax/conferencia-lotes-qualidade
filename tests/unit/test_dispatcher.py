from pathlib import Path
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from src.dispatcher import executar_cli, run_dispatcher


# FIX 1: Usando tmp_path para criar um arquivo real que o .exists() valide
@pytest.mark.unit
@patch("src.dispatcher.pd.read_excel")
def test_run_dispatcher_success(mock_read_excel, tmp_path):
  mock_read_excel.return_value = pd.DataFrame({"col1": [1, 2]})

  # Cria um arquivo temporário real para o test passar pelo .exists()
  fake_file = tmp_path / "planilha_fake.xlsx"
  fake_file.touch()

  mock_sdk = MagicMock()
  mock_config = MagicMock()
  mock_config.caminho_planilha_entrada = fake_file

  mock_item = MagicMock()
  mock_item.k_lote = "LOTE123"
  mock_sdk.get_execution.return_value.parameters = {"param1": "val1"}
  mock_sdk.get_next_task.side_effect = [mock_item, None]

  # Executa sem dar erro de atributo nem de FileNotFoundError
  run_dispatcher(mock_sdk, mock_config)


@pytest.mark.unit
@patch("src.dispatcher.BotMaestroSDK")
@patch("src.dispatcher.Config.carregar")
@patch("src.dispatcher.run_dispatcher")
def test_main_block(mock_run_dispatcher, mock_carregar_config, mock_sdk_class):
    mock_cfg = MagicMock()
    mock_cfg.caminho_planilha_entrada = Path("planilha_fake.xlsx")
    mock_cfg.maestro_server_url = "http://localhost"
    mock_cfg.maestro_login = "usuario"
    mock_cfg.maestro_api_key = "chave"
    mock_carregar_config.return_value = mock_cfg

    mock_sdk_instance = MagicMock()
    mock_sdk_class.return_value = mock_sdk_instance

    assert executar_cli() == 0

    mock_carregar_config.assert_called_once()
    mock_run_dispatcher.assert_called_once_with(mock_sdk_instance, mock_cfg)