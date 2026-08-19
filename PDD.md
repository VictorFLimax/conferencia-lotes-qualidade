# PDD — Conferência de Lotes (Pipeline B: relatório e indicadores)

Documento de desenho do processo para o **relatório de inspeção de 10 dias**. Complementa o PDD em PDF do bot Maestro/POM (`PDD_Process_Design_Document_ajustado_POM.docx.pdf`) e **não substitui** o fluxo Dispatcher → DataPool → Performer.

## 1. Objetivo

Consolidar 250 registros de inspeção, classificar cada um segundo RN01–RN12 e entregar um dashboard executivo com 10 indicadores, ranking de regras e um resumo em linguagem de negócio.

## 2. Escopo

| Inclui | Não inclui |
|--------|------------|
| Leitura da planilha de 10 dias + Base_Referencia | Bot BotCity / DataPool (`src/main.py`) |
| Validação RN01–RN12 (`src/validacao_aula22.py`) | Regras RN01–RN07 do performer (`src/validacao.py`) |
| Indicadores operacionais | Automação web Playwright/Selenium |
| Excel (8 abas) + `resumo_executivo.md` | Ajuste de regras para “bater gabarito” |

## 3. Fluxo

```
Planilha 10 dias
      │
      ▼
gerar_relatorio.processar()     ← Counter de duplicidade POR DIA
      │
      ▼
validar_registro()              ← uma classificação por linha + regra_aplicada
      │
      ▼
calcular_indicadores()          ← UMA chamada → OperationalIndicators
      │
      ├──────────────┬──────────────────┐
      ▼              ▼                  ▼
   Excel 8 abas   resumo_executivo.md  JSON/log
```

A mesma instância de `OperationalIndicators` alimenta Excel, markdown, log e JSON. Recalcular percentuais “na mão” em cada saída é proibido.

## 4. Indicadores

1. Total de registros  
2. Válidos (qtd e %)  
3. Divergências (qtd e %)  
4. Ambíguos (qtd e %)  
5. Erros de Entrada (qtd e %)  
6. Regra mais acionada (`Counter` sobre `regra_aplicada`)  
7. Taxa de qualidade da entrada — referência visual > 80%  
8. Taxa de revisão humana — referência visual < 15%  
9. Taxa de retrabalho — referência visual < 6%  
10. Ganho estimado de tempo — premissas: 120 s manual e 5 s automatizado por registro  

Os limiares 7–9 são **sinal visual**, não critério de aceite. O dataset didático pode ficar fora deles.

## 5. Premissas e limitações

- Ganho de tempo **não** é medição de produção.
- Duplicata em dias diferentes não é RN11.
- Os dois motores de validação do repositório não devem ser unificados.

## 6. Como executar

```powershell
$env:PYTHONPATH = (Get-Location).Path
python main.py
# equivalente: python gerar_relatorio.py
```
