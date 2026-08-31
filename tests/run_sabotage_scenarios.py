"""
Suite de Demonstração e Testes de Resiliência sob Sabotagem ao Vivo.
LG Electronics / AX Academy - Capstone de Hyperautomation (The DX Way).

Executa e comprova os 6 Cenários de Sabotagem exigidos pela Banca Avaliadora:
1. Bot Desktop Indisponível (Crash da GUI -> Retry -> Fallback Degradado -> Sem quebra)
2. Timeout de Dependência (Atraso Web além do deadline -> Processamento de contingência)
3. Serviço de ML Fora do Ar (Serviço offline -> Fallback determinístico auditável)
4. Falha no Canal Principal (Telegram inválido -> Roteamento para Email/Contingência)
5. Coexistência de Runners (Disparo simultâneo -> LockManager previne colisão gráfica)
6. Item com Dado Irrecuperável (Item corrompido/NaN -> Isolamento seguro na DLQ)
"""

import os
import sys
import time
import subprocess
import multiprocessing
from pathlib import Path

# Adiciona diretório raiz ao sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Configuração de encoding Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn
from core.config import settings
from core.lock_manager import LockManager
from core.exceptions import RunnerLockAcquisitionError
from orchestration.dead_letter_queue import DeadLetterQueue
from bots import (
    DesktopCollectorBot,
    WebCollectorBot,
    ConsolidatorBot,
    MLClassifierBot,
    NotifierReporterBot,
)


def print_scenario_header(num: int, title: str, description: str):
    print("\n" + "=" * 80)
    print(f"🔥 CENARIO {num}: {title.upper()}")
    print(f"Descricao: {description}")
    print("=" * 80)


def start_server_process(target_app: str, port: int):
    proc = multiprocessing.Process(
        target=uvicorn.run,
        args=(target_app,),
        kwargs={"host": "127.0.0.1", "port": port, "log_level": "error"},
        daemon=True
    )
    proc.start()
    return proc


