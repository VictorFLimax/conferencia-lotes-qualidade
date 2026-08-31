"""
Suite de Testes Unitários do Pipeline Multi-Bot Híbrido.
The DX Way - Cobertura de Regras de Negócio (RN01-RN04), LockManager, DLQ e ML Fallback.
"""

import math
import pytest
from pathlib import Path
from core.exceptions import (
    InfraFailure,
    ItemDataFailure,
    InvalidItemCodeError,
    CorruptedQuantityError,
    RunnerLockAcquisitionError,
)
from core.lock_manager import LockManager
from orchestration.dead_letter_queue import DeadLetterQueue
from bots.bot_03_consolidator.consolidator import ConsolidatorBot
from bots.bot_04_ml_classifier.classifier import MLClassifierBot


def test_rn01_estoque_igual_pedido(tmp_path):
    """RN01: Saldo físico == Pedido Solicitado -> STATUS: OK."""
    dlq = DeadLetterQueue(storage_path=tmp_path / "dlq_test.json")
    bot = ConsolidatorBot(dlq=dlq)

    desktop_data = {"itens": [{"Cod_Item": "LG-001", "Descricao": "OLED", "Estoque_Fisico": 100, "Observacao": "OK"}]}
    web_data = {"pedidos": [{"Numero_Pedido": "P-1", "Cod_Item": "LG-001", "Qtd_Solicitada": 100, "Obs_Fornecedor": "Entregue"}]}

    res = bot.run(desktop_data, web_data)
    assert res["status"] == "COMPLETED"
    assert len(res["itens"]) == 1
    item = res["itens"][0]
    assert item["status_regra"] == "OK"
    assert item["exige_analise_ml"] is False


def test_rn02_estoque_insuficiente(tmp_path):
    """RN02: Saldo físico < Pedido Solicitado -> STATUS: DIVERGENCIA_ESTOQUE_INSUFICIENTE."""
    dlq = DeadLetterQueue(storage_path=tmp_path / "dlq_test.json")
    bot = ConsolidatorBot(dlq=dlq)

    desktop_data = {"itens": [{"Cod_Item": "LG-002", "Descricao": "Placa", "Estoque_Fisico": 40, "Observacao": "Saldo baixo"}]}
    web_data = {"pedidos": [{"Numero_Pedido": "P-2", "Cod_Item": "LG-002", "Qtd_Solicitada": 80, "Obs_Fornecedor": "Urgente"}]}

    res = bot.run(desktop_data, web_data)
    item = res["itens"][0]
    assert item["status_regra"] == "DIVERGENCIA_ESTOQUE_INSUFICIENTE"
    assert item["exige_analise_ml"] is True


def test_rn03_item_sem_pedido(tmp_path):
    """RN03: Item no estoque físico sem pedido de compra correspondente -> STATUS: DIVERGENCIA_SEM_PEDIDO."""
    dlq = DeadLetterQueue(storage_path=tmp_path / "dlq_test.json")
    bot = ConsolidatorBot(dlq=dlq)

    desktop_data = {"itens": [{"Cod_Item": "LG-003", "Descricao": "Suporte", "Estoque_Fisico": 50, "Observacao": "Estoque sem ordem"}]}
    web_data = {"pedidos": []}

    res = bot.run(desktop_data, web_data)
    item = res["itens"][0]
    assert item["status_regra"] == "DIVERGENCIA_SEM_PEDIDO"
    assert item["exige_analise_ml"] is True


def test_rn04_dado_corrompido_para_dlq(tmp_path):
    """RN04: Dado corrompido/NaN gera ItemDataFailure e é encaminhado à Dead Letter Queue."""
    dlq_path = tmp_path / "dlq_corrupted.json"
    dlq = DeadLetterQueue(storage_path=dlq_path)
    bot = ConsolidatorBot(dlq=dlq)

    desktop_data = {
        "itens": [
            {"Cod_Item": "LG-VALIDO", "Descricao": "Display", "Estoque_Fisico": 10, "Observacao": "Normal"},
            {"Cod_Item": "", "Descricao": "Sem Codigo", "Estoque_Fisico": 10, "Observacao": "Corrompido"},
            {"Cod_Item": "#CORRUPTED#_NaN", "Descricao": "Invalido", "Estoque_Fisico": float("nan"), "Observacao": "Falha"},
        ]
    }
    web_data = {"pedidos": []}

    res = bot.run(desktop_data, web_data)
    assert res["total_processados"] == 1
    assert res["total_dlq"] == 2
    assert len(dlq.list_items()) == 2


def test_lock_manager_mutex(tmp_path):
    """Verifica se o LockManager impede concorrência simultânea de runners."""
    lock_file = tmp_path / "session.lock"
    lock_a = LockManager(lock_file=str(lock_file), runner_id="RUNNER_A")
    lock_b = LockManager(lock_file=str(lock_file), runner_id="RUNNER_B")

    assert lock_a.acquire() is True
    with pytest.raises(RunnerLockAcquisitionError):
        lock_b.acquire()

    lock_a.release()
    assert lock_b.acquire() is True
    lock_b.release()


def test_ml_classifier_isolamento_total():
    """Verifica se o Bot 04 aplica fallback determinístico quando o ML está offline/inacessível."""
    bot = MLClassifierBot(api_url="http://127.0.0.1:9999")  # Porta inexistente

    dados = {
        "itens": [
            {
                "cod_item": "LG-DIV-01",
                "status_regra": "DIVERGENCIA_ESTOQUE_INSUFICIENTE",
                "observacao": "Falha na entrega do fornecedor",
                "exige_analise_ml": True,
            }
        ]
    }

    res = bot.run(dados)
    assert res["status"] == "COMPLETED"
    item = res["itens"][0]
    assert item["origem_decisao"] == "FALLBACK_DETERMINISTICO"
    assert item["confianca_ml"] == 0.0
    assert item["causa_divergencia"] == "REVISAO_MANUAL_REGRA_PADRAO"
