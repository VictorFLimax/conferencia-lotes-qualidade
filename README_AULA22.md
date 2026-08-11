# Relatório de Conferência de Lotes — Aula 22 (AX Academy)

Guia para gerar o Excel com dashboard a partir da planilha de inspeção de 10 dias.

Este fluxo é **independente** do bot BotCity/Maestro. Não altera `src/validacao.py` nem o performer.

---

## O que faz

1. Lê a planilha de 10 dias + aba `Base_Referencia`
2. Valida cada registro com as regras **RN01–RN12**
3. Classifica cada linha em **exatamente uma** categoria:
   - Válido
   - Divergência
   - Ambíguo
   - Erro de Entrada
4. Gera `relatorio_conferencia_lotes.xlsx` com dashboard (gráficos nativos do Excel)
5. Grava log em `logs/relatorio_aula22.log`

---

## Arquivos envolvidos

| Arquivo | Função |
|---------|--------|
| `gerar_relatorio.py` | Script principal (rodar este) |
| `src/validacao_aula22.py` | Regras RN01–RN12 + `RegistroValidado` |
| `dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx` | Entrada padrão |
| `relatorio_conferencia_lotes.xlsx` | Saída gerada na raiz |
| `logs/relatorio_aula22.log` | Log da execução |

---

## Pré-requisitos

- Python 3.10+ (testado com 3.12)
- Dependências do projeto:

```powershell
pip install -r requirements.txt
```

Pacotes usados neste fluxo: `pandas`, `openpyxl`, `python-dotenv`.

---

## Como executar

No PowerShell, na **raiz do repositório**:

```powershell
cd C:\caminho\para\conferencia-lotes-qualidade

# Garante que o pacote src seja encontrado
$env:PYTHONPATH = (Get-Location).Path

python gerar_relatorio.py
```

Saída esperada no terminal (exemplo da última rodada):

```
Entrada: ...\dados_entrada\inspecao_lotes_10dias_sem gabarito.xlsx
Saída:   ...\relatorio_conferencia_lotes.xlsx
--- Resultado ---
Total processado: 250
  Válido: 158 (63.2%)
  Divergência: 50 (20.0%)
  Ambíguo: 20 (8.0%)
  Erro de Entrada: 22 (8.8%)
Soma abas filtradas: 158+50+20+22 = 250  OK
...
```

Se o arquivo de entrada não existir, o script **para** com mensagem de erro.

---

## Configuração opcional (.env)

Crie ou edite o `.env` na raiz (não é obrigatório — há defaults):

```env
INPUT_FILE=dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx
OUTPUT_FILE=relatorio_conferencia_lotes.xlsx
LOG_FILE=logs/relatorio_aula22.log
```

| Variável | Default | Descrição |
|----------|---------|-----------|
| `INPUT_FILE` | `dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx` | Planilha de inspeção |
| `OUTPUT_FILE` | `relatorio_conferencia_lotes.xlsx` | Excel de saída (raiz) |
| `LOG_FILE` | `logs/relatorio_aula22.log` | Log em texto |

Caminhos relativos são resolvidos a partir da raiz do projeto.

Também dá para definir só na sessão:

```powershell
$env:INPUT_FILE = "dados_entrada/inspecao_lotes_10dias_sem gabarito.xlsx"
$env:OUTPUT_FILE = "relatorio_conferencia_lotes.xlsx"
$env:PYTHONPATH = (Get-Location).Path
python gerar_relatorio.py
```

---

## Como usar o Excel gerado

Abra `relatorio_conferencia_lotes.xlsx` no Excel / LibreOffice.

### Abas

| Aba | Conteúdo |
|-----|----------|
| **Resumo** | Dashboard: totais, %, gráfico de rosca e evolução diária |
| **Todos** | Os 250 registros com status normalizado e classificação |
| **Válidos** | Somente classificação Válido |
| **Divergências** | Somente Divergência (RN05, RN10, RN11) |
| **Ambíguos** | Somente Ambíguo (RN09 — revisão humana) |
| **Erros de Entrada** | Somente Erro de Entrada (RN01–RN04, RN12) |
| **Log** | Data/hora e totais da execução |

A soma **Válidos + Divergências + Ambíguos + Erros de Entrada** deve ser igual a **Todos** (250). O script valida isso em runtime.

### Dashboard (aba Resumo)

- Indicadores numéricos e percentuais das 4 classificações
- **Gráfico de rosca** (DoughnutChart) — distribuição
- **Gráfico de linha** — evolução de (Divergências + Ambíguos) nos 10 dias

Os gráficos são objetos nativos do Excel (não imagens). A aba Resumo serve para print/PDF.

### Colunas nas abas de dados

Lote, Produto, Linha, Turno, Status original, Status (normalizado), Responsável, Data inspeção, Observação, Data referência, Classificação, Regra, Mensagem.

**Normalização de status:** `OK` → `APROVADO`, `NOK` → `REPROVADO`.

---

## Regras de negócio (RN01–RN12)

Cada registro cai em **uma** classificação, com esta precedência:

1. **Erro de Entrada** — RN01–RN04 (lote/produto/linha/status vazios) e RN12 (data ausente ou ≠ DD/MM/AAAA)
2. **Divergência** — RN11 (lote duplicado no **mesmo dia**, a partir da 2ª ocorrência)
3. **Divergência** — RN05 (lote não existe na `Base_Referencia`)
4. Normalização — RN06/RN07 (`OK`/`NOK`)
5. **Ambíguo** — RN09 (status desconhecido, ex.: EM AJUSTE, CANCELADO…)
6. **Divergência** — RN10 (REPROVADO sem observação)
7. **Válido** — RN08 (APROVADO / REPROVADO / PENDENTE)

Duplicata em **dias diferentes** não é RN11.

---

## Formato da planilha de entrada

- **10 abas diárias** no padrão `Insp_DD_MM_2026` (descobertas por regex)
- **1 aba** `Base_Referencia`
- Abas diárias: título (l1), metadados (l2), cabeçalho (l3), dados a partir da l4  
  Colunas: `lote_id`, `produto`, `linha`, `turno`, `status`, `responsavel`, `data`, `observacao`
- Base: cabeçalho na linha 2, dados a partir da linha 3  
  Colunas: `lote_id`, `codigo_produto`, `descricao_produto`, `status_cadastro`

---

## Problemas comuns

| Problema | O que fazer |
|----------|-------------|
| `ModuleNotFoundError: src` | Defina `$env:PYTHONPATH = (Get-Location).Path` na raiz |
| Arquivo de entrada não encontrado | Confira o nome (há um **espaço**: `sem gabarito`) ou `INPUT_FILE` |
| Falta `openpyxl` / `pandas` | `pip install -r requirements.txt` |
| Gráficos não aparecem | Abra no Excel/LibreOffice (são charts nativos, não PNG) |

---

## Relação com o bot BotCity

| Fluxo | Comando | Validação |
|-------|---------|-----------|
| Relatório Aula 22 (este guia) | `python gerar_relatorio.py` | `src/validacao_aula22.py` (RN01–RN12) |
| Bot Maestro / web | `python bot.py` | `src/validacao.py` (RN01–RN07 do performer) |

Para o bot completo, veja o [README.md](README.md) principal.
