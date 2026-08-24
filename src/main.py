"""
Fluxo principal: Maestro → DataPool → Validação + Automação Web por Item.

Observabilidade (doc oficial BotCity):
- Execution Log: https://documentation.botcity.dev/maestro/maestro-sdk/log/
- Alerts:        https://documentation.botcity.dev/maestro/maestro-sdk/alerts-and-messages/
- Result Files:  https://documentation.botcity.dev/maestro/maestro-sdk/result-files/
"""
from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse

from botcity.maestro import AutomationTaskFinishStatus, BotMaestroSDK

from src.artifacts import pasta_screenshots, publicar_resultados_execucao
from src.bot import process_item
from src.config import Config, RAIZ_PROJETO
from src.dispatcher import run_dispatcher
from src.maestro_observability import (
    emitir_alerta,
    garantir_execution_log,
    registrar_etapa,
)
from src.vault_client import get_erp_credentials

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
    maestro = BotMaestroSDK.from_sys_args()
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
            "MAESTRO_LOGIN vazio. Defina MAESTRO_LOGIN no .env para login local."
        )

    logger.info("Autenticando no Maestro (local): %s", config.maestro_server_url)
    maestro.login(
        server=config.maestro_server_url,
        login=login,
        key=config.maestro_api_key,
    )
    return maestro


def _consumir_fila(
    maestro: BotMaestroSDK,
    config: Config,
    log_label: str,
    web_page=None,
    fn_preencher=None,
) -> list[dict]:
    """Consome itens do DataPool, valida as regras e realiza a automação web por item."""
    resultados: list[dict] = []
    datapool = maestro.get_datapool(label=config.data_pool_name)

    task_id = getattr(maestro, "task_id", None)
    logger.info("Consumindo DataPool '%s'...", config.data_pool_name)
    registrar_etapa(
        maestro,
        log_label,
        etapa="DATAPOOL",
        status="INICIO",
        mensagem=f"Consumindo fila {config.data_pool_name}",
    )

    while datapool.has_next():
        entry = datapool.next(task_id=str(task_id) if task_id else None)
        if entry is None:
            break

        # 1. Validação em memória (Regras de Negócio)
        resultado = process_item(entry, config)
        lote = str(resultado.get("numero_lote", "-"))

        # 2. Interação Web e Screenshot (se aprovado na validação e Web habilitado)
        if resultado.get("aprovado") and config.web_automation_enabled and web_page and fn_preencher:
            try:
                res_web = fn_preencher(web_page, resultado.get("fields", {}), config)
                caminho_evidencia = res_web.get("screenshot", "")

                resultado["evidencia"] = caminho_evidencia
                resultado["web_sucesso"] = True

                if hasattr(entry, "set_value"):
                    entry.set_value("evidencia", caminho_evidencia)
                entry.report_done(finish_message="APROVADO E PREENCHIDO")

            except Exception as exc:
                logger.error("Erro na automação Web para o lote %s: %s", lote, exc)
                resultado["aprovado"] = False
                resultado["web_sucesso"] = False
                resultado["mensagem"] = f"Erro na interface Web: {exc}"

                entry.report_error(
                    error_type="SYSTEM",
                    finish_message=f"Falha na interface Web: {exc}",
                )
        else:
            if not resultado.get("aprovado"):
                entry.report_error(
                    error_type="BUSINESS",
                    finish_message=str(resultado.get("mensagem", "Reprovado na validação")),
                )
            else:
                entry.report_done(finish_message="APROVADO (SEM WEB)")

        resultados.append(resultado)

        ok = bool(resultado.get("aprovado"))
        registrar_etapa(
            maestro,
            log_label,
            etapa="PROCESSAMENTO_ITEM",
            status="OK" if ok else "NOK",
            lote=lote,
            mensagem=str(resultado.get("mensagem", ""))[:400],
        )

    logger.info("Itens processados na fila: %s", len(resultados))
    registrar_etapa(
        maestro,
        log_label,
        etapa="DATAPOOL",
        status="FIM",
        mensagem=f"Processados {len(resultados)} itens",
    )
    return resultados


