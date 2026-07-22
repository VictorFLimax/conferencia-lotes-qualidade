"""Performer: Processa itens da fila usando a lógica de negócio original."""
import logging
from botcity.maestro import BotMaestroSDK, DataPoolItem, ActivityStatus, ErrorType
from .config import Config
from .base_referencia import BaseReferencia
from .validacao import ConferenciaLotes, registro_de_linha, CamposObrigatoriosVaziosError

logger = logging.getLogger(__name__)

def process_item(maestro: BotMaestroSDK, item: DataPoolItem, config: Config) -> bool:
    numero_lote = item.fields.get("numero_lote", "DESCONHECIDO")
    logger.info(f"Iniciando validação do Lote: {numero_lote}")

    try:
        # 1. SEGURANÇA: Aqui você usaria o Vault se a BaseReferencia fosse um banco real
        # (Para este exercício, vamos manter a lógica original)
        
        # 2. DADOS: Converte o item do DataPool no seu RegistroLote original
        registro = registro_de_linha(item.fields)

        # 3. LÓGICA DE NEGÓCIO ORIGINAL (Intacta!)
        base = BaseReferencia(config)
        conferencia = ConferenciaLotes(base)
        resultado = conferencia.validar_registro(registro)

        # 4. TRATAMENTO DO RESULTADO NO MAESTRO
        if resultado.aprovado:
            logger.info(f"Lote {numero_lote} aprovado.")
            maestro.update_datapool_item(
                pool_name=config.data_pool_name,
                item_id=item.id,
                status=ActivityStatus.SUCCESS,
                fields={"resultado_validacao": "APROVADO"}
            )
            return True
        else:
            msgs = [f"[{d.regra}] {d.mensagem}" for d in resultado.divergencias]
            erro_msg = " | ".join(msgs)
            logger.warning(f"Lote {numero_lote} reprovado: {erro_msg}")
            
            maestro.update_datapool_item(
                pool_name=config.data_pool_name,
                item_id=item.id,
                status=ActivityStatus.ERROR,
                error_type=ErrorType.VALIDATION_ERROR,
                error_message=erro_msg,
                fields={"resultado_validacao": "REPROVADO"}
            )
            return False

    except CamposObrigatoriosVaziosError as e:
        logger.warning(f"ValidationError no Lote {numero_lote}: {e}")
        maestro.update_datapool_item(
            pool_name=config.data_pool_name,
            item_id=item.id,
            status=ActivityStatus.ERROR,
            error_type=ErrorType.VALIDATION_ERROR,
            error_message=str(e)
        )
        return False
        
    except Exception as e:
        logger.error(f"AppError no Lote {numero_lote}: {e}", exc_info=True)
        maestro.update_datapool_item(
            pool_name=config.data_pool_name,
            item_id=item.id,
            status=ActivityStatus.ERROR,
            error_type=ErrorType.APP_ERROR,
            error_message=f"Falha na execução: {str(e)}"
        )
        return False
