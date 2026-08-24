"""Codificação idêntica à usada no treino (`train_model.py`) e na API.

Mapas fixos (não LabelEncoder ajustado nos dados) para a predição na API
usar exatamente os mesmos códigos do treino. Status desconhecido vira OUTRO.
"""
from __future__ import annotations

# Status brutos típicos de RN09 (não padronizados) + sentinela OUTRO.
STATUS_PARA_CODIGO: dict[str, int] = {
    "EM AJUSTE": 0,
    "CANCELADO": 1,
    "BLOQUEADO": 2,
    "RETRABALHO": 3,
    "AGUARDANDO": 4,
    "INDEFINIDO": 5,
    "EM ANALISE": 6,
    "LIBERADO PARCIAL": 7,
    "QUARENTENA": 8,
    "DEVOLVIDO": 9,
    "OUTRO": 10,
}

# Turno canônico após normalização (manhã/tarde/noite). A/B/C da planilha
# de inspeção mapeiam para o mesmo eixo.
TURNO_PARA_CODIGO: dict[str, int] = {
    "manhã": 0,
    "tarde": 1,
    "noite": 2,
}

TURNOS_PERMITIDOS_ENTRADA = frozenset(
    {
        "manhã",
        "manha",
        "tarde",
        "noite",
        "a",
        "b",
        "c",
    }
)

CLASSES_SAIDA = (
    "valido_automatico",
    "revisar",
    "recusar_automatico",
)

FEATURES = ("status_cod", "turno_cod", "tem_obs")


def status_canonico(status_raw: str) -> str:
    """Normaliza status para a chave do mapa (maiúsculas, sem underscore)."""
    texto = " ".join(str(status_raw).strip().upper().replace("_", " ").replace("-", " ").split())
    return texto or "OUTRO"


def turno_canonico(turno: str) -> str | None:
    """Devolve manhã/tarde/noite ou None se o turno não for permitido."""
    bruto = str(turno).strip()
    chave = bruto.lower().replace("ã", "a")
    mapa = {
        "manha": "manhã",
        "manhã": "manhã",
        "tarde": "tarde",
        "noite": "noite",
        "a": "manhã",
        "b": "tarde",
        "c": "noite",
    }
    return mapa.get(chave)


def turno_permitido(turno: str) -> bool:
    return turno_canonico(turno) is not None


def codificar_status(status_raw: str, mapa: dict[str, int] | None = None) -> int:
    tabela = mapa or STATUS_PARA_CODIGO
    chave = status_canonico(status_raw)
    if chave not in tabela:
        chave = "OUTRO"
    return tabela.get(chave, tabela.get("OUTRO", -1))


def codificar_turno(turno: str, mapa: dict[str, int] | None = None) -> int:
    tabela = mapa or TURNO_PARA_CODIGO
    canonico = turno_canonico(turno)
    if canonico is None:
        raise ValueError(f"turno inválido: {turno!r}")
    return tabela[canonico]


def codificar_tem_obs(tem_obs: bool | int) -> int:
    return 1 if bool(tem_obs) else 0


def vetor_features(
    status_raw: str,
    turno: str,
    tem_obs: bool | int,
    mapa_status: dict[str, int] | None = None,
    mapa_turno: dict[str, int] | None = None,
) -> list[int]:
    """Retorna [status_cod, turno_cod, tem_obs] na ordem do treino."""
    return [
        codificar_status(status_raw, mapa_status),
        codificar_turno(turno, mapa_turno),
        codificar_tem_obs(tem_obs),
    ]
