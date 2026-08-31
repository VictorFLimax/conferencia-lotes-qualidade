"""
Módulo de Telemetria, Logs Estruturados e Rastreabilidade de Execução.
Padrão The DX Way.
"""

import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from core.config import settings


class JsonFormatter(logging.Formatter):
    """Formatador de logs em formato JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "runner_id": getattr(record, "runner_id", settings.RUNNER_ID),
            "execution_id": getattr(record, "execution_id", "NO_EXEC_ID"),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


def setup_telemetry(execution_id: str = None) -> logging.Logger:
    """Configura handlers de log para console e arquivo JSON estruturado."""
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    exec_id = execution_id or str(uuid.uuid4())[:8]

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.INFO)

    # Evita duplicação de handlers se chamado múltiplas vezes
    if logger.handlers:
        return logger

    # Handler de Console formatado para leitura humana
    console_handler = logging.StreamHandler(sys.stdout)
    console_format = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    # Handler de Arquivo JSON estruturado
    log_file = settings.LOG_DIR / f"execution_{time.strftime('%Y%m%d')}.jsonl"
    file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    return logger
