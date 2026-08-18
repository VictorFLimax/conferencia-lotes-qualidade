# Relatório de Conferência de Lotes — AX Academy (LG Electronics / IFAM)

Sistema de automação e validação para conferência de lotes de inspeção diária, incluindo o gerador de relatórios executivos em Excel com Dashboard e uma **Suíte de Testes Automatizados** cobrindo a pirâmide de testes (Unitários, Integração, Regressão e End-to-End).

---

## O que o Projeto Faz

1. **Processamento de Lotes:** Lê a planilha de inspeção diária (10 abas diárias) e a aba `Base_Referencia`.
2. **Validação de Regras de Negócio (RN01–RN12):** Avalia cada registro e o classifica em **exatamente uma** das quatro categorias:
   - **Válido**
   - **Divergência**
   - **Ambíguo**
   - **Erro de Entrada**
3. **Relatório Executivo:** Gera o arquivo `relatorio_conferencia_lotes.xlsx` contendo a aba **Resumo (Dashboard com gráficos nativos do Excel)**, abas por classificação e log de execução.
4. **Garantia de Qualidade (Aula 23):** Suíte de testes automatizados com Pytest cobrindo todas as camadas da pirâmide de testes para evitar regressões silenciosas nas regras RN01–RN12.

---

## Estrutura do Repositório

```text
├── dados_entrada/          # Planilhas de entrada (ex: inspecao_lotes_10dias_sem gabarito.xlsx)
├── logs/                   # Arquivos de log de execução
├── src/                    # Código-fonte da aplicação
│   ├── base_referencia.py  # Leitura e mapeamento da Base de Referência
│   ├── config.py           # Configurações do projeto (.env)
│   ├── relatorio.py        # Construção do relatório e gráficos no Excel
│   ├── validacao.py        # Motor de validação das regras RN01-RN12
│   └── validacao_aula22.py # Regras e DataClasses da Aula 22
├── tests/                  # Suíte de Testes Consolidados (Aula 23)
│   ├── conftest.py         # Fixtures e Mocks globais (Base_Referencia simulada, tmp_path)
│   ├── unit/               # Testes Unitários (regras de negócio, parametrização e unittest)
│   ├── integration/        # Testes de Integração (leitura + validação + geração do Excel)
│   └── e2e/                # Testes End-to-End (pipeline completo com mocks)
├── gerar_relatorio.py      # Script executor da geração do relatório
├── pyproject.toml / pytest.ini # Configuração dos markers e cobertura do Pytest
├── README.md               # Documentação do projeto
└── requirements.txt        # Dependências do projeto
```

---

## Pré-requisitos e Instalação

- Python 3.10+ (testado na versão 3.12)

Instalação das dependências:

```powershell
pip install -r requirements.txt
```

---

## Geração do Relatório Excel (Aula 22)

### Execução

No terminal (PowerShell), a partir da raiz do repositório:

```powershell
# Garante que o pacote src seja localizado
$env:PYTHONPATH = (Get-Location).Path

python gerar_relatorio.py
```

### Configuração via .env (Opcional)

Crie um arquivo `.env` na raiz para sobrescrever os caminhos padrão:

```
INPUT_FILE=dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx
OUTPUT_FILE=relatorio_conferencia_lotes.xlsx
LOG_FILE=logs/relatorio_aula22.log
```

---

## Suíte de Testes Automatizados (Aula 23)

A suíte foi desenvolvida para blindar o bot contra regressões silenciosas, garantindo que refatorações não alterem o comportamento das regras RN01–RN12.

### Arquitetura da Pirâmide de Testes

