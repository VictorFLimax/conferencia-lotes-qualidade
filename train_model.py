"""Gera dataset histórico fictício e treina o classificador de lotes ambíguos.

O modelo NÃO substitui RN01–RN12: só decide casos que o motor de regras
já marcou como Ambíguo (status não padronizado).

Uso:
  python train_model.py
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

from api_ml.encoding import (
    CLASSES_SAIDA,
    FEATURES,
    STATUS_PARA_CODIGO,
    TURNO_PARA_CODIGO,
    vetor_features,
)

RAIZ = Path(__file__).resolve().parent
CAMINHO_MODELO = RAIZ / "models" / "classificador_lotes.pkl"
CAMINHO_DATASET = RAIZ / "models" / "dataset_historico.csv"

N_AMOSTRAS = 300
SEED = 42
TAXA_RUIDO = 0.10

STATUS_HISTORICOS = (
    "EM AJUSTE",
    "CANCELADO",
    "BLOQUEADO",
    "RETRABALHO",
    "AGUARDANDO",
    "INDEFINIDO",
    "EM ANALISE",
    "LIBERADO PARCIAL",
    "QUARENTENA",
    "DEVOLVIDO",
)
TURNOS_HISTORICOS = ("manhã", "tarde", "noite")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("train_model")


def rotulo_coerente(status: str, turno: str, tem_obs: int) -> str:
    """Lógica documentada de geração dos rótulos (antes do ruído).

    - recusar_automatico: CANCELADO / BLOQUEADO, ou DEVOLVIDO sem observação.
    - valido_automatico: LIBERADO PARCIAL ou AGUARDANDO com observação no
      turno da manhã/tarde; QUARENTENA com observação de manhã.
    - revisar: status de incerteza (EM AJUSTE, EM ANALISE, INDEFINIDO,
      RETRABALHO), noite sem observação, ou demais combinações ambíguas.
    """
    if status in {"CANCELADO", "BLOQUEADO"}:
        return "recusar_automatico"
    if status == "DEVOLVIDO" and tem_obs == 0:
        return "recusar_automatico"
    if status in {"LIBERADO PARCIAL", "AGUARDANDO"} and tem_obs == 1 and turno != "noite":
        return "valido_automatico"
    if status == "QUARENTENA" and tem_obs == 1 and turno == "manhã":
        return "valido_automatico"
    if status in {"EM AJUSTE", "EM ANALISE", "INDEFINIDO", "RETRABALHO"}:
        return "revisar"
    if turno == "noite" and tem_obs == 0:
        return "revisar"
    if tem_obs == 1:
        return "valido_automatico"
    return "revisar"


def gerar_dataset(n: int = N_AMOSTRAS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    linhas: list[dict[str, object]] = []
    for i in range(n):
        status = str(rng.choice(STATUS_HISTORICOS))
        turno = str(rng.choice(TURNOS_HISTORICOS))
        tem_obs = int(rng.integers(0, 2))
        classe = rotulo_coerente(status, turno, tem_obs)
        if rng.random() < TAXA_RUIDO:
            outras = [c for c in CLASSES_SAIDA if c != classe]
            classe = str(rng.choice(outras))
        linhas.append(
            {
                "lote_id": f"HIST-{i + 1:04d}",
                "status_raw": status,
                "turno": turno,
                "tem_obs": tem_obs,
                "classe": classe,
            }
        )
    return pd.DataFrame(linhas)


def _matriz_features(df: pd.DataFrame) -> np.ndarray:
    vetores = [
        vetor_features(row.status_raw, row.turno, row.tem_obs)
        for row in df.itertuples(index=False)
    ]
    return np.array(vetores, dtype=float)


def treinar(df: pd.DataFrame) -> dict:
    x = _matriz_features(df)
    y = df["classe"].to_numpy()
    x_treino, x_teste, y_treino, y_teste = train_test_split(
        x,
        y,
        test_size=0.20,
        random_state=SEED,
        stratify=y,
    )
    modelo = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        min_samples_leaf=3,
        random_state=SEED,
        n_jobs=1,
    )
    modelo.fit(x_treino, y_treino)
    y_pred = modelo.predict(x_teste)
    acuracia = float(accuracy_score(y_teste, y_pred))
    relatorio = classification_report(y_teste, y_pred, digits=3)
    logger.info("Amostras: %s (treino=%s, teste=%s)", len(df), len(y_treino), len(y_teste))
    logger.info("Distribuição das classes:\n%s", df["classe"].value_counts().to_string())
    logger.info("Acurácia no split de teste: %.4f", acuracia)
    logger.info("Relatório de classificação:\n%s", relatorio)
    return {
        "modelo": modelo,
        "mapa_status": dict(STATUS_PARA_CODIGO),
        "mapa_turno": dict(TURNO_PARA_CODIGO),
        "classes": list(modelo.classes_),
        "features": list(FEATURES),
        "acuracia_teste": acuracia,
        "n_amostras": int(len(df)),
        "taxa_ruido": TAXA_RUIDO,
        "versao": "1.0",
    }


def main() -> int:
    df = gerar_dataset()
    CAMINHO_DATASET.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CAMINHO_DATASET, index=False, encoding="utf-8")
    logger.info("Dataset salvo em %s", CAMINHO_DATASET)

    artefato = treinar(df)
    joblib.dump(artefato, CAMINHO_MODELO)
    logger.info("Modelo serializado em %s", CAMINHO_MODELO)
    print(f"acuracia_teste={artefato['acuracia_teste']:.4f}")
    print(f"modelo={CAMINHO_MODELO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
