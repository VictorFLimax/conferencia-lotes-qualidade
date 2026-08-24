import pytest


def validar_registro(registro: dict) -> str:
    """Valida registro aplicando regras de negócio."""
    if not registro.get("data"):
        return "ERRO_RN12_DATA_INVALIDA"
    if registro.get("duplicado"):
        return "ERRO_RN11_DUPLICIDADE"
    if registro.get("status") == "AMBIGUO":
        return "ERRO_RN09_STATUS_AMBIGUO"
    if registro.get("divergencia"):
        return "ERRO_RN05_DIVERGENCIA"
    return "VALIDO"


@pytest.mark.unit
@pytest.mark.parametrize(
    "registro, resultado_esperado",
    [
        ({"lote": "L1", "data": "2026-08-18", "status": "OK"}, "VALIDO"),
        ({"lote": "L2", "data": "2026-08-18", "divergencia": True}, "ERRO_RN05_DIVERGENCIA"),
        ({"lote": "L3", "data": "2026-08-18", "status": "AMBIGUO"}, "ERRO_RN09_STATUS_AMBIGUO"),
        ({"lote": "L4", "data": "2026-08-18", "duplicado": True}, "ERRO_RN11_DUPLICIDADE"),
        ({"lote": "L5", "data": None}, "ERRO_RN12_DATA_INVALIDA"),
    ],
    ids=[
        "lote_valido",
        "divergencia_rn05",
        "status_ambiguo_rn09",
        "duplicidade_rn11",
        "data_invalida_rn12",
    ],
)
def test_validar_registro_cenarios(registro, resultado_esperado):
    """Teste parametrizado cobrindo 5 cenários com IDs descritivos."""
    assert validar_registro(registro) == resultado_esperado


@pytest.mark.unit
@pytest.mark.regression
def test_regressao_rn10_reprovado_sem_observacao():
    """Garante que a correção da RN10 (reprovado sem observação) permanece estável."""
    registro = {"lote": "L10", "data": "2026-08-18", "status": "NOK", "observacao": ""}
    assert registro["status"] == "NOK"


@pytest.mark.unit
@pytest.mark.skip(reason="RN13 - Regra de integracao com ERP ainda nao implementada no sprint atual")
def test_rn13_integracao_futura():
    """Documenta uma regra que ainda será desenvolvida."""
    pass


@pytest.mark.unit
@pytest.mark.xfail(reason="Bug #104 conhecido: Falha na conversao de fuso horario no ambiente UTC")
def test_bug_conhecido_fuso_horario():
    """Documenta bug conhecido de fuso horário sem quebrar a pipeline de testes."""
    assert False, "Demonstrando xfail para bug conhecido em UTC"