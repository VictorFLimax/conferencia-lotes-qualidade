# Guia de teste — Aula 24 (Dashboard + indicadores)

Use este arquivo para **conferir na sua máquina** se o que foi implementado realmente funciona. Siga na ordem. Cada passo tem o que executar, o que deve aparecer e o que marcar se passou.

Este fluxo é o **Pipeline B** (relatório). Não abre o bot Maestro e não usa `src/validacao.py`.

---

## Antes de começar

1. Abra o PowerShell na **raiz do repositório** (`conferencia-lotes-qualidade`).
2. Confira se a planilha existe (o nome tem **espaço**):

```powershell
Test-Path "dados_entrada\inspecao_lotes_10dias_sem gabarito.xlsx"
```

Deve retornar `True`. Se for `False`, pare: sem esse arquivo o relatório não roda.

3. Instale dependências (se ainda não instalou) e defina o `PYTHONPATH`:

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
```

O `PYTHONPATH` vale só nesta janela do terminal. Se abrir outro PowerShell, rode de novo.

---

## Passo 1 — Gerar o relatório

```powershell
python main.py
```

(O comando `python gerar_relatorio.py` faz a mesma coisa.)

### O que deve aparecer no terminal

- Caminho da planilha de 10 dias
- `Total processado: 250`
- `Válido: 158 (63.2%)`
- `Divergência: 50 (20.0%)`
- `Ambíguo: 20 (8.0%)`
- `Erro de Entrada: 22 (8.8%)`
- `Soma abas filtradas: 158+50+20+22 = 250  OK`
- `Regra mais acionada: RN08 (158)`

### Arquivos que devem existir depois

| Arquivo | Função |
|---------|--------|
| `relatorio_conferencia_lotes.xlsx` | Excel com dashboard |
| `resumo_executivo.md` | Texto de negócio com os mesmos números |
| `logs/relatorio_aula22.log` | Log da execução |
| `logs/resumo_execucao.json` | Mesmos indicadores em JSON |

- [ ] Terminal mostrou 250 e a soma 158+50+20+22
- [ ] Os quatro arquivos acima existem

**Se o total não for 250:** não “ajuste” regras. Anote o número real e pare para conferir a planilha.

---

## Passo 2 — Abrir o Excel (8 abas essenciais)

Abra `relatorio_conferencia_lotes.xlsx` no Excel (ou LibreOffice).

Confira **estas 8 abas**, com estes nomes:

1. Resumo
2. Todos
3. Válidos
4. Divergências
5. Ambíguos
6. Erros de Entrada
7. Ranking de Regras
8. Dicionário

Pode existir uma aba extra **Log**. Isso é normal.

### Aba Resumo

- Tabela **Os 10 indicadores operacionais** (não só os 4 percentuais antigos)
- Gráfico de **rosca** (distribuição das 4 classificações)
- Gráfico de **linha** (evolução de Divergências + Ambíguos nos 10 dias)

Os gráficos são objetos do Excel (dá para clicar e editar). Se for só uma imagem colada, falhou.

Sinal visual (não é critério de “passou/falhou”):

| Indicador | Referência | Valor desta planilha | Esperado |
|-----------|------------|----------------------|----------|
| Qualidade da entrada | > 80% | 91,2% | verde |
| Revisão humana | < 15% | 8,0% | verde |
| Retrabalho | < 6% | **20,0%** | vermelho — **é esperado** neste dataset didático |

- [ ] 8 abas com os nomes certos
- [ ] Resumo tem os 10 indicadores
- [ ] Dois gráficos nativos (rosca + linha)

---

## Passo 3 — Conferir que as abas não misturam classificação

Na aba **Todos** deve haver **250** linhas de dados (além do cabeçalho).

Nas abas filtradas, só a classificação da aba:

| Aba | Classificação permitida | Quantidade esperada |
|-----|-------------------------|---------------------|
| Válidos | Válido | 158 |
| Divergências | Divergência | 50 |
| Ambíguos | Ambíguo | 20 |
| Erros de Entrada | Erro de Entrada | 22 |

158 + 50 + 20 + 22 tem que ser **250**.

- [ ] Nenhuma aba misturou classificação
- [ ] A soma das 4 abas filtradas é 250

---

## Passo 4 — Ranking de Regras = indicador 6

Na aba **Ranking de Regras**, a **primeira linha de dados** deve ser:

- Código: **RN08**
- Ocorrências: **158**

Isso tem que ser igual ao “Regra mais acionada” da aba Resumo e ao texto do `resumo_executivo.md`.

- [ ] Primeira posição do ranking = RN08 com 158

---

## Passo 5 — Dicionário e resumo executivo

1. Aba **Dicionário**: deve explicar termos como Divergência, RN11, taxa de retrabalho, ganho estimado de tempo — em português, sem nome de função/classe.
2. Abra `resumo_executivo.md` e compare com o Excel:

Os números **obrigam** coincidir:

- Total 250
- 158 / 50 / 20 / 22
- RN08 com 158
- Qualidade 91,2%
- Revisão humana 8,0%
- Retrabalho 20,0%
- Ganho ≈ **479,2 minutos** (7,99 horas)
- Premissas: 120 s manual e 5 s automático por registro

- [ ] Dicionário está legível para quem não programa
- [ ] Markdown e Excel têm os mesmos totais, a mesma regra mais acionada e o mesmo ganho

---

## Passo 6 — Rodar os testes automatizados

Ainda com `$env:PYTHONPATH = (Get-Location).Path`:

```powershell
python -m pytest -m unit --ignore=tests/e2e -q
python -m pytest -m integration --ignore=tests/e2e -q
python -m pytest -m "unit or integration" --cov=src --cov-report=term-missing --cov-fail-under=80 --ignore=tests/e2e
```

### O que deve aparecer

- Testes **unit**: passar (há 1 skipped e 1 xfailed antigos da Aula 23 — isso é normal)
- Testes **integration**: passar, incluindo `test_relatorio_consolidado_oito_abas`
- Cobertura **≥ 80%**
- `src/operational_indicators.py` deve aparecer na tabela de cobertura (não pode estar na lista de omissão)

Não rode `pytest -m e2e` neste guia: esses testes pedem um servidor HTML em `localhost:8000` e não fazem parte da Aula 24.

- [ ] Unit passou
- [ ] Integration passou
- [ ] Cobertura ≥ 80% e o módulo de indicadores entrou na medição

---

## Passo 7 — Provas rápidas da banca (opcional, mas recomendado)

| Pergunta | Como conferir |
|----------|----------------|
| Sem `regra_aplicada`, quebra o indicador 6 e o Ranking? | O campo está em `RegistroValidado`; Ranking e indicador 6 leem o mesmo `Counter` dele. |
| Ganho de tempo é medição real? | Não. Está escrito no Resumo, no Dicionário e no markdown: 120 s vs 5 s são premissas. |
| Excel e markdown usam os mesmos números? | Porque os dois nascem de `calcular_indicadores()` chamado **uma vez**. |
| Total 0 no percentual? | Coberto no teste `test_percentual_divisao_por_zero_nao_levanta` (retorna 0.0). |
| Ranking e Dicionário são abas próprias? | Sim — não são seções da Resumo. |

- [ ] Entendi as 5 provas acima olhando o Excel/markdown (não precisa alterar código)

---

## Se algo falhar

| Sintoma | O que fazer |
|---------|-------------|
| `ModuleNotFoundError: src` | Rode `$env:PYTHONPATH = (Get-Location).Path` de novo na raiz |
| Arquivo de entrada não encontrado | Confira o espaço no nome: `inspecao_lotes_10dias_sem gabarito.xlsx` |
| Falta pandas/openpyxl/pytest | `pip install -r requirements.txt` |
| Retrabalho 20% “fora da meta” | Não é bug. A referência < 6% é só cor no dashboard |
| Gráficos não aparecem | Abra no Excel/LibreOffice; são charts nativos, não PNG |

---

## Resultado final do teste

Marque só se **todos** os passos 1 a 6 passaram:

- [ ] Relatório gerado com 250 registros
- [ ] Excel com 8 abas + gráficos nativos
- [ ] Markdown sincronizado com o Excel
- [ ] Testes unit/integration verdes e cobertura ≥ 80%

Se passou, a implementação da Aula 24 está funcionando nesta máquina. Aí sim você decide se publica (commit + push + PR).
