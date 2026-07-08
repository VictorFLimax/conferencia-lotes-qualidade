"""Testes unitários do módulo de validação."""

from __future__ import annotations

from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.base_referencia import BaseReferencia
from src.config import Config
from src.validacao import (
  ConferenciaLotes,
  Divergencia,
  RegistroLote,
  REGRAS_NEGOCIO,
  ResultadoValidacao,
  registro_de_linha,
  rn07_campos_obrigatorios,
)


@pytest.fixture
def config() -> Config:
  """Configuração padrão para testes."""
  return Config(
    caminho_planilha_entrada=__import__("pathlib").Path("data/samples/planilha_lotes.xlsx"),
    caminho_saida_relatorio=__import__("pathlib").Path("data/output/divergencias.xlsx"),
    caminho_base_referencia=None,
    log_level="INFO",
  )


@pytest.fixture
def base_referencia(config: Config) -> BaseReferencia:
  """Instância de base de referência com mock."""
  return BaseReferencia(config)


@pytest.fixture
def conferencia(base_referencia: BaseReferencia) -> ConferenciaLotes:
  """Serviço de conferência configurado para testes."""
  return ConferenciaLotes(base_referencia)


@pytest.fixture
def registro_valido() -> RegistroLote:
  """Registro de lote com dados completos."""
  return RegistroLote(
    numero_lote="LOTE-001",
    codigo_produto="PROD-A",
    quantidade=100.0,
    data_fabricacao="2026-01-15",
    data_validade="2027-01-15",
    status="APROVADO",
  )


class TestRegistroLote:
  """Testes da estrutura de dados RegistroLote."""

  def test_criacao_registro(self, registro_valido: RegistroLote) -> None:
    assert registro_valido.numero_lote == "LOTE-001"
    assert registro_valido.codigo_produto == "PROD-A"
    assert registro_valido.quantidade == 100.0


class TestRegistroDeLinha:
  """Testes da conversão de linha pandas para RegistroLote."""

  def test_mapeia_colunas_corretamente(self) -> None:
    linha = pd.Series({
      "numero_lote": "LOTE-999",
      "codigo_produto": "PROD-X",
      "quantidade": 50,
      "data_fabricacao": "2026-03-01",
      "data_validade": "2027-03-01",
      "status": "PENDENTE",
    })
    registro = registro_de_linha(linha)
    assert registro.numero_lote == "LOTE-999"
    assert registro.quantidade == 50.0

  def test_valores_ausentes_usam_padrao(self) -> None:
    linha = pd.Series({})
    registro = registro_de_linha(linha)
    assert registro.numero_lote == ""
    assert registro.quantidade == 0.0


class TestRegrasNegocio:
  """Testes das regras de negócio (estrutura e contratos)."""

  def test_sete_regras_cadastradas(self) -> None:
    assert len(REGRAS_NEGOCIO) == 7
    codigos = [codigo for codigo, _ in REGRAS_NEGOCIO]
    assert codigos == [f"RN0{i}" for i in range(1, 8)]

  @pytest.mark.parametrize(
    "codigo_regra",
    [f"RN0{i}" for i in range(1, 7)],
  )
  def test_regras_nao_implementadas_levantam_erro(
    self,
    registro_valido: RegistroLote,
    codigo_regra: str,
  ) -> None:
    funcao = dict(REGRAS_NEGOCIO)[codigo_regra]
    with pytest.raises(NotImplementedError):
      funcao(registro_valido, None)

  def test_rn07_nao_implementada(self, registro_valido: RegistroLote) -> None:
    with pytest.raises(NotImplementedError):
      rn07_campos_obrigatorios(registro_valido, None)


class TestConferenciaLotes:
  """Testes do orquestrador de conferência."""

  def test_validar_registro_aprovado_quando_regras_pendentes(
    self,
    conferencia: ConferenciaLotes,
    registro_valido: RegistroLote,
  ) -> None:
    """Regras não implementadas são ignoradas; registro é aprovado por padrão."""
    resultado = conferencia.validar_registro(registro_valido)
    assert isinstance(resultado, ResultadoValidacao)
    assert resultado.aprovado is True
    assert resultado.divergencias == []

  def test_validar_registro_com_divergencia_mockada(
    self,
    conferencia: ConferenciaLotes,
    registro_valido: RegistroLote,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    def regra_falha(
      registro: RegistroLote,
      referencia: dict | None,
    ) -> list[Divergencia]:
      return [Divergencia(regra="RN99", mensagem="Falha simulada")]

    monkeypatch.setattr(
      "src.validacao.REGRAS_NEGOCIO",
      [("RN99", regra_falha)],
    )
    resultado = conferencia.validar_registro(registro_valido)
    assert resultado.aprovado is False
    assert len(resultado.divergencias) == 1

  def test_processar_planilha_chama_validacao_por_linha(
    self,
    conferencia: ConferenciaLotes,
    tmp_path: pytest.TempPathFactory,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    caminho = tmp_path.mktemp("data") / "entrada.xlsx"
    df = pd.DataFrame([
      {
        "numero_lote": "LOTE-001",
        "codigo_produto": "PROD-A",
        "quantidade": 10,
        "data_fabricacao": "2026-01-01",
        "data_validade": "2027-01-01",
        "status": "APROVADO",
      },
      {
        "numero_lote": "LOTE-002",
        "codigo_produto": "PROD-B",
        "quantidade": 20,
        "data_fabricacao": "2026-02-01",
        "data_validade": "2027-02-01",
        "status": "APROVADO",
      },
    ])
    df.to_excel(caminho, index=False)

    mock_validar = MagicMock(
      return_value=ResultadoValidacao(
        registro=RegistroLote("", "", 0, "", "", ""),
        aprovado=True,
      )
    )
    monkeypatch.setattr(conferencia, "validar_registro", mock_validar)

    resultados = conferencia.processar_planilha(caminho)
    assert len(resultados) == 2
    assert mock_validar.call_count == 2
