"""
Bot 02: Coleta Web (LG_Fornecedores_Web_V1).
Coleta de pedidos de compras de fornecedores no portal B2B.
The DX Way - Resiliente a instabilidades de rede e timeouts.
"""

import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from core.config import settings
from core.exceptions import WebPortalUnavailableError
from core.resilience import retry_with_backoff

logger = logging.getLogger("bots.web_collector")


class WebCollectorBot:
    """
    Bot 02 - Coleta de pedidos de compras de fornecedores via Portal Web B2B.
    """

    def __init__(self, base_url: Optional[str] = None):
        self.bot_id = "LG_Fornecedores_Web_V1"
        self.base_url = base_url or settings.WEB_PORTAL_URL

    def run(self, timeout_override: Optional[float] = None) -> Dict[str, Any]:
        """
        Executa a coleta de pedidos com retry e proteção contra timeouts.
        """
        logger.info(f"[{self.bot_id}] Conectando ao Portal Web B2B: {self.base_url}/pedidos...")
        timeout = timeout_override or 5.0

        try:
            pedidos = self._consultar_portal_com_retry(timeout=timeout)
            logger.info(f"[{self.bot_id}] Coletados {len(pedidos)} pedidos com sucesso.")
            return {
                "bot_id": self.bot_id,
                "status": "COMPLETED",
                "total_pedidos": len(pedidos),
                "pedidos": pedidos,
            }
        except WebPortalUnavailableError as wue:
            logger.error(f"[{self.bot_id}] Falha ao coletar dados do portal web: {wue}")
            raise

    @retry_with_backoff(max_retries=3, initial_delay=1.0, backoff_factor=1.5, retry_exceptions=(WebPortalUnavailableError,))
    def _consultar_portal_com_retry(self, timeout: float = 5.0) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/pedidos"
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                if response.status_code != 200:
                    raise WebPortalUnavailableError(
                        f"Portal Web retornou status HTTP {response.status_code}: {response.text}"
                    )
                data = response.json()
                return data.get("data", [])
        except httpx.TimeoutException:
            raise WebPortalUnavailableError(f"Timeout de conexão ({timeout}s) ao consultar {url}")
        except httpx.RequestError as exc:
            raise WebPortalUnavailableError(f"Erro de comunicação com o portal web: {exc}")
