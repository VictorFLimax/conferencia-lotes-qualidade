"""
Portal Web de Fornecedores B2B Simulado (FastAPI).
Renderiza endpoints REST e páginas HTML simples simulando o portal de pedidos B2B.
Permite injeção de latência ou status HTTP 500 para testes de resiliência e timeout.
"""

import asyncio
import time
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI(title="LG Portal B2B Fornecedores Simulado", version="1.0.0")

# Estado de Caos para simulação de falhas/timeouts
CHAOS_STATE = {
    "latency_seconds": 0.0,
    "force_error_500": False,
}

PEDIDOS_COMPRA_MOCK = [
    {
        "Numero_Pedido": "PED-2026-901",
        "Cod_Item": "LG-DISP-001",
        "Qtd_Solicitada": 150,
        "Fornecedor": "LG Display Co.",
        "Data_Entrega": "2026-09-01",
        "Obs_Fornecedor": "Lote inspecionado sem avarias visiveis"
    },
    {
        "Numero_Pedido": "PED-2026-902",
        "Cod_Item": "LG-PLACA-002",
        "Qtd_Solicitada": 80,  # Físico é 45 -> Divergência Estoque Insuficiente
        "Fornecedor": "Hansol Electronics",
        "Data_Entrega": "2026-09-02",
        "Obs_Fornecedor": "Divergencia relatada na contagem fisica do armazem"
    },
    {
        "Numero_Pedido": "PED-2026-903",
        "Cod_Item": "LG-FONTE-003",
        "Qtd_Solicitada": 200,
        "Fornecedor": "PowerTech Manaus",
        "Data_Entrega": "2026-09-03",
        "Obs_Fornecedor": "Fornecedor comunicou atraso no despacho rodoviario"
    },
    {
        "Numero_Pedido": "PED-2026-904",
        "Cod_Item": "LG-AUTO-004",
        "Qtd_Solicitada": 100,  # Físico é 80 -> Divergência
        "Fornecedor": "Acoustic Solutions",
        "Data_Entrega": "2026-09-04",
        "Obs_Fornecedor": "Item cadastrado com codigo antigo no ERP legado"
    },
    {
        "Numero_Pedido": "PED-2026-905",
        "Cod_Item": "LG-CTRL-005",
        "Qtd_Solicitada": 320,
        "Fornecedor": "Remote Logic Corp",
        "Data_Entrega": "2026-09-05",
        "Obs_Fornecedor": "Recebido conforme Nota Fiscal"
    },
    {
        "Numero_Pedido": "PED-2026-906",
        "Cod_Item": "LG-CABO-006",
        "Qtd_Solicitada": 50,  # Físico é 0 -> Divergência
        "Fornecedor": "Amphenol Cables",
        "Data_Entrega": "2026-09-06",
        "Obs_Fornecedor": "Atraso critico no desembaraço aduaneiro do porto"
    },
    # Note que LG-SUP-007 (Físico 95) não tem pedido correspondente -> RN03
]


class LatencyConfig(BaseModel):
    latency_seconds: float
    force_error_500: bool = False


@app.get("/", response_class=HTMLResponse)
async def home():
    """Página visual simples para simulação ou inspeção manual."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Portal Fornecedores B2B LG</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #f4f6f9; margin: 20px; }
            h1 { color: #A50034; }
            table { border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #A50034; color: white; }
        </style>
    </head>
    <body>
        <h1>LG Electronics — Portal B2B de Fornecedores (Pedidos de Compra)</h1>
        <p>Endpoint REST: <code>/pedidos</code> | Monitoramento: <code>/status</code></p>
        <table>
            <tr>
                <th>Nº Pedido</th>
                <th>Cód. Item</th>
                <th>Qtd. Solicitada</th>
                <th>Fornecedor</th>
                <th>Previsão Entrega</th>
                <th>Observação</th>
            </tr>
    """
    for p in PEDIDOS_COMPRA_MOCK:
        html_content += f"""
            <tr>
                <td>{p['Numero_Pedido']}</td>
                <td>{p['Cod_Item']}</td>
                <td>{p['Qtd_Solicitada']}</td>
                <td>{p['Fornecedor']}</td>
                <td>{p['Data_Entrega']}</td>
                <td>{p['Obs_Fornecedor']}</td>
            </tr>
        """
    html_content += """
        </table>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/pedidos")
async def get_pedidos():
    """Endpoint consumido pelo Bot 02 (Web Collector)."""
    if CHAOS_STATE["latency_seconds"] > 0:
        await asyncio.sleep(CHAOS_STATE["latency_seconds"])

    if CHAOS_STATE["force_error_500"]:
        raise HTTPException(status_code=500, detail="[CHAOS ERROR] Erro interno 500 no Portal de Fornecedores")

    return {
        "status": "SUCCESS",
        "total_registros": len(PEDIDOS_COMPRA_MOCK),
        "data": PEDIDOS_COMPRA_MOCK
    }


@app.get("/status")
async def get_status():
    return {
        "portal": "ONLINE",
        "timestamp": time.time(),
        "chaos_config": CHAOS_STATE
    }


@app.post("/chaos/configure")
async def configure_chaos(config: LatencyConfig):
    """Permite aos scripts de teste injetar latência ou falhas propositais."""
    CHAOS_STATE["latency_seconds"] = config.latency_seconds
    CHAOS_STATE["force_error_500"] = config.force_error_500
    return {"message": "Configuração de caos aplicada com sucesso", "config": CHAOS_STATE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
