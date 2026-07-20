import time
import logging
from botcity.maestro import BotMaestroSDK, DataPoolItem, ActivityStatus, ErrorType
from src.config import Config
from src.vault_client import get_erp_credentials

logger = logging.getLogger(__name__)

def process_item(maestro: BotMaestroSDK, item: DataPoolItem) -> bool:
    logger.info(f"Processando item da fila: {item.fields.get('nome')}")
    
    cpf = item.fields.get("cpf", "").strip()
    if not cpf:
        logger.warning(f"ValidationError: CPF em branco para o usuário {item.fields.get('nome')}. Marcando como erro.")
        maestro.update_datapool_item(
            pool_name=Config.DATA_POOL_NAME,
            item_id=item.id,
            status=ActivityStatus.ERROR,
            error_type=ErrorType.VALIDATION_ERROR,
            error_message="CPF está em branco."
        )
        return False

    try:
        creds = get_erp_credentials(maestro)
        logger.info(f"Simulando processamento no ERP para CPF: {cpf}")
        time.sleep(1)
        
        maestro.update_datapool_item(
            pool_name=Config.DATA_POOL_NAME,
            item_id=item.id,
            status=ActivityStatus.SUCCESS
        )
        logger.info(f"Item processado com sucesso: {item.fields.get('nome')}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar item {item.id}: {e}")
        maestro.update_datapool_item(
            pool_name=Config.DATA_POOL_NAME,
            item_id=item.id,
            status=ActivityStatus.ERROR,
            error_type=ErrorType.APP_ERROR,
            error_message=str(e)
        )
        return False
