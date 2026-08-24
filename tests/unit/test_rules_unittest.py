import unittest
from unittest.mock import MagicMock
import pytest


def normalizar_status(status: str) -> str:
    """Função de normalização cobrindo regras de status."""
    if not status:
        return "INDETERMINADO"
    status_upper = str(status).strip().upper()
    if status_upper in ["OK", "APROVADO", "PASS"]:
        return "APROVADO"
    if status_upper in ["NOK", "REPROVADO", "FAIL"]:
        return "REPROVADO"
    return "AMBIGUO"


@pytest.mark.unit
class TestRegrasNegocioUnitTest(unittest.TestCase):

    def setUp(self):
        """Arrange: Prepara mocks e estado comum para os testes de regras RN09-RN12."""
        self.mock_base_ref = MagicMock()
        self.mock_base_ref.consultar_regra.return_value = True

    def test_rn09_a_rn12_normalizacao_e_status(self):
        """Aplica padrão AAA e subTests para múltiplas variações de regras."""
        cenarios = [
            ("OK", "APROVADO", "RN09 - Normalizacao de OK para APROVADO"),
            ("NOK", "REPROVADO", "RN10 - Normalizacao de NOK para REPROVADO"),
            ("FAIL", "REPROVADO", "RN11 - Normalizacao de FAIL para REPROVADO"),
            ("INVALIDO", "AMBIGUO", "RN12 - Trata status desconhecido/ambiguo"),
        ]

        for entrada, esperado, descricao in cenarios:
            with self.subTest(msg=descricao, entrada=entrada, esperado=esperado):
                resultado = normalizar_status(entrada)
                self.assertEqual(
                    resultado, 
                    esperado, 
                    f"Falha em {descricao}. Entrada: {entrada}"
                )


if __name__ == "__main__":
    unittest.main()