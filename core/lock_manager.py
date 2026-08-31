"""
Gerenciador de Lock Exclusivo para Sessão Gráfica de Runners (Mutex).
Garante a coexistência segura entre BotCity Orchestrator e Smart Office,
evitando que dois runners operem a mesma tela simultaneamente.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional
from core.exceptions import RunnerLockAcquisitionError
from core.config import settings


class LockManager:
    """
    Gerenciador de arquivo de lock atômico com registro de PID, runner_id,
    timestamp e suporte a limpeza de locks órfãos (stale locks).
    """

    def __init__(
        self,
        lock_file: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        runner_id: Optional[str] = None,
    ):
        self.lock_file = Path(lock_file or settings.RUNNER_LOCK_FILE)
        self.timeout_seconds = timeout_seconds or settings.RUNNER_LOCK_TIMEOUT_SECONDS
        self.runner_id = runner_id or settings.RUNNER_ID
        self._acquired = False

    def acquire(self) -> bool:
        """
        Tenta adquirir o lock exclusivo para a sessão gráfica.
        Se o lock existir e não estiver expirado (stale), lança RunnerLockAcquisitionError.
        """
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        if self.lock_file.exists():
            try:
                content = json.loads(self.lock_file.read_text(encoding="utf-8"))
                lock_time = content.get("timestamp", 0)
                owner_runner = content.get("runner_id", "DESCONHECIDO")
                owner_pid = content.get("pid", "DESCONHECIDO")

                age = time.time() - lock_time
                if age < self.timeout_seconds:
                    raise RunnerLockAcquisitionError(
                        f"Conflito de Sessão Gráfica! O lock pertence a '{owner_runner}' "
                        f"(PID {owner_pid}) adquirido há {age:.1f}s (expira em {self.timeout_seconds - age:.1f}s)."
                    )
                else:
                    # Lock órfão expirado
                    self._release_file()
            except json.JSONDecodeError:
                # Arquivo corrompido, limpa
                self._release_file()

        # Criação atômica
        payload = {
            "runner_id": self.runner_id,
            "pid": os.getpid(),
            "timestamp": time.time(),
            "acquired_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        try:
            # os.O_CREAT | os.O_EXCL garante criação atômica no sistema de arquivos
            fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(json.dumps(payload, indent=2))
            self._acquired = True
            return True
        except FileExistsError:
            raise RunnerLockAcquisitionError(
                f"Falha de concorrência: outro runner adquiriu o lock simultaneamente."
            )

    def release(self) -> None:
        """Libera o lock se este processo for o proprietário."""
        if not self._acquired and not self.lock_file.exists():
            return

        try:
            if self.lock_file.exists():
                content = json.loads(self.lock_file.read_text(encoding="utf-8"))
                if content.get("runner_id") == self.runner_id or content.get("pid") == os.getpid():
                    self._release_file()
            self._acquired = False
        except Exception:
            self._release_file()
            self._acquired = False

    def _release_file(self) -> None:
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except OSError:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
