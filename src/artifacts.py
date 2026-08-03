"""Publicação de Result Files (Artifacts) no BotCity Maestro.

Documentação:
https://documentation.botcity.dev/maestro/maestro-sdk/result-files/
https://documentation.botcity.dev/maestro/features/result-files/
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


def publicar_resultados_execucao(
    maestro: BotMaestroSDK,
    config: Config,
    caminho_resumo: Path,
    resultados_web: list[dict],
) -> dict[str, int]:
    """
    Publica no Maestro tudo o que permite acompanhar a execução:
    - resumo JSON
    - log de execução (arquivo)
    - screenshots PNG

    Visível em: Orchestrator → Result Files / aba Result Files da task.
    """
    task_id = getattr(maestro, "task_id", None)
    if not config.upload_artifacts:
        logger.info("UPLOAD_ARTIFACTS=false — nenhum Result File será enviado.")
        return {"json": 0, "log": 0, "screenshots": 0}

    if not task_id:
        logger.info(
            "Sem task_id — Result Files ficam só locais em %s",
            config.log_file.parent,
        )
        return {"json": 0, "log": 0, "screenshots": 0}

    json_ok = (
        1
        if publicar_artefato(
            maestro, task_id, caminho_resumo, artifact_name="resumo_execucao.json"
        )
        else 0
    )

    log_ok = 0
    if config.log_file.exists():
        log_ok = (
            1
            if publicar_artefato(
                maestro,
                task_id,
                config.log_file,
                artifact_name="execucao.log",
            )
            else 0
        )

    snaps = coletar_screenshots_resultados(resultados_web)
    pasta = pasta_screenshots(config)
    for png in sorted(pasta.glob("*.png")):
        if png not in snaps:
            snaps.append(png)

    shots = publicar_screenshots(maestro, task_id, snaps, config)
    return {"json": json_ok, "log": log_ok, "screenshots": shots}
