"""
Entry Point Principal para Execução do Pipeline Multi-Bot Híbrido Completo.
LG Electronics / AX Academy - Capstone de Hyperautomation (The DX Way).

Executa sequencialmente:
1. Setup de Telemetria e Auditoria
2. Subida/Verificação dos Mocks de Serviços (Web e ML)
3. Orquestração dos 5 Bots com prioridades e dependências:
   - Bot 01 (Desktop Collector com LockManager)
   - Bot 02 (Web Collector B2B)
   - Bot 03 (Consolidator RN01-RN04 com timeout e DLQ)
   - Bot 04 (ML Classifier com Isolamento e Fallback)
   - Bot 05 (Notifier Reporter com Auditoria CSV/XLSX e Alerta Multicanal)
"""

import argparse
import multiprocessing
import os
import sys
import time
import uuid
import uvicorn

# Configuração de encoding para ambientes Windows (evita erro cp1252 com emojis)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core.config import settings
from core.telemetry import setup_telemetry
from orchestration.orchestrator_engine import OrchestratorEngine, TaskPriority
from orchestration.dead_letter_queue import DeadLetterQueue
from bots import (
    DesktopCollectorBot,
    WebCollectorBot,
    ConsolidatorBot,
    MLClassifierBot,
    NotifierReporterBot,
)


def start_server_process(target_app: str, port: int):
    """Inicia um servidor FastAPI em subprocesso para o mock."""
    proc = multiprocessing.Process(
        target=uvicorn.run,
        args=(target_app,),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": "error"},
        daemon=True
    )
    proc.start()
    return proc


