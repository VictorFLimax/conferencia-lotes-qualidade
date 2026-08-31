"""
Padrões de Resiliência: Retry com Exponential Backoff e Circuit Breaker.
The DX Way - Proteção contra falhas transitórias de infraestrutura.
"""

import functools
import logging
import time
from typing import Callable, Tuple, Type, Any

logger = logging.getLogger("core.resilience")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    retry_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    logger_instance: Any = None,
):
    """
    Decorator para retries com recuo exponencial em operações suscetíveis a falhas transitórias.
    """
    log = logger_instance or logger

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        log.error(
                            f"[{func.__name__}] Esgotadas as {max_retries} tentativas. Última falha: {e}"
                        )
                        raise
                    log.warning(
                        f"[{func.__name__}] Tentativa {attempt}/{max_retries} falhou: {e}. "
                        f"Aguardando {delay:.2f}s antes da próxima tentativa..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exception
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit Breaker simples para contenção de falhas contínuas em serviços externos.
    Estados: CLOSED (normal), OPEN (bloqueado), HALF_OPEN (testando recuperação).
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 10.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit Breaker aberto! Limite de {self.failure_threshold} falhas atingido.")

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit Breaker em HALF_OPEN. Testando serviço...")
                return True
            return False
        if self.state == "HALF_OPEN":
            return True
        return False
