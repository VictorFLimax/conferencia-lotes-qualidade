"""
Bot 01: Coleta Desktop (LG_Estoque_Desktop_V1).
Automação do Sistema Desktop Legado com Lock de Sessão Gráfica e Resiliência.
The DX Way - Runner Dedicado, Retry com Backoff e Fallback Degradado.
"""

import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.config import settings
from core.exceptions import DesktopAppCrashError, RunnerLockAcquisitionError
from core.lock_manager import LockManager
from core.resilience import retry_with_backoff

logger = logging.getLogger("bots.desktop_collector")


class DesktopCollectorBot:
    """
    Bot 01 - Coleta de dados do sistema legado em cliente Windows.
    Exige Runner com sessão gráfica dedicada.
    """

    def __init__(self, runner_id: Optional[str] = None):
        self.bot_id = "LG_Estoque_Desktop_V1"
        self.runner_id = runner_id or settings.RUNNER_ID
        self.lock_manager = LockManager(runner_id=self.runner_id)
        self.export_file = Path("logs/desktop_estoque_exportado.json")

    def run(self, simulate_crash: bool = False) -> Dict[str, Any]:
        """
        Executa o ciclo completo com aquisição de lock de sessão gráfica,
        abertura da GUI legada, exportação e fallback degradado caso haja crash.
        """
        logger.info(f"[{self.bot_id}] Solicitando lock de sessão gráfica...")

        # 1. Mutex de Sessão Gráfica (Evita concorrência com o orquestrador legado)
        try:
            self.lock_manager.acquire()
            logger.info(f"[{self.bot_id}] Lock adquirido com sucesso para o Runner '{self.runner_id}'.")
        except RunnerLockAcquisitionError as rle:
            logger.error(f"[{self.bot_id}] Conflito de sessão gráfica detectado: {rle}")
            raise

        try:
            # 2. Coleta com Retry
            dados_estoque = self._executar_coleta_com_retry(simulate_crash=simulate_crash)
            return {
                "bot_id": self.bot_id,
                "status": "COMPLETED",
                "degraded_mode": False,
                "total_itens": len(dados_estoque),
                "itens": dados_estoque,
            }
        except DesktopAppCrashError as dce:
            # 3. Fallback Degradado: Em caso de falha do software legado, não derruba o pipeline
            logger.warning(
                f"[{self.bot_id}] ATIVAÇÃO DE FALLBACK DEGRADADO: Falha no sistema legado ({dce}). "
                f"Lote será marcado para revisão contingencial."
            )
            return {
                "bot_id": self.bot_id,
                "status": "DEGRADED",
                "degraded_mode": True,
                "motivo_degradacao": str(dce),
                "total_itens": 0,
                "itens": [],
            }
        finally:
            self.lock_manager.release()
            logger.info(f"[{self.bot_id}] Sessão gráfica liberada.")

    @retry_with_backoff(max_retries=2, initial_delay=1.0, backoff_factor=1.5, retry_exceptions=(DesktopAppCrashError,))
    def _executar_coleta_com_retry(self, simulate_crash: bool = False) -> List[Dict[str, Any]]:
        """Executa a aplicação legado em subprocesso e recupera os dados gerados."""
        if self.export_file.exists():
            self.export_file.unlink()

        cmd = [sys.executable, settings.DESKTOP_APP_PATH, "--auto-export"]
        if simulate_crash:
            cmd.append("--crash")

        logger.info(f"[{self.bot_id}] Acionando GUI Desktop: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        try:
            stdout, stderr = proc.communicate(timeout=10)
            if proc.returncode != 0:
                raise DesktopAppCrashError(f"Aplicação desktop encerrou anormalmente com código {proc.returncode}: {stderr}")
        except subprocess.TimeoutExpired:
            proc.kill()
            raise DesktopAppCrashError("Aplicação desktop travou e não respondeu dentro de 10s.")

        if not self.export_file.exists():
            raise DesktopAppCrashError("Arquivo de dados exportados pela GUI não foi gerado.")

        try:
            conteudo = json.loads(self.export_file.read_text(encoding="utf-8"))
            logger.info(f"[{self.bot_id}] Coletados {len(conteudo)} itens de estoque com sucesso.")
            return conteudo
        except Exception as e:
            raise DesktopAppCrashError(f"Falha ao ler os dados gerados pela GUI: {e}")