| Camada | Marker | Descrição | Exemplo |
|---|---|---|---|
| Unitário | `@pytest.mark.unit` | Testes isolados de funções e regras de negócio sem I/O. | Normalização de status (NOK → REPROVADO), `unittest.TestCase` com `setUp`/`subTest` e `@pytest.mark.parametrize`. |
| Integração | `@pytest.mark.integration` | Colaboração entre leitura da planilha, validação e geração do arquivo temporário. | Leitura + Validação gerando relatório em `tmp_path`. |
| Regressão | `@pytest.mark.regression` | Proteção contra bugs antigos ou regras críticas corrigidas. | Verificação do comportamento da RN10 (REPROVADO sem observação). |
| End-to-End | `@pytest.mark.e2e` | Teste do fluxo ponta a ponta sobre dados simulados e mockados. | Execução do pipeline completo verificando integridade do resumo final. |

### Executando os Testes

Você pode executar a suíte completa ou filtrar por camada utilizando os markers configurados:

**1. Executar todos os testes**

```bash
pytest
```

**2. Executar por Camada Específica (Markers)**

```bash
# Executa apenas os Testes Unitários
pytest -m unit

# Executa apenas os Testes de Integração
pytest -m integration

# Executa apenas os Testes de Regressão
pytest -m regression

# Executa apenas os Testes End-to-End (E2E)
pytest -m e2e

# Executa combinações (ex: Unitários e Integração)
pytest -m "unit or integration"
```

---

## Relatório de Cobertura de Código (≥ 80%)

A meta do projeto é manter a cobertura de código dos módulos de negócio igual ou superior a 80%, comprovada via plugin `pytest-cov`.

**Executar testes e gerar relatório no terminal**

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

**Gerar relatório visual interativo em HTML**

```bash
pytest --cov=src --cov-report=html
```

O relatório em HTML será salvo no diretório `htmlcov/index.html` e serve como evidência auditável de cobertura.

---

## Mocks e Isolamento de Testes

- **Base_Referencia Mockada:** Os testes utilizam `unittest.mock.MagicMock` e fixtures centralizadas no `conftest.py` para simular consultas sem dependência do arquivo real em disco.
- **Escrita Segura:** Nenhum teste escreve arquivos reais na raiz do projeto. Qualquer geração de planilha nos testes de integração utiliza a fixture `tmp_path` do Pytest.
- **Data/Hora:** Chamadas de relógio e datas são mockadas para evitar testes frágeis (flaky tests).
- **Tratamento de Exceções Conhecidas:** Regras pendentes ou bugs mapeados são mantidos com decorators explicitando o motivo:
  - `@pytest.mark.skip(reason="...")`: Para funcionalidades dependentes de ambiente ou futuras.
  - `@pytest.mark.xfail(reason="...")`: Para falhas conhecidas em tratamento.

---

## Resumo das Regras de Negócio (RN01–RN12)

Os registros são classificados em ordem estrita de precedência:

1. **Erro de Entrada:** RN01–RN04 (campos obrigatórios vazios) e RN12 (data ausente ou fora do formato DD/MM/AAAA).
2. **Divergência (Duplicidade):** RN11 (lote duplicado na mesma aba/dia).
3. **Divergência (Inexistente):** RN05 (lote ausente na Base_Referencia).
4. **Ambíguo:** RN09 (status não catalogado, necessita análise humana).
5. **Divergência (Observação):** RN10 (status REPROVADO sem campo de observação preenchido).
6. **Válido:** RN08 (status válidos: APROVADO, REPROVADO com obs, ou PENDENTE).

---

## Solução de Problemas Comuns

| Erro / Sintoma | Causa | Solução |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | Python não encontrou o diretório raiz no path. | Execute `$env:PYTHONPATH = (Get-Location).Path` antes de rodar o comando. |
| `PytestUnknownMarkWarning` | Markers não cadastrados na configuração do Pytest. | Verifique se o `pytest.ini` ou `pyproject.toml` contém a declaração da seção `[pytest.markers]`. |
| Cobertura abaixo de 80% | Inclusão de scripts executáveis/legados na medição. | Certifique-se de que o arquivo `.coveragerc` ou `pyproject.toml` lista as omissões dos arquivos executáveis/runners. |