"""Ensaio local de sabotagem: API inacessível, bot não para."""
from src.item_processor import REVISAO_ML_OFFLINE, processar_ambiguos_com_ml
from src.ml_client import MLClient
from src.validacao_aula22 import (
    CLASSIFICACAO_AMBIGUO,
    CLASSIFICACAO_VALIDO,
    RegistroValidado,
)


def reg(lote: str, cls: str = CLASSIFICACAO_AMBIGUO) -> RegistroValidado:
    return RegistroValidado(
        lote_id=lote,
        produto="TV",
        linha="L1",
        turno="A",
        status_original="EM AJUSTE",
        status_normalizado="EM AJUSTE",
        responsavel="Ana",
        data="15/06/2026",
        observacao="",
        data_referencia="15/06/2026",
        classificacao=cls,
        regra="RN09",
        mensagem="t",
        regra_aplicada="RN09",
    )


def main() -> int:
    cliente = MLClient(url="http://127.0.0.1:59999", timeout=0.3)
    registros = [reg(f"L{i}") for i in range(1, 9)] + [
        reg("OK", CLASSIFICACAO_VALIDO)
    ]
    decisoes = processar_ambiguos_com_ml(registros, cliente=cliente)
    print("decisoes", len(decisoes))
    print("acoes", {d.acao for d in decisoes})
    print("todas_offline", all(d.offline for d in decisoes))
    print("circuito_aberto", cliente.circuito_aberto)
    print("falhas", cliente.falhas_consecutivas)
    assert len(decisoes) == 8
    assert all(d.acao == REVISAO_ML_OFFLINE for d in decisoes)
    assert cliente.circuito_aberto
    print("SABOTAGEM_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
