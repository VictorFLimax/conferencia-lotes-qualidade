"""Fluxo principal: Maestro → DataPool → validação → automação web opcional."""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK

from src.artifacts import (
    coletar_screenshots_resultados,
    pasta_screenshots,
    publicar_artefato,
    publicar_screenshots,
)
from src.bot import process_item
from src.config import Config, RAIZ_PROJETO
from src.dispatcher import run_dispatcher
from src.vault_client import get_erp_credentials
from src.web import executar_automacao_web

logger = logging.getLogger(__name__)


def _configurar_logging(config: Config) -> None:
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(config.log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def _conectar_maestro(config: Config) -> BotMaestroSDK:
    """
    Conecta ao Maestro.

    No Runner: usa argumentos do BotCity (from_sys_args).
    Local: faz login com MAESTRO_SERVER_URL + MAESTRO_LOGIN + MAESTRO_API_KEY.
    """
    maestro = BotMaestroSDK.from_sys_args()
    # Evita crash quando roda local sem parâmetros do Runner
    maestro.RAISE_NOT_CONNECTED = False

    if not config.maestro_enabled:
        logger.info("MAESTRO_ENABLED=false — execução sem orquestração.")
        return maestro

    ja_conectado = bool(getattr(maestro, "access_token", None))
    if ja_conectado:
        logger.info("Maestro autenticado via Runner (from_sys_args).")
        return maestro

    if not config.maestro_api_key:
        raise RuntimeError(
            "MAESTRO_API_KEY não definido no .env e não há autenticação do Runner."
        )

    login = config.maestro_login
    if not login:
        logger.warning(
            "MAESTRO_LOGIN vazio. Defina MAESTRO_LOGIN no .env "
            "(Developer Environment do Maestro) para login local."
        )

    logger.info("Autenticando no Maestro (local): %s", config.maestro_server_url)
    maestro.login(
        server=config.maestro_server_url,
        login=login,
        key=config.maestro_api_key,
    )
    return maestro


def _consumir_fila(maestro: BotMaestroSDK, config: Config) -> list[dict]:
    """Consome itens do DataPool e valida cada um."""
    resultados: list[dict] = []
    datapool = maestro.get_datapool(label=config.data_pool_name)

    task_id = getattr(maestro, "task_id", None)
    logger.info("Consumindo DataPool '%s'...", config.data_pool_name)

    while datapool.has_next():
        entry = datapool.next(task_id=str(task_id) if task_id else None)
        if entry is None:
            break
        resultados.append(process_item(entry, config))

    logger.info("Itens processados na fila: %s", len(resultados))
    return resultados


def _aplicar_parametros_da_task(maestro: BotMaestroSDK) -> dict[str, str]:
    """
    Lê os parâmetros da task no Orchestrator e aplica como variáveis de ambiente.

    Permite configurar o bot pelo Maestro, sem depender de um .env no Runner.
    https://documentation.botcity.dev/maestro/maestro-sdk/setup/
    """
    task_id = getattr(maestro, "task_id", None)
    if not task_id:
        return {}

    try:
        task = maestro.get_task(task_id)
        parametros = dict(getattr(task, "parameters", None) or {})
    except Exception as exc:
        logger.warning("Não foi possível ler parâmetros da task: %s", exc)
        return {}

    aplicados: dict[str, str] = {}
    for chave, valor in parametros.items():
        if valor is None:
            continue
        os.environ[str(chave).strip()] = str(valor)
        aplicados[str(chave).strip()] = str(valor)

    if aplicados:
        logger.info("Parâmetros da task aplicados: %s", sorted(aplicados))
    return aplicados


def _log_diagnostico(config: Config) -> None:
    """Registra a configuração efetiva (aparece no Execution Log do Maestro)."""
    logger.info("Arquivo de configuração: %s", config.env_file)
    logger.info("DataPool: %s", config.data_pool_name)
    logger.info("Planilha: %s (existe=%s)",
                config.caminho_planilha_entrada,
                config.caminho_planilha_entrada.exists())
    logger.info(
        "Web: habilitado=%s driver=%s url=%s",
        config.web_automation_enabled,
        config.web_automation_driver,
        config.web_automation_url,
    )

    if config.web_automation_url.startswith("file://"):
        caminho_html = Path(unquote(urlparse(config.web_automation_url).path).lstrip("/"))
        logger.info("HTML local: %s (existe=%s)", caminho_html, caminho_html.exists())

    logger.info(
        "Screenshots=%s | UploadArtifacts=%s",
        config.screenshot_enabled,
        config.upload_artifacts,
    )


def _salvar_resumo(config: Config, resumo: dict) -> Path:
    pasta = config.log_file.parent
    pasta.mkdir(parents=True, exist_ok=True)
    caminho = pasta / "resumo_execucao.json"
    caminho.write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("Resumo salvo em %s", caminho)
    return caminho


def main() -> int:
    config = Config.carregar()
    _configurar_logging(config)

    inicio = datetime.now(timezone.utc)
    logger.info("=" * 60)
    logger.info("INÍCIO — Conferência de Lotes")

    maestro = _conectar_maestro(config)

    # Parâmetros da task sobrepõem o .env/.env.botcity
    if _aplicar_parametros_da_task(maestro):
        config = Config.carregar()
        _configurar_logging(config)

    _log_diagnostico(config)
    logger.info("=" * 60)

    credenciais = {"login": config.web_usuario, "password": config.web_senha}

    if config.maestro_enabled and config.vault_enabled:
        try:
            credenciais = get_erp_credentials(maestro, config)
        except Exception as exc:
            logger.error("Falha ao obter Vault; usando WEB_USUARIO/WEB_SENHA. %s", exc)

    # Opcional: popular a fila a partir da planilha
    run_dispatcher_flag = os.getenv("RUN_DISPATCHER", "false").lower() == "true"
    if run_dispatcher_flag and config.maestro_enabled:
        try:
            enviados = run_dispatcher(maestro, config)
            logger.info("RUN_DISPATCHER=true — %s itens enfileirados.", enviados)
        except Exception as exc:
            logger.error("Falha no dispatcher: %s", exc)
            return 1

    resultados_validacao: list[dict] = []
    if config.maestro_enabled:
        try:
            resultados_validacao = _consumir_fila(maestro, config)
        except Exception as exc:
            logger.error("Falha ao consumir DataPool: %s", exc, exc_info=True)
            _finalizar_task(maestro, sucesso=False, mensagem=str(exc))
            return 1
    else:
        logger.info("Maestro desligado — sem consumo de DataPool.")

    # Automação web nos itens aprovados (ou em todos os fields processados)
    resultados_web: list[dict] = []
    if config.web_automation_enabled:
        lotes_web = [
            r["fields"]
            for r in resultados_validacao
            if r.get("aprovado") and r.get("fields")
        ]
        # Se a fila estava vazia, permite teste web com um lote de exemplo
        if not lotes_web and not resultados_validacao:
            logger.info(
                "Fila vazia — executando automação web com lote de demonstração."
            )
            lotes_web = [
                {
                    "numero_lote": "LOTE-DEMO-001",
                    "produto_id": "1",
                    "status": "concluido",
                }
            ]
        try:
            resultados_web = executar_automacao_web(
                lotes_web,
                config,
                usuario=credenciais["login"],
                senha=credenciais["password"],
            )
        except Exception as exc:
            logger.error("Falha na automação web: %s", exc, exc_info=True)
            _finalizar_task(maestro, sucesso=False, mensagem=f"Web: {exc}")
            return 1

    aprovados = sum(1 for r in resultados_validacao if r.get("aprovado"))
    reprovados = sum(1 for r in resultados_validacao if not r.get("aprovado"))
    web_ok = sum(1 for r in resultados_web if r.get("sucesso"))

    resumo = {
        "inicio": inicio.isoformat(),
        "fim": datetime.now(timezone.utc).isoformat(),
        "data_pool": config.data_pool_name,
        "planilha": str(config.caminho_planilha_entrada),
        "itens_validados": len(resultados_validacao),
        "aprovados": aprovados,
        "reprovados": reprovados,
        "web_automation_enabled": config.web_automation_enabled,
        "web_automation_driver": config.web_automation_driver,
        "web_sucessos": web_ok,
        "web_total": len(resultados_web),
        "raiz_projeto": str(RAIZ_PROJETO),
    }
    caminho_resumo = _salvar_resumo(config, resumo)

    if config.maestro_enabled:
        task_id = getattr(maestro, "task_id", None)

        # Result Files: resumo JSON + screenshots
        # https://documentation.botcity.dev/maestro/maestro-sdk/result-files/
        if config.upload_artifacts and task_id:
            publicar_artefato(
                maestro,
                task_id,
                caminho_resumo,
                artifact_name="resumo_execucao.json",
            )

            snaps = coletar_screenshots_resultados(resultados_web)
            # Inclui screenshots de login e demais PNGs da pasta
            pasta = pasta_screenshots(config)
            for png in pasta.glob("*.png"):
                if png not in snaps:
                    snaps.append(png)
            enviados = publicar_screenshots(maestro, task_id, snaps, config)
            resumo["screenshots_enviados"] = enviados
            caminho_resumo.write_text(
                json.dumps(resumo, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        elif config.screenshot_enabled:
            logger.info(
                "Screenshots locais em: %s (envie com UPLOAD_ARTIFACTS=true e task no Runner)",
                pasta_screenshots(config),
            )

        ok = reprovados == 0 and (
            not config.web_automation_enabled or web_ok == len(resultados_web)
        )
        _finalizar_task(
            maestro,
            sucesso=ok,
            mensagem=(
                f"Validados={len(resultados_validacao)} OK={aprovados} "
                f"NOK={reprovados} | Web driver={config.web_automation_driver} "
                f"sucessos={web_ok}/{len(resultados_web)}"
            ),
        )

    logger.info("FIM — resumo: %s", resumo)
    return 0


def _finalizar_task(maestro: BotMaestroSDK, sucesso: bool, mensagem: str) -> None:
    task_id = getattr(maestro, "task_id", None)
    if not task_id:
        logger.info("Sem task_id (execução local) — finish_task ignorado.")
        return
    status = (
        AutomationTaskFinishStatus.SUCCESS
        if sucesso
        else AutomationTaskFinishStatus.FAILED
    )
    try:
        maestro.finish_task(task_id=task_id, status=status, message=mensagem[:255])
        logger.info("Task %s finalizada: %s", task_id, status)
    except Exception as exc:
        logger.warning("Falha ao finalizar task: %s", exc)


if __name__ == "__main__":
    raise SystemExit(main())