def run_all_sabotage_scenarios():
    print("\n" + "#" * 80)
    print("      SUITE DE VALIDACAO DOS 6 CENARIOS DE SABOTAGEM AO VIVO (BANCA LG)      ")
    print("#" * 80)

    # Inicia servidores mock
    web_proc = start_server_process("mocks.web_portal.server:app", port=8001)
    ml_proc = start_server_process("mocks.ml_service.api:app", port=8002)
    time.sleep(1.2)

    results_summary = {}

    try:
        # ====================================================================
        # CENÁRIO 1: Bot Desktop Indisponível
        # ====================================================================
        print_scenario_header(
            1,
            "Bot Desktop Indisponivel (Crash da GUI)",
            "A aplicacao desktop fecha abruptamente. O bot deve tentar retry, acionar fallback degradado e nao travar o pipeline."
        )
        bot_01 = DesktopCollectorBot(runner_id="RUNNER_DEMO_01")
        res_01 = bot_01.run(simulate_crash=True)

        assert res_01["status"] == "DEGRADED", "O bot 01 deveria ter reportado status DEGRADED"
        assert res_01["degraded_mode"] is True, "O modo degradado deveria estar True"
        print(f"[OK] Cenário 1 validado: Fallback degradado ativado com sucesso. Motivo: {res_01['motivo_degradacao']}")
        results_summary["Cenário 1 (Desktop Indisponível)"] = "APROVADO (Fallback Degradado Ativado)"

        # ====================================================================
        # CENÁRIO 2: Timeout de Dependência
        # ====================================================================
        print_scenario_header(
            2,
            "Timeout de Dependencia do Predecessor",
            "O bot de coleta web excede o deadline configuravel. O Consolidador detecta timeout e prossegue em contingencia com dados parciais."
        )
        dlq = DeadLetterQueue()
        bot_03 = ConsolidatorBot(dlq=dlq)
        desktop_data = {
            "itens": [
                {"Cod_Item": "LG-ITEM-A", "Descricao": "Display Teste", "Estoque_Fisico": 50, "Observacao": "Estoque OK"},
                {"Cod_Item": "LG-ITEM-B", "Descricao": "Placa Teste", "Estoque_Fisico": 30, "Observacao": "Estoque OK"},
            ]
        }
        # Simula predecessor web sofrendo timeout
        res_03_timeout = bot_03.run(
            desktop_result=desktop_data,
            web_result={"pedidos": []},
            dependency_timeout_occurred=True
        )

        assert res_03_timeout["status"] == "COMPLETED", "Consolidador deveria finalizar com sucesso em contingência"
        assert len(res_03_timeout["itens"]) == 2, "Deveria ter processado os 2 itens disponíveis"
        print(f"[OK] Cenário 2 validado: Consolidador operou com contingência sem travar ({len(res_03_timeout['itens'])} itens processados).")
        results_summary["Cenário 2 (Timeout de Dependência)"] = "APROVADO (Contingência Parcial Sem Bloqueio)"

        # ====================================================================
        # CENÁRIO 3: Serviço de ML Fora do Ar
        # ====================================================================
        print_scenario_header(
            3,
            "Servico de ML Fora do Ar / Falha 503",
            "Endpoint de ML indisponivel. O classificador aplica fallback deterministico com confianca 0.0 e origem registrada."
        )
        import httpx
        httpx.post("http://127.0.0.1:8002/chaos/toggle?offline=true")

        bot_04 = MLClassifierBot()
        dados_para_ml = {
            "itens": [
                {
                    "cod_item": "LG-PLACA-002",
                    "descricao": "Placa Principal",
                    "status_regra": "DIVERGENCIA_ESTOQUE_INSUFICIENTE",
                    "observacao": "Divergência física constatada",
                    "exige_analise_ml": True,
                }
            ]
        }
        res_04 = bot_04.run(dados_para_ml)
        item_ml = res_04["itens"][0]

        assert item_ml["origem_decisao"] == "FALLBACK_DETERMINISTICO", f"Esperado FALLBACK_DETERMINISTICO, obtido {item_ml['origem_decisao']}"
        assert item_ml["confianca_ml"] == 0.0, "Confiança no fallback deveria ser 0.0"
        print(f"[OK] Cenário 3 validado: ML offline tratado sem exceção. Origem Decisão: {item_ml['origem_decisao']} | Causa: {item_ml['causa_divergencia']}")
        results_summary["Cenário 3 (Serviço ML Offline)"] = "APROVADO (Fallback Determinístico Gravado)"

        # Restaura ML para estado online
        httpx.post("http://127.0.0.1:8002/chaos/toggle?offline=false")

        # ====================================================================
        # CENÁRIO 4: Falha no Canal Principal (Telegram)
        # ====================================================================
        print_scenario_header(
            4,
            "Falha no Canal de Alerta Principal (Telegram)",
            "Token do Telegram invalido. O bot de notificacao captura o erro e roteia o alerta para o canal secundario (Email/Contingencia)."
        )
        bot_05 = NotifierReporterBot(runner_id="RUNNER_DEMO_01")
        res_05 = bot_05.run(
            itens_classificados=res_04["itens"],
            degraded_mode=True,
            dlq_count=0,
            forced_telegram_token="TOKEN_TOTALMENTE_INVALIDO_12345"
        )

        assert res_05["canal_notificacao_utilizado"] == "EMAIL_FALLBACK_CONTINGENCY", "Deveria ter acionado EMAIL_FALLBACK_CONTINGENCY"
        print(f"[OK] Cenário 4 validado: Alerta roteado com sucesso para o canal alternativo: {res_05['canal_notificacao_utilizado']}")
        results_summary["Cenário 4 (Telegram Falha / Fallback)"] = "APROVADO (Roteamento Contingencial Confirmado)"

        # ====================================================================
        # CENÁRIO 5: Coexistência de Runners (Mutex de Sessão Gráfica)
        # ====================================================================
        print_scenario_header(
            5,
            "Coexistencia de Runners (BotCity vs Smart Office)",
            "Dois orquestradores tentam disparar bots com sessao grafica na mesma maquina no mesmo instante. O LockManager bloqueia o segundo runner."
        )
        lock_file_test = "logs/test_coexistencia.lock"
        if Path(lock_file_test).exists():
            Path(lock_file_test).unlink()

        lock_runner_a = LockManager(lock_file=lock_file_test, runner_id="RUNNER_LEGADO_BOTCITY")
        lock_runner_b = LockManager(lock_file=lock_file_test, runner_id="RUNNER_SMART_OFFICE")

        lock_runner_a.acquire()
        print("[RUNNER_LEGADO_BOTCITY] Adquiriu com sucesso a sessão gráfica exclusiva.")

        colisao_detectada = False
        try:
            print("[RUNNER_SMART_OFFICE] Tentando adquirir a mesma sessão gráfica simultaneamente...")
            lock_runner_b.acquire()
        except RunnerLockAcquisitionError as err:
            colisao_detectada = True
            print(f"[BLOQUEIO PREVENTIVO CONFIRMADO] {err}")
        finally:
            lock_runner_a.release()
            print("[RUNNER_LEGADO_BOTCITY] Sessão gráfica liberada.")

        assert colisao_detectada is True, "O segundo runner deveria ter sido bloqueado pelo LockManager"
        print("[OK] Cenário 5 validado: Conflito de sessão gráfica e sobreposição de automação prevenida com sucesso.")
        results_summary["Cenário 5 (Coexistência de Runners)"] = "APROVADO (LockManager Bloqueou Colisão)"

        # ====================================================================
        # CENÁRIO 6: Item com Dado Irrecuperável (Dead Letter Queue)
        # ====================================================================
        print_scenario_header(
            6,
            "Item com Dado Irrecuperavel (Isolamento na DLQ)",
            "Item injetado com dados nulos/NaN e codigo corrompido. O item eh isolado na DLQ apos validacao, e os demais itens seguem normalmente."
        )
        dlq.clear()
        lote_com_sabotagem = {
            "itens": [
                {"Cod_Item": "LG-ITEM-VALIDO-01", "Descricao": "Display 4K", "Estoque_Fisico": 10, "Observacao": "Normal"},
                {"Cod_Item": "#CORRUPTED#_NaN", "Descricao": "Dados Corrompidos", "Estoque_Fisico": float("nan"), "Observacao": "Falha"},
                {"Cod_Item": "LG-ITEM-VALIDO-02", "Descricao": "Fonte 120W", "Estoque_Fisico": 20, "Observacao": "Normal"},
            ]
        }
        res_03_dlq = bot_03.run(
            desktop_result=lote_com_sabotagem,
            web_result={"pedidos": []}
        )

        assert res_03_dlq["total_dlq"] == 1, "Exatamente 1 item deveria ter sido encaminhado para a DLQ"
        assert res_03_dlq["total_processados"] == 2, "Os outros 2 itens válidos deveriam ter sido processados normalmente"
        itens_na_dlq = dlq.list_items()
        assert len(itens_na_dlq) >= 1, "Item deveria estar registrado no armazenamento persistente da DLQ"

        print(f"[OK] Cenário 6 validado: Item corrompido isolado na DLQ ({itens_na_dlq[-1]['error_reason']}). "
              f"Itens sadios processados normalmente: {res_03_dlq['total_processados']}.")
        results_summary["Cenário 6 (Item Irrecuperável -> DLQ)"] = "APROVADO (Isolamento DLQ + Sucesso nos Demais)"

        # ====================================================================
        # QUADRO RESUMO FINAL
        # ====================================================================
        print("\n" + "=" * 80)
        print("🏆 RELATORIO DE HOMOLOGACAO DOS 6 CENARIOS DE SABOTAGEM DA BANCA:")
        print("=" * 80)
        for cenario, status in results_summary.items():
            print(f"  ✓ {cenario:<45} : {status}")
        print("=" * 80)
        print("RESULTADO GERAL: 100% DOS CENARIOS DE SABOTAGEM SUPORTADOS COM EXITO!\n")

    finally:
        web_proc.terminate()
        ml_proc.terminate()
        web_proc.join(timeout=1.0)
        ml_proc.join(timeout=1.0)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    run_all_sabotage_scenarios()
