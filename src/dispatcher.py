import csv
import logging
from botcity.maestro import BotMaestroSDK, DataPoolItem
from src.config import Config

logger = logging.getLogger(__name__)

def run_dispatcher(maestro: BotMaestroSDK, csv_path: str):
    logger.info(f"Iniciando Dispatcher: Lendo arquivo {csv_path} e populando a fila.")
    try:
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item = DataPoolItem(
                    fields={
                        "cpf": str(row.get("cpf", "")).strip(),
                        "nome": str(row.get("nome", "")).strip(),
                        "departamento": str(row.get("departamento", "")).strip()
                    }
                )
                maestro.create_datapool_item(pool_name=Config.DATA_POOL_NAME, item=item)
                logger.info(f"Item enviado para a fila: {item.fields['nome']}")
        logger.info("Dispatcher concluído com sucesso.")
    except Exception as e:
        logger.error(f"Erro no Dispatcher: {e}")
        raise
