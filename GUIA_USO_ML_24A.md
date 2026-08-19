# Guia de uso e teste — Exercício 24-A (ML + RPA)

Passo a passo para **usar** e **testar** a classificação inteligente dos lotes ambíguos. Siga na ordem. Cada passo tem o comando, o que deve aparecer e o que marcar se passou.

O modelo **não substitui** as regras RN01–RN12. Ele só decide registros que o motor já marcou como **Ambíguo**. Se a API cair, o bot **não para**: cada lote vai para `REVISAO_ML_OFFLINE` e o processamento continua.

Este fluxo é o **Pipeline B** (`python main.py`). Não usa Maestro e não altera `src/validacao.py`.

---

## Antes de começar

1. Abra o PowerShell na **raiz** do repositório (`conferencia-lotes-qualidade`).
2. Ative o ambiente virtual, se usar um.
3. Instale dependências e defina o `PYTHONPATH` (vale só nesta janela):

```powershell
pip install -r requirements.txt
$env:PYTHONPATH = (Get-Location).Path
```

4. Confira a planilha de 10 dias (o nome tem **espaço**):

```powershell
Test-Path "dados_entrada\inspecao_lotes_10dias_sem gabarito.xlsx"
```

Deve retornar `True`. Sem esse arquivo o relatório completo não roda.

5. (Opcional) URL da API no `.env`:

```
ML_API_URL=http://localhost:8000
```

Se não definir, o cliente usa esse mesmo default.

- [ ] Ambiente pronto (`PYTHONPATH` + dependências)

---

## Passo 1 — Treinar o modelo

Gera o dataset fictício (≥ 200 amostras) e grava o classificador.

```powershell
python train_model.py
```

### O que deve aparecer

- `Dataset salvo em ...\models\dataset_historico.csv`
- `Amostras: 300 (treino=240, teste=60)`
- `Acurácia no split de teste: 0.88...` (por volta de 88%)
- `Modelo serializado em ...\models\classificador_lotes.pkl`

### Conferir arquivos

```powershell
Test-Path "models\classificador_lotes.pkl"
```

Deve retornar `True`.

- [ ] Modelo treinado e `.pkl` gerado

---

## Passo 2 — Subir a API (escolha uma forma)

A API precisa estar no ar **antes** de classificar ambíguos de verdade. Deixe o terminal da API aberto.

### Opção A — local (desenvolvimento)

```powershell
$env:PYTHONPATH = (Get-Location).Path
uvicorn api_ml.main:app --reload --port 8000
```

Deve aparecer algo como: `Uvicorn running on http://127.0.0.1:8000`.

### Opção B — Docker (local, não é deploy)

```powershell
docker-compose up --build api_ml
```

O healthcheck chama `GET /health`. No compose, o bot resolve a API pelo nome `http://api_ml:8000`.

- [ ] API no ar na porta 8000

---

## Passo 3 — Testar a API na mão

Em **outro** PowerShell (a API continua no primeiro).

### 3.1 Saúde do modelo

```powershell
curl http://localhost:8000/health
```

Ou no PowerShell nativo:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

**Esperado:** `status = ok` e `modelo_carregado = true`.  
Se o `.pkl` não carregou: HTTP **503** (o processo da API **não cai**).

- [ ] `/health` ok

### 3.2 Predição válida (HTTP 200)

```powershell
Invoke-RestMethod -Method POST -Uri http://localhost:8000/predict -ContentType "application/json" -Body '{"lote_id":"LG-2026-00999","status_raw":"EM AJUSTE","turno":"manhã","tem_obs":true}'
```

**Esperado:**

| Campo | Valor |
|-------|--------|
| `lote_id` | `LG-2026-00999` |
| `classe` | uma de: `valido_automatico`, `revisar`, `recusar_automatico` |
| `probabilidade` | número entre 0 e 1 |
| `nivel_confianca` | `alta` (≥ 0,85), `média` (0,65–0,85) ou `baixa` (< 0,65) |
| `latencia_ms` | preenchido |
| `acao` | classe prevista se confiança alta; senão `revisar` ou `revisar_prioritario` |

Turno da planilha (`A`, `B`, `C`) também é aceito (A = manhã, B = tarde, C = noite).

- [ ] `/predict` com payload válido retorna 200

### 3.3 Turno inválido (HTTP 422)

```powershell
try {
  Invoke-RestMethod -Method POST -Uri http://localhost:8000/predict -ContentType "application/json" -Body '{"lote_id":"LG-1","status_raw":"EM AJUSTE","turno":"madrugada","tem_obs":true}'
} catch {
  $_.Exception.Response.StatusCode.value__
}
```

**Esperado:** **422**.

- [ ] Turno inválido rejeitado com 422

---

## Passo 4 — Rodar o pipeline com a API no ar

