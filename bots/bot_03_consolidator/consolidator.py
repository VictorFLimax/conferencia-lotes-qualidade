"""
Bot 03: Consolidação e Regras de Negócio Determinísticas (LG_Consolidacao_RN_V1).
Aplica RN01 a RN04 sobre a fusão de estoque físico e pedidos web.
Isola dados irrecuperáveis enviando para a Dead Letter Queue (DLQ).
The DX Way.
"""

import logging
import math
from typing import Any, Dict, List, Optional
from core.config import settings
from core.exceptions import DependencyTimeoutError, ItemDataFailure, InvalidItemCodeError, CorruptedQuantityError
from orchestration.dead_letter_queue import DeadLetterQueue

logger = logging.getLogger("bots.consolidator")


class ConsolidatorBot:
    """
    Bot 03 - Motor Determinístico de Regras de Negócio:
    RN01: Estoque == Solicitado -> OK
    RN02: Estoque < Solicitado  -> DIVERGENCIA_ESTOQUE_INSUFICIENTE
    RN03: Item sem Pedido       -> DIVERGENCIA_SEM_PEDIDO
    RN04: Dado corrompido/NaN   -> DLQ (ItemDataFailure)
    """

    def __init__(self, dlq: Optional[DeadLetterQueue] = None):
        self.bot_id = "LG_Consolidacao_RN_V1"
        self.dlq = dlq or DeadLetterQueue()

    def run(
        self,
        desktop_result: Dict[str, Any],
        web_result: Dict[str, Any],
        dependency_timeout_occurred: bool = False,
    ) -> Dict[str, Any]:
        logger.info(f"[{self.bot_id}] Iniciando consolidação e conferência determinística...")

        if dependency_timeout_occurred:
            logger.warning(
                f"[{self.bot_id}] DEPENDENCY TIMEOUT DETECTADO! Aplicando contingência com dados parciais."
            )

        itens_estoque = desktop_result.get("itens", []) if desktop_result else []
        pedidos_web = web_result.get("pedidos", []) if web_result else []

        # Mapeia pedidos por Cod_Item
        pedidos_map = {}
        for p in pedidos_web:
            cod = p.get("Cod_Item")
            if cod:
                pedidos_map[cod] = p

        itens_consolidados = []
        itens_dlq_count = 0

        # Processamento item a item garantindo isolamento total de falhas de dado
        for idx, estoque in enumerate(itens_estoque):
            item_id = estoque.get("Cod_Item")

            try:
                # Validação de integridade do dado (RN04)
                self._validar_integridade_item(estoque)

                pedido_correspondente = pedidos_map.pop(item_id, None)
                consolidado = self._aplicar_regras_negocio(estoque, pedido_correspondente)
                itens_consolidados.append(consolidado)

            except ItemDataFailure as idf:
                # Isolamento do item corrompido e descarte seguro para a DLQ
                itens_dlq_count += 1
                logger.warning(f"[{self.bot_id}] Item rejeitado por falha de dado. Enviando para DLQ: {idf}")
                self.dlq.enqueue(
                    item_id=str(item_id or f"ITEM_DESCONHECIDO_{idx}"),
                    raw_data=estoque,
                    error_reason=str(idf),
                    retry_count=3,
                )
                continue

        # Pedidos web que sobraram sem estoque físico correspondente
        for cod_sobra, pedido in pedidos_map.items():
            itens_consolidados.append({
                "cod_item": cod_sobra,
                "descricao": f"Pedido {pedido.get('Numero_Pedido')} sem saldo de estoque",
                "estoque_fisico": 0,
                "qtd_solicitada": pedido.get("Qtd_Solicitada", 0),
                "numero_pedido": pedido.get("Numero_Pedido"),
                "status_regra": "DIVERGENCIA_ESTOQUE_INSUFICIENTE",
                "observacao": pedido.get("Obs_Fornecedor", ""),
                "exige_analise_ml": True,
            })

        logger.info(
            f"[{self.bot_id}] Consolidação finalizada: {len(itens_consolidados)} processados, "
            f"{itens_dlq_count} encaminhados à DLQ."
        )

        return {
            "bot_id": self.bot_id,
            "status": "COMPLETED",
            "total_processados": len(itens_consolidados),
            "total_dlq": itens_dlq_count,
            "itens": itens_consolidados,
        }

    def _validar_integridade_item(self, item: Dict[str, Any]) -> None:
        """RN04 - Validação de dados de entrada."""
        cod = item.get("Cod_Item")
        if not cod or str(cod).strip() == "" or cod == "nan" or (isinstance(cod, float) and math.isnan(cod)):
            raise InvalidItemCodeError(item_id=str(cod), message="Código do item é nulo ou corrompido (NaN).", raw_data=item)

        # Caracteres de corrupção explícita
        if any(char in str(cod) for char in ["#CORRUPTED#", "\x00", "\ufffd"]):
            raise InvalidItemCodeError(item_id=str(cod), message="Código possui caracteres corrompidos irrecuperáveis.", raw_data=item)

        estoque = item.get("Estoque_Fisico")
        if estoque is None or (isinstance(estoque, float) and math.isnan(estoque)) or estoque < 0:
            raise CorruptedQuantityError(item_id=str(cod), message=f"Saldo físico inválido: {estoque}", raw_data=item)

    def _aplicar_regras_negocio(
        self,
        estoque: Dict[str, Any],
        pedido: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        cod = estoque["Cod_Item"]
        qtd_fisica = estoque.get("Estoque_Fisico", 0)
        descricao = estoque.get("Descricao", "")
        obs = estoque.get("Observacao", "")

        # RN03: Item sem pedido correspondente
        if not pedido:
            return {
                "cod_item": cod,
                "descricao": descricao,
                "estoque_fisico": qtd_fisica,
                "qtd_solicitada": 0,
                "numero_pedido": "SEM_PEDIDO",
                "status_regra": "DIVERGENCIA_SEM_PEDIDO",
                "observacao": obs,
                "exige_analise_ml": True,
            }

        qtd_solicitada = pedido.get("Qtd_Solicitada", 0)
        num_pedido = pedido.get("Numero_Pedido", "")
        obs_completa = f"{obs} | {pedido.get('Obs_Fornecedor', '')}".strip(" |")

        # RN01: Estoque Físico == Pedido Solicitado
        if qtd_fisica == qtd_solicitada:
            return {
                "cod_item": cod,
                "descricao": descricao,
                "estoque_fisico": qtd_fisica,
                "qtd_solicitada": qtd_solicitada,
                "numero_pedido": num_pedido,
                "status_regra": "OK",
                "observacao": obs_completa,
                "exige_analise_ml": False,
            }

        # RN02: Estoque Físico < Pedido Solicitado
        if qtd_fisica < qtd_solicitada:
            return {
                "cod_item": cod,
                "descricao": descricao,
                "estoque_fisico": qtd_fisica,
                "qtd_solicitada": qtd_solicitada,
                "numero_pedido": num_pedido,
                "status_regra": "DIVERGENCIA_ESTOQUE_INSUFICIENTE",
                "observacao": obs_completa,
                "exige_analise_ml": True,
            }

        # Outras divergências (Estoque Físico > Solicitado)
        return {
            "cod_item": cod,
            "descricao": descricao,
            "estoque_fisico": qtd_fisica,
            "qtd_solicitada": qtd_solicitada,
            "numero_pedido": num_pedido,
            "status_regra": "DIVERGENCIA_ESTOQUE_SOBRANTE",
            "observacao": obs_completa,
            "exige_analise_ml": True,
        }
