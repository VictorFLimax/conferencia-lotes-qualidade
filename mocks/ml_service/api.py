"""
Microserviço Mock de Machine Learning / NLP (FastAPI).
Endpoint: POST /predict/divergencia
Permite injeção de falhas (POST /chaos/toggle) para validação do fallback determinístico.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="LG ML Classifier Service (Simulado)", version="1.0.0")

# Estado de Caos
CHAOS_STATE = {
    "offline": False,
    "corrupted_payload": False
}


class DivergencePredictRequest(BaseModel):
    observacao: str


class DivergencePredictResponse(BaseModel):
    categoria_provavel: str
    confianca: float
    status: str = "SUCCESS"


@app.get("/health")
async def health():
    if CHAOS_STATE["offline"]:
        raise HTTPException(status_code=503, detail="Serviço de ML indisponível (Simulação de Caos)")
    return {"status": "ONLINE", "chaos": CHAOS_STATE}


@app.post("/predict/divergencia")
async def predict_divergencia(payload: DivergencePredictRequest):
    """
    Classifica a observação em uma das três categorias de negócio:
    - ATRASO_FORNECEDOR
    - DIVERGENCIA_FISICA
    - ERRO_CADASTRO
    """
    if CHAOS_STATE["offline"]:
        raise HTTPException(status_code=503, detail="[CHAOS ERROR] Serviço de ML fora do ar (503 Service Unavailable)")

    if CHAOS_STATE["corrupted_payload"]:
        # Retorna payload quebrado/inesperado
        return {"resposta_invalida": 12345, "sem_campo_categoria": True}

    texto = (payload.observacao or "").lower()

    if any(k in texto for k in ["atraso", "porto", "despacho", "rodoviario", "aduaneiro", "transporte"]):
        categoria = "ATRASO_FORNECEDOR"
        confianca = 0.92
    elif any(k in texto for k in ["fisica", "armazem", "contagem", "wms", "avaria", "saldo"]):
        categoria = "DIVERGENCIA_FISICA"
        confianca = 0.88
    elif any(k in texto for k in ["codigo", "erp", "cadastro", "antigo", "descricao"]):
        categoria = "ERRO_CADASTRO"
        confianca = 0.84
    else:
        categoria = "OUTROS_INDEFINIDO"
        confianca = 0.50  # Abaixo de 0.75 para forçar fallback determinístico por limiar

    return DivergencePredictResponse(
        categoria_provavel=categoria,
        confianca=confianca
    )


@app.post("/chaos/toggle")
async def toggle_chaos(offline: bool = False, corrupted_payload: bool = False):
    CHAOS_STATE["offline"] = offline
    CHAOS_STATE["corrupted_payload"] = corrupted_payload
    return {"message": "Estado de caos do ML atualizado", "chaos": CHAOS_STATE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