Ainda com a API ligada:

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:ML_API_URL = "http://localhost:8000"
python main.py
```

### O que o programa faz

1. Lê a planilha de 10 dias e aplica **RN01–RN12** (igual à Aula 22/24).
2. Para cada registro **Ambíguo**, chama a API via `MLClient`.
3. Encaminha conforme a confiança (alta / média / baixa).
4. Grava auditoria e o Excel.

### Onde conferir o resultado

| Saída | O que olhar |
|-------|-------------|
| Terminal | `Decisões de ML: N (aba 'Decisões de ML')` |
| `relatorio_conferencia_lotes.xlsx` | 8 abas de sempre **+** aba **Decisões de ML** |
| `logs/decisoes_ml.jsonl` | uma linha JSON por lote que passou no classificador |

Na aba **Decisões de ML** (e no JSONL) devem existir: `lote_id`, classe, probabilidade, nível de confiança, latência e se a API estava indisponível.

As 8 abas originais **não mudam** (Válido / Divergência / Ambíguo / Erro continuam vindo das regras).

- [ ] Relatório gerado com a 9ª aba preenchida
- [ ] JSONL com uma linha por ambíguo

---

## Passo 5 — Testar a queda da API (o bot não pode parar)

A regra de ouro: um modelo que trava quando a API cai vale menos do que um que segue com revisão humana.

### 5.1 Atalho (sem planilha)

Derruba de propósito a URL da API e processa 8 ambíguos fictícios:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python scripts/ensaio_sabotagem.py
```

**Esperado no terminal:**

```
decisoes 8
acoes {'REVISAO_ML_OFFLINE'}
todas_offline True
circuito_aberto True
falhas 5
SABOTAGEM_OK
```

Depois de **5 falhas seguidas** o circuit breaker abre: as próximas chamadas devolvem `None` **sem tentar a rede**.

- [ ] Ensaio imprimiu `SABOTAGEM_OK`

### 5.2 Pipeline real com a API desligada

No terminal da API: `Ctrl+C` (ou `docker-compose stop api_ml`).

```powershell
$env:PYTHONPATH = (Get-Location).Path
python main.py
```

**Esperado:**

- o comando **termina** (não trava, não explode);
- todos os ambíguos na aba **Decisões de ML** com ação `REVISAO_ML_OFFLINE` e `API indisponível = sim`;
- as outras 8 abas continuam completas (nenhum registro some).

- [ ] `python main.py` conclui com a API fora
- [ ] Aba e JSONL marcam `REVISAO_ML_OFFLINE`

Para voltar a chamar a rede: suba a API de novo **e** reinicie o processo (`python main.py` outra vez). O circuito só reabre com `reset()` ou novo processo.

---

## Passo 6 — Suíte automatizada

```powershell
$env:PYTHONPATH = (Get-Location).Path

pytest -m unit
pytest -m integration
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

### O que esses testes cobrem

| Teste | Arquivo | O que prova |
|-------|---------|-------------|
| Payload válido → 200 | `tests/integration/test_api_ml.py` | `/predict` devolve classe, probabilidade e nível coerentes |
| Turno inválido → 422 | idem | validação Pydantic |
| `MLClient` sucesso | `tests/unit/test_ml_client.py` | retorno válido, não `None` |
| API fora | idem | devolve `None` e **não lança exceção** |
| Circuit breaker | idem | 6ª chamada não bate na rede |
| Fallback do bot | `tests/unit/test_item_processor.py` | `REVISAO_ML_OFFLINE` |
| 9ª aba | `tests/integration/test_decisoes_ml_excel.py` | nenhum lote do classificador some |

**Esperado:** testes unitários e de integração verdes; cobertura de `src` ≥ 80% (incluindo `src/ml_client.py`).

- [ ] `pytest -m unit` verde
- [ ] `pytest -m integration` verde
- [ ] cobertura ≥ 80%

---

## Como interpretar uma decisão

O bot **não prevê**. Ele só encaminha o que a API devolveu:

| Situação | Ação aplicada |
|----------|----------------|
| API ok, probabilidade ≥ 0,85 | classe prevista (`valido_automatico`, `revisar` ou `recusar_automatico`) |
| API ok, 0,65 ≤ p < 0,85 | `revisar` |
| API ok, p < 0,65 | `revisar_prioritario` |
| API fora, timeout, 4xx/5xx, JSON ruim ou circuito aberto | `REVISAO_ML_OFFLINE` |

Retreino: rode `python train_model.py` de novo e reinicie o `uvicorn` (ou o container `api_ml`). O contrato `/predict` e o `MLClient` não mudam.

---

## Problemas comuns

| Sintoma | Causa | O que fazer |
|---------|--------|-------------|
| `ModuleNotFoundError: No module named 'src'` (ou `api_ml`) | `PYTHONPATH` não definido nesta janela | `$env:PYTHONPATH = (Get-Location).Path` |
| `/health` 503 | `.pkl` ausente ou corrompido | `python train_model.py` e reiniciar a API |
| `/predict` 422 | turno fora de manhã/tarde/noite (ou A/B/C) | corrigir o JSON |
| Relatório só com `REVISAO_ML_OFFLINE` | API não está no ar (comportamento correto) | subir o `uvicorn` e rodar `python main.py` de novo |
| Circuit breaker “grudado” | 5 falhas no mesmo processo | reiniciar o `python main.py` depois que a API voltar |
| Porta 8000 ocupada | outro processo usando a porta | feche o `uvicorn` antigo ou use `--port 8001` e ajuste `ML_API_URL` |

---

## Ordem rápida (cola)

```powershell
$env:PYTHONPATH = (Get-Location).Path
python train_model.py
uvicorn api_ml.main:app --reload --port 8000          # deixe este terminal aberto
# outro terminal:
$env:PYTHONPATH = (Get-Location).Path
python main.py                                        # uso com API no ar
python scripts/ensaio_sabotagem.py                    # teste com API fora
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```
