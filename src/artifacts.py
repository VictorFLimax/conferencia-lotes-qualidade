"""Publicação de Result Files (Artifacts) no BotCity Maestro.

Documentação:
https://documentation.botcity.dev/maestro/maestro-sdk/result-files/
"""
from __future__ import annotations

import logging
from pathlib import Path

from botcity.maestro import BotMaestroSDK

from src.config import Config

logger = logging.getLogger(__name__)


def pasta_screenshots(config: Config) -> Path:
    pasta = config.log_file.parent / "screenshots"
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def publicar_artefato(
    maestro: BotMaestroSDK,
    task_id: str | int,
    caminho: Path,
    artifact_name: str | None = None,
) -> bool:
    """
    Envia um arquivo para Result Files do Maestro.

    maestro.post_artifact(task_id=..., artifact_name=..., filepath=...)
    """
    if not caminho.exists():
        logger.warning("Arquivo não encontrado para artefato: %s", caminho)
        return False

    nome = artifact_name or caminho.name
    try:
        maestro.post_artifact(
            task_id=task_id,
            artifact_name=nome,
            filepath=str(caminho.resolve()),
        )
        logger.info("Result File enviado: %s (task_id=%s)", nome, task_id)
        return True
    except Exception as exc:
        logger.warning("Falha ao enviar Result File '%s': %s", nome, exc)
        return False


def publicar_screenshots(
    maestro: BotMaestroSDK,
    task_id: str | int | None,
    caminhos: list[Path | str],
    config: Config,
) -> int:
    """Publica screenshots como Result Files. Retorna quantidade enviada."""
    if not config.upload_artifacts:
        logger.info("UPLOAD_ARTIFACTS=false — screenshots não serão enviados ao Maestro.")
        return 0

    if not task_id:
        logger.info(
            "Sem task_id (execução local) — screenshots ficam só em disco: %s",
            pasta_screenshots(config),
        )
        return 0

    enviados = 0
    for raw in caminhos:
        caminho = Path(raw)
        if not caminho.exists():
            continue
        if publicar_artefato(maestro, task_id, caminho):
            enviados += 1
    logger.info("Screenshots enviados ao Maestro: %s/%s", enviados, len(caminhos))
    return enviados


def coletar_screenshots_resultados(resultados_web: list[dict]) -> list[Path]:
    """Extrai caminhos de screenshot dos resultados da automação web."""
    paths: list[Path] = []
    for item in resultados_web:
        snap = item.get("screenshot")
        if snap:
            paths.append(Path(snap))
    return paths
