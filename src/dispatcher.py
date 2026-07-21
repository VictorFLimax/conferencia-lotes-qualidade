"""Dispatcher: Lê a planilha e popula o DataPool do Maestro."""
import logging
import pandas as pd
from botcity.maestro import BotMaestroSDK, DataPoolItem
from src.config import Config

logger = logging.getLogger(__name__)

def run_dispatcher(maestro: BotMaestroSDK, config: Config) -> int:
    caminho = config.caminho_planilha_entrada
    if not caminho.exists():
        raise FileNotFoundError(f"Planilha de entrada não encontrada: {caminho}")

    logger.info(f"Lendo planilha para alimentar a fila: {caminho}")
    df = pd.read_excel(caminho)
    itens_enviados = 0

    for index, row in df.iterrows():
        item = DataPoolItem(
            fields={
                "numero_lote": str(row.get("numero_lote", "")).strip(),
                "codigo_produto": str(row.get("codigo_produto", "")).strip(),
                "quantidade": str(row.get("quantidade", "")).strip(),
                "data_fabricacao": str(row.get("data_fabricacao", "")).strip(),
                "data_validade": str(row.get("data_validade", "")).strip(),
                "status": str(row.get("status", "")).strip(),
                "linha_original": str(index + 2),
            }
        )
        maestro.create_datapool_item(pool_name=config.data_pool_name, item=item)
        itens_enviados += 1

    logger.info(f"Dispatcher concluído. {itens_enviados} itens enviados para '{config.data_pool_name}'.")
    return itens_enviados
