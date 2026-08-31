# Conferência de Lotes — Qualidade

Bot de automação em Python para **conferência e auditoria de lotes de qualidade**, integrado ao [BotCity Maestro](https://botcity.dev/), com automação web via **Playwright** ou **Selenium**, screenshots, Execution Log e Result Files.

**Repositório:** [https://github.com/VictorFLimax/conferencia-lotes-qualidade](https://github.com/VictorFLimax/conferencia-lotes-qualidade)

### Equipe

| Integrante |
|------------|
| Victor |
| André |
| Gustavo |
| Mouriem |

---

## O que já foi implementado

| Recurso | Status | Detalhe |
|---------|--------|---------|
| Entry point `bot.py` | Pronto | Exigido pelo BotCity Runner / Easy Deploy |
| Configuração via `.env` | Pronto | `INPUT_FILE`, Maestro, web, screenshots, log |
| `.env.botcity` no ZIP | Pronto | Config sem segredos para o Runner |
| Dispatcher → DataPool | Pronto | Popula a fila a partir da planilha |
| Performer (validação) | Pronto | Consome fila e aplica RN01–RN07 |
| Escolha Playwright / Selenium | Pronto | `WEB_AUTOMATION_DRIVER` |
| HTML de teste no ZIP | Pronto | `html/login.html` → `lote-teste.html` |
| URL relativa portável | Pronto | `WEB_AUTOMATION_URL=html/login.html` |
| Auto-install Chromium | Pronto | `PLAYWRIGHT_AUTO_INSTALL=true` |
| Screenshots | Pronto | `logs/screenshots/*.png` |
| Result Files (artefatos) | Pronto | JSON + log + PNGs via `post_artifact` |
| Execution Log | Pronto | Etapas no Orchestrator (`new_log_entry`) |
| Alerts | Pronto | Início, fim e erros (`maestro.alert`) |
| Parâmetros da task | Pronto | Sobrescrevem o `.env` no Runner |
| Pack ZIP (`pack_botcity.py`) | Pronto | Gera `dist/conferencia-lotes-botcity.zip` |
| Vault (credenciais) | Pronto | Opcional via `VAULT_ENABLED` |
| Relatório Aula 22/24 | Pronto | Dashboard + 10 indicadores — `python main.py` |
| ML + RPA (Aula 24-A) | Pronto | Classifica ambíguos via FastAPI + RandomForest; bot nunca para |

---

## Visão geral

Fluxo: **Dispatcher → DataPool → Performer → (opcional) Web → Observabilidade Maestro**.

### O que o bot faz

1. Carrega config (`.env` local ou `.env.botcity` no Runner)
2. Conecta no Maestro (`from_sys_args` no Runner / login local)
3. Aplica parâmetros da task (se houver)
4. (Opcional) Popula o DataPool a partir da planilha (`RUN_DISPATCHER=true`)
5. Consome a fila e valida cada lote (RN01–RN07)
6. Abre o HTML e preenche o formulário com **Playwright** ou **Selenium**
7. Tira screenshots (login, sucesso, erro)
8. Grava Execution Log + Alerts + Result Files
9. Finaliza a task no Maestro

---

## Arquitetura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Planilha Excel │────▶│    Dispatcher    │────▶│    DataPool     │
│  (entrada)      │     │  (popula fila)   │     │   (Maestro)     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Result Files    │◀────│    Performer     │◀────│  Consumo fila   │
│ Log + Alerts    │     │  (valida lotes)  │     │                 │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           ┌────────────────┐      ┌─────────────────────┐
           │ Base Referência│      │ Automação web       │
           │ + RN01–RN07    │      │ Playwright|Selenium │
           └────────────────┘      │ + screenshots       │
                                   └─────────────────────┘
```

---

## Estrutura do projeto

```
conferencia-lotes-qualidade/
├── bot.py                         # Entry point BotCity (Easy Deploy)
├── pack_botcity.py                # Gera o ZIP para o Maestro
├── train_model.py                 # Dataset fictício + treino RandomForest
├── requirements.txt
├── docker-compose.yml             # bot + api_ml (healthcheck)
├── .env.example
├── api_ml/
│   ├── main.py                    # FastAPI POST /predict e GET /health
│   ├── encoding.py                # Mapas idênticos ao treino
│   ├── confianca.py               # Limiares 0,85 / 0,65
│   ├── requirements.txt
│   └── Dockerfile
├── models/
│   └── classificador_lotes.pkl    # Artefato (modelo + encoders)
├── html/
│   ├── login.html
│   └── lote-teste.html
├── src/
│   ├── main.py                    # Fluxo BotCity + observabilidade
│   ├── config.py
│   ├── dispatcher.py
│   ├── bot.py                     # Performer Maestro (RN01–RN07)
│   ├── item_processor.py          # Encaminha ambíguos; fallback REVISAO_ML_OFFLINE
│   ├── ml_client.py               # Cliente resiliente + circuit breaker
│   ├── validacao.py               # RN01–RN07 do Maestro (não misturar)
│   ├── validacao_aula22.py        # RN01–RN12 do relatório
│   ├── operational_indicators.py
│   ├── relatorio.py
│   ├── base_referencia.py
│   ├── vault_client.py
│   ├── artifacts.py
│   ├── maestro_observability.py
│   ├── pages/
│   └── web/
├── dados_entrada/
├── logs/
└── dist/
```

---

## Pré-requisitos

- Python 3.11+
- Conta BotCity Maestro + DataPool criado (`FilaConferenciaLotes_Eq_AGMV`)
- Planilha em `dados_entrada/` (local)
- Playwright: `python -m playwright install chromium` (ou `PLAYWRIGHT_AUTO_INSTALL=true`)
- Selenium: Chrome instalado (`webdriver-manager` baixa o driver)

---

## Instalação

```bash
git clone https://github.com/VictorFLimax/conferencia-lotes-qualidade.git
cd conferencia-lotes-qualidade

python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
python -m playwright install chromium
Copy-Item .env.example .env   # Windows
# cp .env.example .env        # Linux/macOS
```

### Dependências

| Pacote | Uso |
|--------|-----|
| `botcity-maestro-sdk` | Maestro, DataPool, logs, alerts, artefatos |
| `python-dotenv` | `.env` |
| `pandas` / `openpyxl` | Planilha |
| `playwright` | Automação web (opção A) |
| `selenium` + `webdriver-manager` | Automação web (opção B) |
| `pytest` | Testes |
| `scikit-learn` / `joblib` | Classificador de ambíguos |
| `FastAPI` / `uvicorn` / `pydantic` | API `/predict` e `/health` |
| `httpx` | Cliente HTTP resiliente (`MLClient`) |

---

## Configuração (`.env`)

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `MAESTRO_ENABLED` | Liga Maestro | `true` |
| `MAESTRO_SERVER_URL` | URL do workspace | `https://lgcmd.botcity.dev` |
| `MAESTRO_LOGIN` | Login (Developer Environment) — local | `lg-cmdi` |
| `MAESTRO_API_KEY` | Key do Maestro | *(sua key)* |
| `DATA_POOL_NAME` | Label do DataPool | `FilaConferenciaLotes_Eq_AGMV` |
| `INPUT_FILE` | Planilha de entrada | `dados_entrada/inspecao_lotes_dia.xlsx` |
| `LOG_FILE` | Arquivo de log | `logs/execucao.log` |
| `VAULT_ENABLED` | Usa Vault | `false` |
| `CREDENTIAL_LABEL` | Label no Vault | `credencial_erp` |
| `RUN_DISPATCHER` | Popular a fila ao iniciar | `false` |
| `WEB_AUTOMATION_ENABLED` | Liga automação web | `true` |
| `WEB_AUTOMATION_DRIVER` | `playwright` ou `selenium` | `playwright` |
| `WEB_AUTOMATION_URL` | URL http(s) **ou** caminho relativo | `html/login.html` |
| `PLAYWRIGHT_HEADLESS` | Headless Playwright | `true` no Runner |
| `PLAYWRIGHT_AUTO_INSTALL` | Instala Chromium se faltar | `true` |
| `SELENIUM_HEADLESS` | Headless Selenium | `true` no Runner |
| `WEB_USUARIO` / `WEB_SENHA` | Login do HTML (Vault off) | `usuario.teste` |
| `SCREENSHOT_ENABLED` | Tira prints | `true` |
| `UPLOAD_ARTIFACTS` | Sobe Result Files | `true` |
| `EXECUTION_LOG_LABEL` | Label do Execution Log | `ConferenciaLotes_Execucao` |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `ML_API_URL` | URL da API de ML | `http://localhost:8000` (compose: `http://api_ml:8000`) |

> **Nunca** versione o `.env` com segredos (já está no `.gitignore`).

### Escolher Playwright ou Selenium

```env
WEB_AUTOMATION_ENABLED=true
WEB_AUTOMATION_DRIVER=playwright   # ou: selenium
WEB_AUTOMATION_URL=html/login.html
```

O orquestrador (`src/web/orchestrator.py`) lê `WEB_AUTOMATION_DRIVER` e chama o runner correspondente.

Caminhos relativos viram `file://` automaticamente — funciona igual no PC local e no Runner.

### Erro "Executable doesn't exist" (Playwright)

O Chromium não está na máquina. Com `PLAYWRIGHT_AUTO_INSTALL=true` o bot instala sozinho. Manualmente:

```powershell
python -m playwright install chromium
```

Alternativa: `WEB_AUTOMATION_DRIVER=selenium` (usa o Chrome do sistema).

---

## Planilha de entrada

Arquivo padrão: `dados_entrada/inspecao_lotes_dia.xlsx`

| Aba | Função |
|-----|--------|
| `Inspecao_14_06_2026` | Dados da inspeção |
| `Base_Referencia` | Lotes oficiais |
| `Formulario_Analise` | Análise manual (auxiliar) |

Cabeçalho da inspeção (linha 3): `lote_id`, `produto`, `linha`, `turno`, `status`, `responsavel`, `data`, `observacao`.

Exemplo: `LG-2026-00101`.

---

## Regras de negócio

| Código | O que valida |
|--------|--------------|
| RN01 | Lote existe na base de referência |
| RN02 | Produto corresponde à base |
| RN03 | Quantidade / consistência com a base |
| RN04 | Datas (stub / em evolução) |
| RN05 | Status permitido |
| RN06 | Lote não vencido (stub) |
| RN07 | Campos obrigatórios |

---

## Como executar

### Local — fluxo completo

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:RUN_DISPATCHER = "true"   # opcional
python bot.py
```

### Local — só HTML (sem Maestro)

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:MAESTRO_ENABLED = "false"
python bot.py
```

Fluxo web:

1. Abre `html/login.html`
2. Preenche usuário/senha → **Entrar**
3. Vai para `lote-teste.html`
4. Preenche lote, produto e status → **Processar Lote**
5. Valida sucesso e grava screenshot em `logs/screenshots/`

### Só popular o DataPool

```powershell
python -m src.dispatcher
```

### Relatório executivo (Pipeline B — Aulas 22 e 24)

Não usa Maestro. Detalhes em [README_AULA22.md](README_AULA22.md) e [PDD.md](PDD.md).

```powershell
$env:PYTHONPATH = (Get-Location).Path
python main.py
```

Gera o Excel com 8 abas essenciais + 9ª aba `Decisões de ML`, o `resumo_executivo.md` e o JSON em `logs/`. Premissa do ganho de tempo: 120 s manuais vs 5 s automatizados por registro (estimativa didática).

---

## Exercício 24-A — classificação inteligente de lotes (ML + RPA)

**Como usar e testar (passo a passo):** [GUIA_USO_ML_24A.md](GUIA_USO_ML_24A.md).

Camada **nova**: o motor de regras (RN01–RN12) continua igual. O modelo só decide os registros já marcados como **Ambíguo**. Separação: **o bot faz automação, o modelo faz predição, a API faz a ponte.**

O que mais vale é **degradação elegante sob estresse**, não acurácia em condição ideal.

```
Planilha 10 dias → validar_registro() → Ambíguos
                                          │
                                          ▼
                                    MLClient (timeout 2,5s)
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
              pred válida           pred is None         circuito aberto
              (API no ar)        (timeout/4xx/5xx)     (5 falhas seguidas)
                     │                    │                    │
                     ▼                    ▼                    ▼
            calibração 0,85/0,65   REVISAO_ML_OFFLINE   REVISAO_ML_OFFLINE
                     │                    └────────┬───────────┘
                     ▼                             ▼
              log JSONL + aba              bot continua o lote
              "Decisões de ML"
```

### Como o dataset foi gerado

Script versionado: `train_model.py` (300 amostras fictícias, seed 42).

| Feature | Origem | Codificação |
|---------|--------|-------------|
| `status_raw` | Status não padronizado (RN09): EM AJUSTE, CANCELADO, BLOQUEADO, RETRABALHO, AGUARDANDO, INDEFINIDO, EM ANALISE, LIBERADO PARCIAL, QUARENTENA, DEVOLVIDO | mapa fixo inteiro (`api_ml/encoding.py`); desconhecido → `OUTRO` |
| `turno` | manhã / tarde / noite (A/B/C da planilha viram o mesmo eixo) | 0 / 1 / 2 |
| `tem_obs` | observação preenchida? | 0 / 1 |

**Três classes**

| Classe | Lógica de rótulo (antes do ruído) |
|--------|-----------------------------------|
| `recusar_automatico` | CANCELADO ou BLOQUEADO; DEVOLVIDO sem observação |
| `valido_automatico` | LIBERADO PARCIAL ou AGUARDANDO com observação no turno manhã/tarde; QUARENTENA com observação de manhã |
| `revisar` | EM AJUSTE / EM ANALISE / INDEFINIDO / RETRABALHO; noite sem observação; demais combinações ambíguas |

**Ruído:** 10% das amostras trocam o rótulo para outra classe, para o modelo não ser trivial.

Os mapas de status e turno vão **dentro do `.pkl`** junto do `RandomForestClassifier`, para a API codificar do mesmo jeito que o treino.

### Decisões de design do modelo

- **RandomForest:** lida com features categóricas já codificadas, não exige escala, é estável em dataset pequeno e serializa fácil com `joblib`.
- **Hiperparâmetros:** `n_estimators=120`, `max_depth=8`, `min_samples_leaf=3`, `random_state=42` — profundidade limitada para não memorizar o ruído.
- **Split:** 80/20 estratificado. Acurácia no teste da geração atual: **88,33%**. Um modelo de ~80% que nunca para o bot vale mais que 95% que trava quando a API cai.
- **Limiares 0,85 e 0,65:** 0,95 reduziria falsos automáticos, mas mandaria quase tudo para revisão humana. 0,85 equilibra risco e volume. É escolha de **risco de negócio**, não técnica pura. Falso `recusar_automatico` descarta lote bom (custo alto e visível); falso `valido_automatico` deixa passar lote ruim (custo silencioso). Por isso só a confiança **alta** aplica a classe prevista automaticamente.

### Como subir a API

```powershell
$env:PYTHONPATH = (Get-Location).Path

# 1) treinar (gera models/classificador_lotes.pkl)
python train_model.py

# 2) API local (dev)
uvicorn api_ml.main:app --reload --port 8000

# ou via docker-compose (local — não é deploy remoto)
docker-compose up --build api_ml
```

Variável `ML_API_URL` (default `http://localhost:8000`; no compose o bot usa `http://api_ml:8000`).

```powershell
# health
curl http://localhost:8000/health

# predict (turno inválido deve dar 422)
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"lote_id\":\"LG-1\",\"status_raw\":\"EM AJUSTE\",\"turno\":\"manhã\",\"tem_obs\":true}"
```

`GET /health` → `{"status":"ok","modelo_carregado":true}` ou HTTP 503 se o `.pkl` não carregou. O processo da API **não cai**.

### Calibração de confiança (exata)

| Probabilidade | Nível | Ação no bot |
|---------------|-------|-------------|
| ≥ 0,85 | alta | aplica a classe prevista (`valido_automatico` / `revisar` / `recusar_automatico`) |
| 0,65 ≤ p < 0,85 | média | `revisar` |
| < 0,65 | baixa | `revisar_prioritario` |

### Comportamento sob falha

`src/ml_client.py` **nunca lança exceção**. Timeout, rede, HTTP 4xx/5xx e JSON inválido viram `None`.

**Circuit breaker:** 5 falhas consecutivas abrem o circuito; daí em diante `classificar()` devolve `None` **sem tentar a rede**. Uma chamada bem-sucedida zera o contador. Para voltar a tentar com o circuito aberto: `MLClient.reset()` ou reinício do processo.

**Fallback:** `src/item_processor.py` — se `pred is None`, o lote vai para `REVISAO_ML_OFFLINE` e o pipeline dos 10 dias **continua**. Nada some.

Auditoria: log JSONL em `logs/decisoes_ml.jsonl` (`lote_id`, `classe`, `probabilidade`, `nivel_confianca`, `latencia_ms`, `offline`) e 9ª aba **Decisões de ML** no Excel.

### Ensaio de sabotagem (local)

Derrubar a API no meio do lote **não pode travar o bot**.

```powershell
$env:PYTHONPATH = (Get-Location).Path

# 1) API no ar — decisões reais na aba / JSONL
docker-compose up --build api_ml
python main.py

# 2) Sabotagem: derruba a API e roda de novo
docker-compose stop api_ml
python main.py
```

Esperado no passo 2: o processo termina; ambíguos saem como `REVISAO_ML_OFFLINE` no log e na 9ª aba; após 5 falhas o circuit breaker para de chamar a rede (latência cai para imediata). Sem API local, o mesmo fallback acontece ao rodar `python main.py` direto.

Atalho sem planilha (API propositalmente inacessível; confirma as 8 decisões offline e o circuito aberto):

```powershell
$env:PYTHONPATH = (Get-Location).Path
python scripts/ensaio_sabotagem.py
```

### Testes novos

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -m unit
pytest -m integration
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```

Inclui: payload válido `/predict`, turno inválido 422, `MLClient` sucesso, API fora (`None` sem exceção), circuit breaker na 6ª chamada sem HTTP.

---

## Subir no BotCity Maestro

Docs: [Python Custom Bot](https://documentation.botcity.dev/tutorials/custom-automations/python-custom/) · [Easy Deploy](https://documentation.botcity.dev/maestro/features/easy-deploy/) · [Setup SDK](https://documentation.botcity.dev/maestro/maestro-sdk/setup/)

1. Gerar o ZIP:

```powershell
python pack_botcity.py
```

Saída: `dist/conferencia-lotes-botcity.zip`  
Inclui: `bot.py`, `requirements.txt`, `.env.botcity`, `html/`, `src/`  
**Não** inclui: `.env`, `.venv`, planilha, logs.

2. Easy Deploy → tecnologia **Python** → entry point `bot.py`.

### Prioridade de configuração no Runner

1. `.env.botcity` (embarcado no ZIP)
2. `.env` na máquina do Runner (se existir)
3. **Parâmetros da task** (maior prioridade)

Exemplo de parâmetros na task:

| Parâmetro | Valor |
|-----------|-------|
| `WEB_AUTOMATION_DRIVER` | `selenium` |
| `PLAYWRIGHT_HEADLESS` | `true` |
| `DATA_POOL_NAME` | outro DataPool |

Autenticação no Runner: `BotMaestroSDK.from_sys_args()`.  
Local: `MAESTRO_SERVER_URL` + `MAESTRO_LOGIN` + `MAESTRO_API_KEY`.

---

## Observabilidade no Maestro (implementado)

### Result Files (artefatos / prints)

Docs: https://documentation.botcity.dev/maestro/maestro-sdk/result-files/

Via `maestro.post_artifact(...)` o bot sobe:

| Arquivo | Conteúdo |
|---------|----------|
| `resumo_execucao.json` | Métricas da execução |
| `execucao.log` | Log textual completo |
| `*.png` | Screenshots de login / sucesso / erro |

Onde ver: menu **Result Files** ou aba **Result Files** da task.

### Execution Log (acompanhar o processo)

Docs: https://documentation.botcity.dev/maestro/maestro-sdk/log/

Label: `ConferenciaLotes_Execucao` (`EXECUTION_LOG_LABEL`)

Etapas gravadas com `new_log_entry`:

`INICIO` → `DATAPOOL` → `VALIDACAO` → `WEB` → `WEB_LOTE` → `ARTIFACTS` → `FIM`

Colunas: etapa, status, lote, mensagem, driver, horário.

### Alerts

Docs: https://documentation.botcity.dev/maestro/maestro-sdk/alerts-and-messages/

`maestro.alert(...)` no início, no fim e em erros (`INFO` / `WARN` / `ERROR`).

```env
SCREENSHOT_ENABLED=true
UPLOAD_ARTIFACTS=true
EXECUTION_LOG_LABEL=ConferenciaLotes_Execucao
```

Sem `task_id` (execução local), prints e log ficam só em `logs/`; Execution Log e Alerts sobem no Runner.

---

## Fluxo de execução (detalhe)

1. `Config.carregar()` — `.env` ou `.env.botcity`
2. Login Maestro (Runner ou local)
3. Parâmetros da task aplicados
4. Execution Log criado / reutilizado + alerta de início
5. Vault (opcional)
6. Dispatcher (se `RUN_DISPATCHER=true`)
7. Consumo do DataPool + validação + log por item
8. Automação web + screenshots + log por lote
9. Upload de Result Files (JSON, log, PNGs)
10. Alerta de fim + `finish_task`

Códigos de saída: `0` sucesso · `1` erro crítico.

---

## Segurança e Vault

Com `VAULT_ENABLED=true`, busca `CREDENTIAL_LABEL` no Maestro. Com Vault off, usa `WEB_USUARIO` / `WEB_SENHA`.

- `.env` fora do Git e do ZIP
- Logs nunca imprimem a senha

---

## Docker

```bash
docker compose up --build
docker compose up --build api_ml    # só a API de ML
# ou
docker build -t conferencia-lotes .
docker run --env-file .env -v ./dados_entrada:/app/dados_entrada:ro conferencia-lotes
```

Entry point do container do bot: `python bot.py`.  
A API (`api_ml`) sobe com `uvicorn` na porta 8000 e healthcheck em `GET /health`. No compose, o bot resolve a URL pelo nome do serviço: `http://api_ml:8000`.

---

## 🚀 Configuração e Simulação de Crise (S10-B)

Este pipeline foi projetado para operar com resiliência total, degradando com elegância sob falhas de infraestrutura ou de componentes opcionais (ML).

### 1. Orquestração Multi-Bot
O pipeline é orquestrado pelo script `src/orquestrador.py`, que dispara sequencialmente 3 bots via `create_task()` no Maestro, garantindo a cadeia de execução rastreável:
1. `andre-dispatcher-v1` (Alimenta a fila do DataPool)
2. `gustavo-conferencia-v1` (Processa, valida RN01-RN03 e enriquece com ML)
3. `victor-relatorio-v1` (Gera o relatório final com `origem_decisao` e `confianca_ml`)

Para executar a orquestração completa localmente:
```bash
python -m src.orquestrador

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Runtime |
| BotCity Maestro SDK | DataPool, tasks, logs, alerts, artefatos |
| Playwright / Selenium | Automação web (escolha via `.env`) |
| pandas / openpyxl | Planilhas |
| FastAPI / scikit-learn | API de predição + classificador de ambíguos |
| python-dotenv | Configuração |
| Docker / GitHub Actions | Empacotamento e CI |

---

## Documentação BotCity usada

| Tema | Link |
|------|------|
| Setup SDK | https://documentation.botcity.dev/maestro/maestro-sdk/setup/ |
| Custom Bot (ZIP + `bot.py`) | https://documentation.botcity.dev/tutorials/custom-automations/python-custom/ |
| Easy Deploy | https://documentation.botcity.dev/maestro/features/easy-deploy/ |
| Result Files | https://documentation.botcity.dev/maestro/maestro-sdk/result-files/ |
| Execution Log | https://documentation.botcity.dev/maestro/maestro-sdk/log/ |
| Alerts | https://documentation.botcity.dev/maestro/maestro-sdk/alerts-and-messages/ |

---

## Repositório

**https://github.com/VictorFLimax/conferencia-lotes-qualidade**

Desenvolvido por: **Victor**, **André**, **Gustavo** e **Mouriem**.
