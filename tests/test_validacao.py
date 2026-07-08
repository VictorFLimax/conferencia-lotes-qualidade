"""Testes unitários do módulo de validação."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest

from src.base_referencia import BaseReferencia
from src.config import Config
from src.validacao import (
  CAMPOS_OBRIGATORIOS,
  CamposObrigatoriosVaziosError,
  ConferenciaLotes,
  Divergencia,
  RegistroLote,
  REGRAS_NEGOCIO,
  ResultadoValidacao,
  registro_de_linha,
  rn07_campos_obrigatorios,
  valida_campos_obrigatorios,
  valida_estrutura,
)


def registro_completo() -> dict[str, str]:
  """Registro com todos os campos obrigatórios preenchidos."""
  return {
    "lote_id": "LOTE-001",
    "produto": "PROD-A",
    "linha": "L1",
    "turno": "MANHA",
    "status": "APROVADO",
    "responsavel": "João Silva",
  }


@pytest.fixture
def config() -> Config:
  """Configuração padrão para testes."""
  return Config(
    caminho_planilha_entrada=Path("data/samples/planilha_lotes.xlsx"),
    caminho_saida_relatorio=Path("data/output/divergencias.xlsx"),
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


class TestValidaEstrutura:
  """Testes da Issue #1 — validação de estrutura da planilha."""

  def test_estrutura_completa(self) -> None:
    df = pd.DataFrame([registro_completo()])
    resultado = valida_estrutura(df)

    assert resultado.estrutura_completa is True
    assert resultado.colunas_ausentes == []
    assert resultado.colunas_presentes == CAMPOS_OBRIGATORIOS

  def test_nao_falha_quando_falta_coluna(self) -> None:
    df = pd.DataFrame([{"lote_id": "LOTE-001", "produto": "PROD-A"}])
    resultado = valida_estrutura(df)

    assert resultado.estrutura_completa is False
    assert "linha" in resultado.colunas_ausentes
    assert "turno" in resultado.colunas_ausentes
    assert "status" in resultado.colunas_ausentes
    assert "responsavel" in resultado.colunas_ausentes

  def test_dataframe_vazio_nao_estoura_erro(self) -> None:
    df = pd.DataFrame()
    resultado = valida_estrutura(df)

    assert resultado.estrutura_completa is False
    assert len(resultado.colunas_ausentes) == len(CAMPOS_OBRIGATORIOS)


class TestValidaCamposObrigatorios:
  """Testes da Issue #1 — campos obrigatórios vazios."""

  def test_registro_valido_nao_levanta_erro(self) -> None:
    valida_campos_obrigatorios(registro_completo())

  def test_registro_valido_como_series(self) -> None:
    valida_campos_obrigatorios(pd.Series(registro_completo()))

  @pytest.mark.parametrize("campo_vazio", CAMPOS_OBRIGATORIOS)
  def test_detecta_cada_campo_vazio(self, campo_vazio: str) -> None:
    registro = registro_completo()
    registro[campo_vazio] = ""

    with pytest.raises(CamposObrigatoriosVaziosError) as exc_info:
      valida_campos_obrigatorios(registro)

    assert campo_vazio in exc_info.value.campos_vazios

  @pytest.mark.parametrize("campo_vazio", CAMPOS_OBRIGATORIOS)
  def test_detecta_campo_ausente(self, campo_vazio: str) -> None:
    registro = registro_completo()
    del registro[campo_vazio]

    with pytest.raises(CamposObrigatoriosVaziosError) as exc_info:
      valida_campos_obrigatorios(registro)

    assert campo_vazio in exc_info.value.campos_vazios

  @pytest.mark.parametrize(
    "valor_vazio",
    [None, "", "   ", float("nan")],
  )
  def test_detecta_valores_considerados_vazios(self, valor_vazio: object) -> None:
    registro = registro_completo()
    registro["status"] = valor_vazio

    with pytest.raises(CamposObrigatoriosVaziosError) as exc_info:
      valida_campos_obrigatorios(registro)

    assert "status" in exc_info.value.campos_vazios

  def test_detecta_multiplos_campos_vazios(self) -> None:
    registro = {
      "lote_id": "",
      "produto": None,
      "linha": "L1",
      "turno": "",
      "status": "APROVADO",
      "responsavel": "   ",
    }

    with pytest.raises(CamposObrigatoriosVaziosError) as exc_info:
      valida_campos_obrigatorios(registro)

    assert exc_info.value.campos_vazios == [
      "lote_id",
      "produto",
      "turno",
      "responsavel",
    ]


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
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
  ) -> None:
    caminho = tmp_path / "entrada.xlsx"
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
