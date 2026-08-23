# PDD — Conferência de Lotes (Pipeline B: relatório, indicadores e ML)

Documento de desenho do processo para o **relatório de inspeção de 10 dias** e, a partir da Aula 24-A, para a **camada de classificação de lotes ambíguos via Machine Learning**. Complementa o PDD em PDF do bot Maestro/POM (`PDD_Process_Design_Document_ajustado_POM.docx.pdf`) e **não substitui** o fluxo Dispatcher → DataPool → Performer.

## 1. Objetivo

Consolidar 250 registros de inspeção, classificar cada um segundo RN01–RN12 e entregar um dashboard executivo com 10 indicadores, ranking de regras e um resumo em linguagem de negócio.

Desde a Aula 24-A, o processo também submete os registros classificados como **Ambíguo** a um classificador de Machine Learning (via API própria), registrando a decisão do modelo — ou a indisponibilidade da API — em log estruturado e em uma aba dedicada do relatório, sem alterar as regras RN01–RN12 já em produção.

## 2. Escopo

| Inclui | Não inclui |
|--------|------------|
| Leitura da planilha de 10 dias + Base_Referencia | Bot BotCity / DataPool (`src/main.py`) |
| Validação RN01–RN12 (`src/validacao_aula22.py`) | Regras RN01–RN07 do performer (`src/validacao.py`) |
| Indicadores operacionais | Automação web Playwright/Selenium |
| Excel (9 abas, com a aba `Decisões de ML`) + `resumo_executivo.md` | Ajuste de regras para “bater gabarito” |
| Classificação ML dos registros Ambíguos (`api_ml/`, `src/ml_client.py`, `src/item_processor.py`) | Predição dentro do bot/relatório — a predição vive só na API |
| Log estruturado de decisões de ML (`logs/decisoes_ml.jsonl`) | Retreinamento automático / MLOps contínuo |

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
      ├── registros "Ambíguo" ──▶ processar_ambiguos_com_ml()   ← src/item_processor.py
      │                                  │
      │                                  ▼
      │                          MLClient.classificar()          ← src/ml_client.py
      │                                  │ POST /predict
      │                                  ▼
      │                          API FastAPI (api_ml/main.py)    ← RandomForest via joblib
      │                                  │
      │                    pred ─────────┴───────── None (falha/timeout/circuito aberto)
      │                     │                                │
      │                     ▼                                ▼
      │             classe + confiança              REVISAO_ML_OFFLINE
      │                     └──────────────┬─────────────────┘
      │                                    ▼
      │                     DecisaoML → log estruturado (JSONL) + aba "Decisões de ML"
      │
      ├──────────────┬──────────────────┐
      ▼              ▼                  ▼
   Excel 9 abas   resumo_executivo.md  JSON/log
```

A mesma instância de `OperationalIndicators` alimenta Excel, markdown, log e JSON. Recalcular percentuais “na mão” em cada saída é proibido.

Apenas os registros já classificados como **Ambíguo** pelo motor de regras (RN01–RN12) são enviados ao classificador. O ML nunca decide Válido/Divergência/Erro de Entrada — essas classificações continuam 100% de responsabilidade de `validar_registro()`.

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

## 4.1 Camada de Machine Learning (Aula 24-A)

Componente adicional que classifica automaticamente os registros que o motor de regras marcou como **Ambíguo**, sem alterar RN01–RN12.

**Arquitetura**

| Componente | Responsabilidade | Onde |
|---|---|---|
| Dataset histórico fictício | 300 amostras, 3 features (`status_raw`, `turno`, `tem_obs`), 3 classes (`válido_automático`, `revisar`, `recusar_automático`) | `train_model.py` |
| Modelo | `RandomForestClassifier` (scikit-learn), serializado com `joblib` | `models/classificador_lotes.pkl` |
| API | FastAPI com `/predict` (Pydantic + validação de turno) e `/health`, carregada no `lifespan` | `api_ml/main.py` |
| Cliente | `MLClient` — nunca lança exceção; timeout, erro de rede ou HTTP viram `None` | `src/ml_client.py` |
| Circuit breaker | Após 5 falhas consecutivas o cliente para de tentar a rede e retorna `None` imediatamente, até `reset()`/reinício | `src/ml_client.py` |
| Encaminhamento | Traduz a predição (ou `None`) em ação operacional; fallback `REVISAO_ML_OFFLINE` | `src/item_processor.py` |
| Auditoria | Log estruturado JSONL por decisão (`lote_id`, `classe`, `probabilidade`, `nível de confiança`, `latência`, `offline`) + aba `Decisões de ML` no Excel | `logs/decisoes_ml.jsonl`, `gerar_relatorio.py` |

**Calibração de confiança** (exata, não arredondada):

| Probabilidade | Nível | Ação |
|---|---|---|
| ≥ 0,85 | alta | aplica a classe prevista automaticamente |
| [0,65 – 0,85) | média | `revisar` |
| < 0,65 | baixa | `revisar_prioritario` |

**Degradação sob falha:** se a API estiver fora do ar, com timeout, ou o circuito estiver aberto, o registro recebe `REVISAO_ML_OFFLINE` e o processamento do lote **continua até o fim** — o bot nunca para por causa do ML. Esse comportamento é validado em `scripts/ensaio_sabotagem.py` e nos testes automatizados (`tests/unit/test_ml_client.py`, `tests/integration/test_api_ml.py`, `tests/unit/test_item_processor.py`).

## 5. Premissas e limitações

- Ganho de tempo **não** é medição de produção.
- Duplicata em dias diferentes não é RN11.
- Os dois motores de validação do repositório não devem ser unificados.
- O classificador de ML é uma camada de apoio para os casos **Ambíguo**; não substitui, sobrepõe nem reclassifica Válido/Divergência/Erro de Entrada.
- O dataset de treinamento é fictício e gerado por script (`train_model.py`); não representa dados reais de produção.
- Acurácia do modelo depende do split de treino/teste a cada `python train_model.py` (seed fixa = 42, mas resultado não é contrato de SLA).

## 6. Como executar

```powershell
$env:PYTHONPATH = (Get-Location).Path
python main.py
# equivalente: python gerar_relatorio.py
```

### 6.1 Camada de ML (opcional, mas necessária para a aba "Decisões de ML")

```powershell
$env:PYTHONPATH = (Get-Location).Path

# 1) treinar e serializar o modelo
python train_model.py

# 2) subir a API (dev) — ou via docker-compose (api_ml)
uvicorn api_ml.main:app --reload

# 3) rodar o pipeline normalmente; ambíguos passam pelo MLClient automaticamente
python main.py

# 4) opcional — ensaiar a API fora do ar (sabotagem controlada)
python scripts/ensaio_sabotagem.py
```

Sem a API no ar, o pipeline roda normalmente e os registros Ambíguos saem como `REVISAO_ML_OFFLINE` — nenhum passo acima é obrigatório para gerar as 8 abas herdadas da Aula 22/24; a 9ª aba (`Decisões de ML`) é gerada de todo modo, só que com todos os registros marcados como offline.
