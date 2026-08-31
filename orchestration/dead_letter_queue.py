"""
Dead Letter Queue (DLQ) com Persistência Auditável.
The DX Way - Isolamento de itens com falhas de dados irrecuperáveis (ItemDataFailure).
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.config import settings


class DeadLetterQueue:
    """
    Gerenciador de Dead Letter Queue.
    Registra itens rejeitados por falha irrecuperável de dado,
    garantindo que o pipeline continue sem bloqueios operacionais.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path or settings.DLQ_STORAGE_PATH)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_records([])

    def _read_records(self) -> List[Dict[str, Any]]:
        try:
            if self.storage_path.exists():
                content = self.storage_path.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else []
        except Exception:
            return []
        return []

    def _write_records(self, records: List[Dict[str, Any]]) -> None:
        self.storage_path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")

    def enqueue(
        self,
        item_id: str,
        raw_data: Any,
        error_reason: str,
        retry_count: int = 3,
        runner_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Adiciona um item com falha de dados à Dead Letter Queue."""
        record = {
            "dlq_id": f"DLQ_{int(time.time() * 1000)}",
            "item_id": item_id,
            "raw_data": raw_data,
            "error_reason": str(error_reason),
            "tentativas_realizadas": retry_count,
            "runner_id": runner_id or settings.RUNNER_ID,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "PENDENTE_ANALISE_HUMANA"
        }
        records = self._read_records()
        records.append(record)
        self._write_records(records)
        return record

    def list_items(self) -> List[Dict[str, Any]]:
        """Retorna todos os itens registrados na DLQ."""
        return self._read_records()

    def clear(self) -> None:
        """Limpa todos os itens da DLQ (utilizado em testes e inicializações)."""
        self._write_records([])
