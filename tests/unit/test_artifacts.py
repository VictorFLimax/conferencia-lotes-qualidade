from pathlib import Path
from unittest.mock import MagicMock
import pytest

from src.artifacts import (
    coletar_screenshots_resultados,
    pasta_screenshots,
    publicar_artefato,
    publicar_resultados_execucao,
    publicar_screenshots,
)


@pytest.fixture
def mock_config(tmp_path):
    """Cria uma estrutura de diretórios e uma configuração de teste."""
    config = MagicMock()
    log_file = tmp_path / "logs" / "execucao.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_file.touch()

    config.log_file = log_file
    config.upload_artifacts = True
    return config


@pytest.fixture
def mock_maestro():
    """Simula o BotMaestroSDK com task_id."""
    maestro = MagicMock()
    maestro.task_id = "12345"
    return maestro


# --- Testes Unitários ---


@pytest.mark.unit
def test_pasta_screenshots(mock_config):
    pasta = pasta_screenshots(mock_config)
    assert pasta.exists()
    assert pasta.is_dir()
    assert pasta.name == "screenshots"


@pytest.mark.unit
def test_publicar_artefato_arquivo_inexistente(mock_maestro):
    caminho_inexistente = Path("/caminho/falso/artefato.txt")
    resultado = publicar_artefato(mock_maestro, "12345", caminho_inexistente)

    assert resultado is False
    mock_maestro.post_artifact.assert_not_called()


@pytest.mark.unit
def test_publicar_artefato_sucesso(mock_maestro, tmp_path):
    arquivo = tmp_path / "relatorio.txt"
    arquivo.write_text("conteudo do relatorio")

    resultado = publicar_artefato(mock_maestro, "12345", arquivo, "meu_relatorio.txt")

    assert resultado is True
    mock_maestro.post_artifact.assert_called_once_with(
        task_id="12345",
        artifact_name="meu_relatorio.txt",
        filepath=str(arquivo.resolve()),
    )


@pytest.mark.unit
def test_publicar_artefato_usa_nome_padrao_se_nao_fornecido(mock_maestro, tmp_path):
    arquivo = tmp_path / "teste.png"
    arquivo.touch()

    resultado = publicar_artefato(mock_maestro, "12345", arquivo)

    assert resultado is True
    mock_maestro.post_artifact.assert_called_once_with(
        task_id="12345",
        artifact_name="teste.png",
        filepath=str(arquivo.resolve()),
    )


@pytest.mark.unit
def test_publicar_artefato_excecao(mock_maestro, tmp_path):
    arquivo = tmp_path / "erro.txt"
    arquivo.touch()

    mock_maestro.post_artifact.side_effect = Exception("Erro de conexao")

    resultado = publicar_artefato(mock_maestro, "12345", arquivo)

    assert resultado is False


@pytest.mark.unit
def test_publicar_screenshots_upload_desativado(mock_maestro, mock_config):
    mock_config.upload_artifacts = False
    enviados = publicar_screenshots(mock_maestro, "12345", ["/tmp/print.png"], mock_config)

    assert enviados == 0


@pytest.mark.unit
def test_publicar_screenshots_sem_task_id(mock_maestro, mock_config):
    enviados = publicar_screenshots(mock_maestro, None, ["/tmp/print.png"], mock_config)

    assert enviados == 0


@pytest.mark.unit
def test_publicar_screenshots_sucesso(mock_maestro, mock_config, tmp_path):
    img1 = tmp_path / "print1.png"
    img2 = tmp_path / "print2.png"
    img1.touch()
    img2.touch()

    enviados = publicar_screenshots(
        mock_maestro, "12345", [img1, img2, "/inexistente.png"], mock_config
    )

    assert enviados == 2


@pytest.mark.unit
def test_coletar_screenshots_resultados():
    resultados_web = [
        {"status": "ok", "screenshot": "/path/to/shot1.png"},
        {"status": "erro"},  # Sem chave "screenshot"
        {"status": "ok", "screenshot": "/path/to/shot2.png"},
    ]

    shots = coletar_screenshots_resultados(resultados_web)

    assert len(shots) == 2
    assert shots[0] == Path("/path/to/shot1.png")
    assert shots[1] == Path("/path/to/shot2.png")


@pytest.mark.unit
def test_publicar_resultados_execucao_upload_desativado(mock_maestro, mock_config, tmp_path):
    mock_config.upload_artifacts = False
    resumo = tmp_path / "resumo.json"

    resultado = publicar_resultados_execucao(mock_maestro, mock_config, resumo, [])

    assert resultado == {"json": 0, "log": 0, "screenshots": 0}


@pytest.mark.unit
def test_publicar_resultados_execucao_sem_task_id(mock_config, tmp_path):
    maestro_sem_task = MagicMock()
    del maestro_sem_task.task_id  # Garante que getattr retorne None
    resumo = tmp_path / "resumo.json"

    resultado = publicar_resultados_execucao(maestro_sem_task, mock_config, resumo, [])

    assert resultado == {"json": 0, "log": 0, "screenshots": 0}


@pytest.mark.unit
def test_publicar_resultados_execucao_sucesso_completo(mock_maestro, mock_config, tmp_path):
    # Prepara os arquivos
    resumo_json = tmp_path / "resumo.json"
    resumo_json.touch()

    pasta_print = pasta_screenshots(mock_config)
    png_da_pasta = pasta_print / "extra.png"
    png_da_pasta.touch()

    png_do_resultado = tmp_path / "resultado.png"
    png_do_resultado.touch()

    resultados_web = [{"screenshot": str(png_do_resultado)}]

    # Executa
    resultado = publicar_resultados_execucao(
        mock_maestro, mock_config, resumo_json, resultados_web
    )

    assert resultado["json"] == 1
    assert resultado["log"] == 1
    assert resultado["screenshots"] == 2  # png_do_resultado + png_da_pasta