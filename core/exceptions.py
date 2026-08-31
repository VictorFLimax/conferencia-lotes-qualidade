"""
Hierarquia de Exceções Segregadas do Pipeline Multi-Bot.
The DX Way - Distinção entre InfraFailure (infraestrutura) e ItemDataFailure (dados de item).
"""

from typing import Any, Optional


class PipelineBaseException(Exception):
    """Exceção base do pipeline."""
    def __init__(self, message: str, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.details = details


# ============================================================================
# 1. FALHAS DE INFRAESTRUTURA / EXECUÇÃO (InfraFailure)
# Comportamento: Retry com backoff, alertas críticos, fallback ou contingência.
# ============================================================================

class InfraFailure(PipelineBaseException):
    """
    Indica indisponibilidade de ambiente, rede, travamento de app,
    colisão de sessão ou falha de serviço externo.
    """
    pass


class RunnerLockAcquisitionError(InfraFailure):
    """Lançado quando uma sessão gráfica não pode ser obtida por colisão com outro Runner."""
    pass


class DependencyTimeoutError(InfraFailure):
    """Lançado quando uma tarefa predecessora não finaliza dentro do deadline configurado."""
    pass


class DesktopAppCrashError(InfraFailure):
    """Lançado quando a interface desktop fecha inesperadamente ou não responde."""
    pass


class WebPortalUnavailableError(InfraFailure):
    """Lançado quando o portal web de fornecedores retorna erro 5xx ou timeout de conexão."""
    pass


class MLServiceUnavailableError(InfraFailure):
    """Lançado quando a API de ML está fora do ar ou retorna erro de servidor."""
    pass


class NotificationDeliveryError(InfraFailure):
    """Lançado quando o envio por um canal de notificação falha."""
    pass


# ============================================================================
# 2. FALHAS DE ITEM / DADOS (ItemDataFailure)
# Comportamento: O item é isolado, submetido a retry limitado e encaminhado
# à Dead Letter Queue (DLQ). O pipeline NUNCA trava.
# ============================================================================

class ItemDataFailure(PipelineBaseException):
    """
    Indica que o dado recebido para o item é nulo, corrompido, NaN
    ou com formato inconsistente irrecuperável.
    """
    def __init__(self, item_id: str, message: str, raw_data: Optional[Any] = None):
        super().__init__(f"Falha no item [{item_id}]: {message}", details=raw_data)
        self.item_id = item_id
        self.raw_data = raw_data


class InvalidItemCodeError(ItemDataFailure):
    """Código de item ausente, nulo ou com caracteres ilegais."""
    pass


class CorruptedQuantityError(ItemDataFailure):
    """Quantidade física ou solicitada nula, negativa ou não numérica."""
    pass
