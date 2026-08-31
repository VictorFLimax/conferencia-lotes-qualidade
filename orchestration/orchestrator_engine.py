"""
Orchestrator Engine do Pipeline Multi-Bot Híbrido.
Gerenciamento de filas, prioridades, dependências sequenciais com timeout e controle de estado.
The DX Way - Smart Office & BotCity Orchestrator Coexistence.
"""

import enum
import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional
from core.exceptions import DependencyTimeoutError, InfraFailure

logger = logging.getLogger("orchestration.engine")


class TaskPriority(enum.IntEnum):
    """Prioridades de execução de tarefas no orquestrador."""
    LOW = 10
    MEDIUM = 20
    HIGH = 30       # Ex: Bot Desktop (disputa sessão gráfica dedicada)
    CRITICAL = 40   # Ex: Notificação de emergência e contenção de Dead Letter


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    DEGRADED = "DEGRADED"


class Task:
    def __init__(
        self,
        bot_id: str,
        name: str,
        handler: Callable[..., Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout_seconds: Optional[float] = None,
        depends_on: Optional[List[str]] = None,
    ):
        self.task_id = str(uuid.uuid4())[:8]
        self.bot_id = bot_id
        self.name = name
        self.handler = handler
        self.priority = priority
        self.timeout_seconds = timeout_seconds or 30.0
        self.depends_on = depends_on or []
        self.status = TaskStatus.PENDING
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None


class OrchestratorEngine:
    """
    Motor de orquestração responsável por executar os bots do pipeline,
    respeitando prioridades, dependências e timeouts explícitos de predecessor.
    """

    def __init__(self, execution_id: Optional[str] = None):
        self.execution_id = execution_id or str(uuid.uuid4())[:8]
        self.tasks: Dict[str, Task] = {}
        self.execution_log: List[Dict[str, Any]] = []

    def register_task(
        self,
        bot_id: str,
        name: str,
        handler: Callable[..., Any],
        priority: TaskPriority = TaskPriority.MEDIUM,
        timeout_seconds: Optional[float] = None,
        depends_on: Optional[List[str]] = None,
    ) -> Task:
        task = Task(
            bot_id=bot_id,
            name=name,
            handler=handler,
            priority=priority,
            timeout_seconds=timeout_seconds,
            depends_on=depends_on,
        )
        self.tasks[task.bot_id] = task
        return task

    def execute_task_with_dependency_check(self, bot_id: str, *args, **kwargs) -> Task:
        """
        Executa uma tarefa verificando se todos os predecessors finalizaram
        dentro do deadline estipulado.
        """
        task = self.tasks.get(bot_id)
        if not task:
            raise ValueError(f"Tarefa para o bot '{bot_id}' não encontrada no orquestrador.")

        # Validação de Predecessores
        for dep_bot_id in task.depends_on:
            dep_task = self.tasks.get(dep_bot_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                if dep_task and dep_task.status == TaskStatus.TIMEOUT:
                    logger.warning(
                        f"[{task.name}] Predecessor '{dep_bot_id}' sofreu TIMEOUT. Executando em modo contingência."
                    )
                elif dep_task and dep_task.status == TaskStatus.DEGRADED:
                    logger.warning(
                        f"[{task.name}] Predecessor '{dep_bot_id}' finalizou com dados DEGRADADOS. Prosseguindo."
                    )
                elif not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    raise DependencyTimeoutError(
                        f"Dependência não atendida para [{task.name}]: bot '{dep_bot_id}' está em estado {dep_task.status if dep_task else 'INEXISTENTE'}."
                    )

        # Execução com controle de tempo
        task.status = TaskStatus.RUNNING
        task.start_time = time.time()
        logger.info(f"==> Iniciando Tarefa: [{task.bot_id}] {task.name} (Prioridade: {task.priority.name})")

        try:
            task.result = task.handler(*args, **kwargs)
            task.status = TaskStatus.COMPLETED
            logger.info(f"<== Tarefa Concluída com Sucesso: [{task.bot_id}] em {time.time() - task.start_time:.2f}s")
        except DependencyTimeoutError as dte:
            task.status = TaskStatus.TIMEOUT
            task.error = dte
            logger.error(f"[TIMEOUT] [{task.bot_id}] Excedeu deadline de dependência: {dte}")
        except InfraFailure as ife:
            task.status = TaskStatus.FAILED
            task.error = ife
            logger.error(f"[FALHA INFRA] [{task.bot_id}] Erro de infraestrutura: {ife}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = e
            logger.error(f"[ERRO NÃO TRATADO] [{task.bot_id}]: {e}")
        finally:
            task.end_time = time.time()
            self._log_task_execution(task)

        return task

    def _log_task_execution(self, task: Task):
        duration = (task.end_time - task.start_time) if task.start_time and task.end_time else 0.0
        entry = {
            "execution_id": self.execution_id,
            "bot_id": task.bot_id,
            "task_name": task.name,
            "priority": task.priority.name,
            "status": task.status.value,
            "duration_seconds": round(duration, 3),
            "error": str(task.error) if task.error else None,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.execution_log.append(entry)