def _aplicar_parametros_da_task(maestro: BotMaestroSDK) -> dict[str, str]:
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
    logger.info("Arquivo de configuração: %s", config.env_file)
    logger.info("DataPool: %s", config.data_pool_name)
    logger.info(
        "Planilha: %s (existe=%s)",
        config.caminho_planilha_entrada,
        config.caminho_planilha_entrada.exists(),
    )
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
        "Screenshots=%s | UploadArtifacts=%s | ExecutionLog=%s",
        config.screenshot_enabled,
        config.upload_artifacts,
        config.execution_log_label,
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

    if _aplicar_parametros_da_task(maestro):
        config = Config.carregar()
        _configurar_logging(config)

    _log_diagnostico(config)
    logger.info("=" * 60)

    log_label = config.execution_log_label
    if config.maestro_enabled:
        log_label = garantir_execution_log(maestro, log_label)
        registrar_etapa(
            maestro,
            log_label,
            etapa="INICIO",
            status="OK",
            mensagem="Bot iniciado",
            driver=config.web_automation_driver,
        )
        emitir_alerta(
            maestro,
            titulo="Conferência de Lotes — início",
            mensagem=(
                f"Driver={config.web_automation_driver} | "
                f"DataPool={config.data_pool_name} | "
                f"Web={config.web_automation_enabled}"
            ),
            tipo="INFO",
        )

    credenciais = {"login": config.web_usuario, "password": config.web_senha}

    if config.maestro_enabled and config.vault_enabled:
        try:
            credenciais = get_erp_credentials(maestro, config)
            registrar_etapa(
                maestro, log_label, etapa="VAULT", status="OK", mensagem="Credencial obtida"
            )
        except Exception as exc:
            logger.error("Falha ao obter Vault; usando WEB_USUARIO/WEB_SENHA. %s", exc)
            registrar_etapa(
                maestro,
                log_label,
                etapa="VAULT",
                status="WARN",
                mensagem=f"Fallback local: {exc}",
            )
            emitir_alerta(maestro, "Vault falhou", str(exc), tipo="WARN")

    # Dispatcher Opcional
    run_dispatcher_flag = os.getenv("RUN_DISPATCHER", "false").lower() == "true"
    if run_dispatcher_flag and config.maestro_enabled:
        try:
            enviados = run_dispatcher(maestro, config)
            logger.info("RUN_DISPATCHER=true — %s itens enfileirados.", enviados)
            registrar_etapa(
                maestro,
                log_label,
                etapa="DISPATCHER",
                status="OK",
                mensagem=f"{enviados} itens enfileirados",
            )
        except Exception as exc:
            logger.error("Falha no dispatcher: %s", exc)
            registrar_etapa(
                maestro, log_label, etapa="DISPATCHER", status="ERROR", mensagem=str(exc)
            )
            emitir_alerta(maestro, "Falha no dispatcher", str(exc), tipo="ERROR")
            _finalizar_task(maestro, sucesso=False, mensagem=str(exc))
            return 1

    resultados_processamento: list[dict] = []

    # Processamento do DataPool com Sessão Web Selecionada Dinamicamente
    if config.maestro_enabled:
        try:
            if config.web_automation_enabled:
                driver_tipo = config.web_automation_driver.lower()
                logger.info("Iniciando sessão do %s...", driver_tipo.capitalize())

                if driver_tipo == "selenium":
                    from src.web_automation_selenium import (
                        WebAutomationSessionSelenium as WebSession,
                        fazer_login,
                        preencher_lote,
                    )
                else:
                    from src.web_automation_playwright import (
                        WebAutomationSession as WebSession,
                        fazer_login,
                        preencher_lote,
                    )

                with WebSession(config) as web:
                    browser_ref = getattr(web, "page", None) or getattr(web, "driver", None)
                    fazer_login(browser_ref, credenciais["login"], credenciais["password"])
                    
                    resultados_processamento = _consumir_fila(
                        maestro,
                        config,
                        log_label,
                        web_page=browser_ref,
                        fn_preencher=preencher_lote,
                    )
            else:
                resultados_processamento = _consumir_fila(
                    maestro, config, log_label, web_page=None
                )
        except Exception as exc:
            logger.error("Falha ao processar DataPool: %s", exc, exc_info=True)
            registrar_etapa(
                maestro, log_label, etapa="DATAPOOL", status="ERROR", mensagem=str(exc)
            )
            emitir_alerta(maestro, "Falha no DataPool", str(exc), tipo="ERROR")
            _finalizar_task(maestro, sucesso=False, mensagem=str(exc))
            return 1
    else:
        logger.info("Maestro desligado — sem consumo de DataPool.")

    aprovados = sum(1 for r in resultados_processamento if r.get("aprovado"))
    reprovados = sum(1 for r in resultados_processamento if not r.get("aprovado"))
    web_sucessos = sum(1 for r in resultados_processamento if r.get("web_sucesso"))

    resumo = {
        "inicio": inicio.isoformat(),
        "fim": datetime.now(timezone.utc).isoformat(),
        "data_pool": config.data_pool_name,
        "planilha": str(config.caminho_planilha_entrada),
        "itens_processados": len(resultados_processamento),
        "aprovados": aprovados,
        "reprovados": reprovados,
        "web_automation_enabled": config.web_automation_enabled,
        "web_automation_driver": config.web_automation_driver,
        "web_sucessos": web_sucessos,
        "execution_log_label": log_label,
        "raiz_projeto": str(RAIZ_PROJETO),
    }
    caminho_resumo = _salvar_resumo(config, resumo)

    if config.maestro_enabled:
        publicados = publicar_resultados_execucao(
            maestro, config, caminho_resumo, resultados_processamento
        )
        resumo["result_files"] = publicados
        caminho_resumo.write_text(
            json.dumps(resumo, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        registrar_etapa(
            maestro,
            log_label,
            etapa="ARTIFACTS",
            status="OK",
            mensagem=(
                f"json={publicados.get('json', 0)} "
                f"log={publicados.get('log', 0)} "
                f"screenshots={publicados.get('screenshots', 0)}"
            ),
        )

        ok = reprovados == 0
        mensagem_fim = (
            f"Processados={len(resultados_processamento)} OK={aprovados} "
            f"NOK={reprovados} | Web Sucessos={web_sucessos}"
        )
        registrar_etapa(
            maestro,
            log_label,
            etapa="FIM",
            status="SUCCESS" if ok else "FAILED",
            mensagem=mensagem_fim,
            driver=config.web_automation_driver,
        )
        emitir_alerta(
            maestro,
            titulo="Conferência de Lotes — fim",
            mensagem=mensagem_fim,
            tipo="INFO" if ok else "WARN",
        )
        _finalizar_task(maestro, sucesso=ok, mensagem=mensagem_fim)

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