def run_pipeline(
    simulate_desktop_crash: bool = False,
    simulate_ml_offline: bool = False,
    web_latency: float = 0.0,
    force_invalid_telegram_token: bool = False,
    inject_corrupted_item: bool = False,
):
    execution_id = f"EXEC_{time.strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:4]}"
    logger = setup_telemetry(execution_id=execution_id)

    print("\n" + "=" * 80)
    print(f"[*] INICIANDO PIPELINE MULTI-BOT HIBRIDO -- EXECUCAO [{execution_id}]")
    print("=" * 80 + "\n")

    # 1. Iniciar Microserviços Mocks se necessário
    web_proc = start_server_process("mocks.web_portal.server:app", port=8001)
    ml_proc = start_server_process("mocks.ml_service.api:app", port=8002)
    time.sleep(1.2)  # Aquecimento dos servidores

    # Injeção de configurações de simulação nos mocks
    if web_latency > 0:
        import httpx
        httpx.post("http://127.0.0.1:8001/chaos/configure", json={"latency_seconds": web_latency, "force_error_500": False})

    if simulate_ml_offline:
        import httpx
        httpx.post("http://127.0.0.1:8002/chaos/toggle?offline=true")

    # 2. Inicialização do Orquestrador e DLQ
    orchestrator = OrchestratorEngine(execution_id=execution_id)
    dlq = DeadLetterQueue()

    # Instâncias dos Bots
    bot_01 = DesktopCollectorBot()
    bot_02 = WebCollectorBot()
    bot_03 = ConsolidatorBot(dlq=dlq)
    bot_04 = MLClassifierBot()
    bot_05 = NotifierReporterBot()

    # Registro de Tarefas no Orquestrador com Prioridades e Dependências
    orchestrator.register_task(
        bot_id=bot_01.bot_id,
        name="Coleta de Estoque Físico Legado (Desktop GUI)",
        handler=lambda: bot_01.run(simulate_crash=simulate_desktop_crash),
        priority=TaskPriority.HIGH,  # Sessão gráfica dedicada
        timeout_seconds=20.0
    )

    orchestrator.register_task(
        bot_id=bot_02.bot_id,
        name="Coleta de Pedidos de Fornecedores B2B (Web)",
        handler=lambda: bot_02.run(),
        priority=TaskPriority.MEDIUM,
        timeout_seconds=15.0
    )

    try:
        # EXECUÇÃO DO BOT 01 (Desktop)
        task_01 = orchestrator.execute_task_with_dependency_check(bot_01.bot_id)
        res_desktop = task_01.result or {"itens": []}

        # Se injetar item corrompido para o teste de Dead Letter (Cenário 6)
        if inject_corrupted_item and "itens" in res_desktop:
            res_desktop["itens"].append({
                "Cod_Item": "#CORRUPTED#_NaN",
                "Descricao": "Material com código corrompido de propósito",
                "Estoque_Fisico": 99,
                "Status": "ATIVO",
                "Observacao": "Simulação de dado irrecuperável para DLQ"
            })

        # EXECUÇÃO DO BOT 02 (Web)
        task_02 = orchestrator.execute_task_with_dependency_check(bot_02.bot_id)
        res_web = task_02.result or {"pedidos": []}

        # EXECUÇÃO DO BOT 03 (Consolidator com Verificação de Dependência e Timeout)
        dependency_timeout = (task_02.status.value == "TIMEOUT" or web_latency >= settings.DEPENDENCY_TIMEOUT_SECONDS)
        res_consolidator = bot_03.run(
            desktop_result=res_desktop,
            web_result=res_web,
            dependency_timeout_occurred=dependency_timeout
        )

        # EXECUÇÃO DO BOT 04 (ML Classifier com Enriquecimento Opcional)
        res_ml = bot_04.run(consolidator_result=res_consolidator)

        # EXECUÇÃO DO BOT 05 (Notifier & Reporter com Roteamento por Severidade)
        token_teste = "TOKEN_INVALIDO_SIMULADO" if force_invalid_telegram_token else None
        degraded = task_01.status.value == "DEGRADED" or dependency_timeout or simulate_ml_offline

        res_notifier = bot_05.run(
            itens_classificados=res_ml.get("itens", []),
            degraded_mode=degraded,
            dlq_count=res_consolidator.get("total_dlq", 0),
            forced_telegram_token=token_teste
        )

        print("\n" + "=" * 80)
        print("📊 RESUMO FINAL DA EXECUÇÃO DO PIPELINE:")
        print(f"  • Execution ID: {execution_id}")
        print(f"  • Itens Processados: {res_consolidator.get('total_processados', 0)}")
        print(f"  • Itens na Dead Letter Queue: {res_consolidator.get('total_dlq', 0)}")
        print(f"  • Modo Degradado Ativado: {degraded}")
        print(f"  • Severidade da Notificação: {res_notifier.get('severidade')}")
        print(f"  • Canal de Alerta Utilizado: {res_notifier.get('canal_notificacao_utilizado')}")
        print(f"  • Relatório CSV: {res_notifier.get('relatorio_csv')}")
        print(f"  • Relatório Excel: {res_notifier.get('relatorio_xlsx')}")
        print("=" * 80 + "\n")

    finally:
        # Finalização limpa dos servidores mocks em background
        web_proc.terminate()
        ml_proc.terminate()
        web_proc.join(timeout=1.0)
        ml_proc.join(timeout=1.0)


if __name__ == "__main__":
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="Pipeline Multi-Bot Híbrido (LG / AX Academy)")
    parser.add_argument("--crash-desktop", action="store_true", help="Simula crash do Bot Desktop")
    parser.add_argument("--ml-offline", action="store_true", help="Simula serviço de ML fora do ar")
    parser.add_argument("--web-latency", type=float, default=0.0, help="Injeta latência no portal web")
    parser.add_argument("--invalid-telegram", action="store_true", help="Força token inválido no Telegram")
    parser.add_argument("--corrupt-item", action="store_true", help="Injeta item corrompido para DLQ")
    args = parser.parse_args()

    run_pipeline(
        simulate_desktop_crash=args.crash_desktop,
        simulate_ml_offline=args.ml_offline,
        web_latency=args.web_latency,
        force_invalid_telegram_token=args.invalid_telegram,
        inject_corrupted_item=args.corrupt_item,
    )
