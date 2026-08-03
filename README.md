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
| HTML de teste no ZIP | Pronto | `html/login(1).html` → `lote-teste.html` |
| URL relativa portável | Pronto | `WEB_AUTOMATION_URL=html/login(1).html` |
| Auto-install Chromium | Pronto | `PLAYWRIGHT_AUTO_INSTALL=true` |
| Screenshots | Pronto | `logs/screenshots/*.png` |
| Result Files (artefatos) | Pronto | JSON + log + PNGs via `post_artifact` |
| Execution Log | Pronto | Etapas no Orchestrator (`new_log_entry`) |
| Alerts | Pronto | Início, fim e erros (`maestro.alert`) |
| Parâmetros da task | Pronto | Sobrescrevem o `.env` no Runner |
| Pack ZIP (`pack_botcity.py`) | Pronto | Gera `dist/conferencia-lotes-botcity.zip` |
| Vault (credenciais) | Pronto | Opcional via `VAULT_ENABLED` |

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
├── requirements.txt
├── .env.example                   # Modelo local (com segredos vazios)
├── .env.botcity                   # Config embarcada no ZIP (sem segredos)
├── README.md
├── html/
│   ├── login(1).html              # Login (ambiente de teste)
│   ├── login.html
│   └── lote-teste.html            # Formulário de lote
├── src/
│   ├── main.py                    # Fluxo completo + observabilidade
│   ├── config.py                  # Carrega .env / .env.botcity
│   ├── dispatcher.py              # Popula DataPool
│   ├── bot.py                     # Performer (1 item)
│   ├── validacao.py               # RN01–RN07
│   ├── base_referencia.py
│   ├── vault_client.py
│   ├── artifacts.py               # post_artifact (Result Files)
│   ├── maestro_observability.py   # Execution Log + Alerts
│   ├── pages/                     # Page Objects
│   │   ├── LoginPagePlaywright.py
│   │   ├── LoginPageSelenium.py
│   │   ├── FormPagePlaywright.py
│   │   └── FormPageSelenium.py
│   └── web/
│       ├── orchestrator.py        # Escolhe playwright | selenium
│       ├── playwright_runner.py   # + auto-install Chromium
│       └── selenium_runner.py
├── dados_entrada/                 # Planilha (*.xlsx fora do Git)
├── logs/
│   ├── execucao.log
│   ├── resumo_execucao.json
│   └── screenshots/               # PNGs de login / sucesso / erro
└── dist/
    └── conferencia-lotes-botcity.zip
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
| `WEB_AUTOMATION_URL` | URL http(s) **ou** caminho relativo | `html/login(1).html` |
| `PLAYWRIGHT_HEADLESS` | Headless Playwright | `true` no Runner |
| `PLAYWRIGHT_AUTO_INSTALL` | Instala Chromium se faltar | `true` |
| `SELENIUM_HEADLESS` | Headless Selenium | `true` no Runner |
| `WEB_USUARIO` / `WEB_SENHA` | Login do HTML (Vault off) | `usuario.teste` |
| `SCREENSHOT_ENABLED` | Tira prints | `true` |
| `UPLOAD_ARTIFACTS` | Sobe Result Files | `true` |
| `EXECUTION_LOG_LABEL` | Label do Execution Log | `ConferenciaLotes_Execucao` |
| `LOG_LEVEL` | Nível de log | `INFO` |

> **Nunca** versione o `.env` com segredos (já está no `.gitignore`).

### Escolher Playwright ou Selenium

```env
WEB_AUTOMATION_ENABLED=true
WEB_AUTOMATION_DRIVER=playwright   # ou: selenium
WEB_AUTOMATION_URL=html/login(1).html
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

1. Abre `html/login(1).html`
2. Preenche usuário/senha → **Entrar**
3. Vai para `lote-teste.html`
4. Preenche lote, produto e status → **Processar Lote**
5. Valida sucesso e grava screenshot em `logs/screenshots/`

### Só popular o DataPool

```powershell
python -m src.dispatcher
```

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
# ou
docker build -t conferencia-lotes .
docker run --env-file .env -v ./dados_entrada:/app/dados_entrada:ro conferencia-lotes
```

Entry point do container: `python bot.py`.

---

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Runtime |
| BotCity Maestro SDK | DataPool, tasks, logs, alerts, artefatos |
| Playwright / Selenium | Automação web (escolha via `.env`) |
| pandas / openpyxl | Planilhas |
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
