"""Dispatcher: lê a planilha e popula o DataPool do Maestro."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from botcity.maestro import BotMaestroSDK, DataPoolEntry

from src.config import Config

logger = logging.getLogger(__name__)


def run_dispatcher(maestro: BotMaestroSDK, config: Config) -> int:
    caminho = Path(config.caminho_planilha_entrada)
    if not caminho.exists():
        raise FileNotFoundError(f"Planilha de entrada não encontrada: {caminho}")

    logger.info("Lendo planilha para alimentar a fila: %s", caminho)
    df = pd.read_excel(caminho)
    itens_enviados = 0

    datapool = maestro.get_datapool(label=config.data_pool_name)

    for index, row in df.iterrows():
        fields = {
            "numero_lote": str(row.get("numero_lote", row.get("lote_id", ""))).strip(),
            "codigo_produto": str(
                row.get("codigo_produto", row.get("produto", ""))
            ).strip(),
            "quantidade": str(row.get("quantidade", "")).strip(),
            "data_fabricacao": str(row.get("data_fabricacao", "")).strip(),
            "data_validade": str(row.get("data_validade", "")).strip(),
            "status": str(row.get("status", "")).strip(),
            "linha_original": str(int(index) + 2),
        }

        entry = DataPoolEntry(values=fields)
        datapool.create_entry(entry)
        itens_enviados += 1

    logger.info(
        "Dispatcher concluído. %s itens enviados para '%s'.",
        itens_enviados,
        config.data_pool_name,
    )
    return itens_enviados


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    cfg = Config.carregar()
    sdk = BotMaestroSDK()
    sdk.RAISE_NOT_CONNECTED = False
    sdk.login(
        server=cfg.maestro_server_url,
        login=cfg.maestro_login,
        key=cfg.maestro_api_key,
    )
    run_dispatcher(sdk, cfg)
