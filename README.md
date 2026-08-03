# Conferência de Lotes — Qualidade

Bot de automação em Python para **conferência e auditoria de lotes de qualidade**, integrado ao [BotCity Maestro](https://botcity.dev/), com automação web opcional via **Playwright** ou **Selenium**.

**Repositório:** [https://github.com/VictorFLimax/conferencia-lotes-qualidade](https://github.com/VictorFLimax/conferencia-lotes-qualidade)

### Equipe

| Integrante |
|------------|
| Victor |
| André |
| Gustavo |
| Mouriem |

---

## Visão geral

O bot orquestra no padrão **Dispatcher → DataPool → Performer** e, se habilitado, preenche o formulário web local (`html/login(1).html` → `lote-teste.html`).

### O que o bot faz

1. Lê a planilha em `dados_entrada/` (via `INPUT_FILE`)
2. (Opcional) Envia linhas ao DataPool do Maestro (**Dispatcher**)
3. Consome a fila item a item (**Performer**)
4. Valida cada lote com as regras RN01–RN07
5. Marca o item no DataPool (`report_done` / `report_error`)
6. (Opcional) Abre o HTML e preenche o formulário com **Playwright** ou **Selenium**
7. Gera `logs/resumo_execucao.json`, publica artefato e finaliza a task no Maestro

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
│ Resumo JSON     │◀────│    Performer     │◀────│  Consumo fila   │
│ + artefato      │     │  (valida lotes)  │     │                 │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
           ┌────────────────┐      ┌─────────────────────┐
           │ Base Referência│      │ Automação web       │
           │ + RN01–RN07    │      │ Playwright|Selenium │
           └────────────────┘      └─────────────────────┘
```

---

## Estrutura do projeto

```
conferencia-lotes-qualidade/
├── bot.py                      # Entry point BotCity Runner / Easy Deploy
├── pack_botcity.py             # Gera ZIP para subir no Maestro
├── requirements.txt
├── .env.example
├── README.md
├── html/
│   ├── login(1).html           # Tela de login (ambiente de teste)
│   ├── login.html
│   └── lote-teste.html         # Formulário de lote
├── src/
│   ├── main.py                 # Fluxo Maestro + validação + web
│   ├── config.py               # Único carregamento do .env
│   ├── dispatcher.py           # Popular o DataPool
│   ├── bot.py                  # Performer (processa 1 item)
│   ├── validacao.py            # RN01–RN07
│   ├── base_referencia.py      # Base de referência
│   ├── vault_client.py         # Credenciais Vault
│   ├── relatorio.py
│   ├── pages/                  # Page Objects
│   │   ├── LoginPagePlaywright.py
│   │   ├── LoginPageSelenium.py
│   │   ├── FormPagePlaywright.py
│   │   └── FormPageSelenium.py
│   └── web/                    # Orquestrador web
│       ├── orchestrator.py     # Escolhe playwright | selenium
│       ├── playwright_runner.py
│       └── selenium_runner.py
├── dados_entrada/              # Planilha (NÃO versionar *.xlsx)
├── logs/                       # Logs e resumo
└── dist/                       # ZIP gerado para BotCity
```

---

## Pré-requisitos

- Python 3.11+
- Conta BotCity Maestro + DataPool criado
- Planilha em `dados_entrada/`
- Para web com Playwright: `python -m playwright install chromium`
- Para web com Selenium: Chrome instalado (usa `webdriver-manager`)

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
```

### Dependências principais

| Pacote | Uso |
|--------|-----|
| `botcity-maestro-sdk` | Maestro, DataPool, artefatos, finish task |
| `python-dotenv` | `.env` |
| `pandas` / `openpyxl` | Planilha |
| `playwright` | Automação web (opção A) |
| `selenium` + `webdriver-manager` | Automação web (opção B) |
| `pytest` | Testes |

---

## Configuração (`.env`)

```powershell
Copy-Item .env.example .env
```

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
| `WEB_AUTOMATION_DRIVER` | **`playwright`** ou **`selenium`** | `playwright` |
| `WEB_AUTOMATION_URL` | URL http(s) **ou** caminho relativo | `html/login(1).html` |
| `PLAYWRIGHT_HEADLESS` | Headless Playwright | `false` |
| `PLAYWRIGHT_AUTO_INSTALL` | Instala Chromium se faltar | `true` |
| `SELENIUM_HEADLESS` | Headless Selenium | `false` |
| `WEB_USUARIO` / `WEB_SENHA` | Login do HTML (se Vault off) | `usuario.teste` |

> **Nunca** versione o `.env` com segredos (já está no `.gitignore`).

### Escolher Playwright ou Selenium

```env
WEB_AUTOMATION_ENABLED=true
WEB_AUTOMATION_DRIVER=playwright   # ou: selenium
WEB_AUTOMATION_URL=file:///C:/Users/Turma01/Downloads/conferencia-lotes-qualidade/html/login%281%29.html
```

O orquestrador em `src/web/orchestrator.py` lê `WEB_AUTOMATION_DRIVER` e chama o runner correspondente.

`WEB_AUTOMATION_URL` aceita caminho relativo ao projeto (convertido em `file://`), o que mantém o bot portável entre máquinas e no Runner.

### Erro "Executable doesn't exist" (Playwright)

Significa que o Chromium do Playwright não está instalado naquela máquina. Com `PLAYWRIGHT_AUTO_INSTALL=true` o bot instala sozinho na primeira execução. Para instalar manualmente:

```powershell
python -m playwright install chromium
```

---

## Planilha de entrada

Arquivo padrão: `dados_entrada/inspecao_lotes_dia.xlsx`

| Aba | Função |
|-----|--------|
| `Inspecao_14_06_2026` | Dados enviados ao DataPool |
| `Base_Referencia` | Lotes oficiais |
| `Formulario_Analise` | Análise manual (auxiliar) |

**Aba de inspeção** (linhas 1–2 = título/metadados; linha 3 = cabeçalho):

| Campo | Obrigatório |
|-------|-------------|
| `lote_id` | sim |
| `produto` | sim |
| `linha` | sim |
| `turno` | sim |
| `status` | sim |
| `responsavel` | sim |
| `data` | sim |
| `observacao` | não (obrigatória se REPROVADO/NOK) |

Exemplo de `lote_id`: `LG-2026-00101`.

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

Há também validação de estrutura da planilha (`lote_id`, `produto`, `linha`, `turno`, `status`, `responsavel`).

---

## Como executar

### Local — fluxo completo

```powershell
# Com Maestro + (opcional) popular fila
$env:RUN_DISPATCHER = "true"
python bot.py

# Só performer / web (sem popular fila)
python bot.py
```

### Local — só HTML (sem Maestro)

```powershell
$env:PYTHONPATH = (Get-Location).Path
$env:MAESTRO_ENABLED = "false"
python bot.py
```

Fluxo web esperado:

1. Abre `login(1).html`
2. Preenche usuário/senha → **Entrar**
3. Redireciona para `lote-teste.html`
4. Preenche lote, produto e status → **Processar Lote**
5. Valida mensagem de sucesso e grava snapshot em `logs/`

### Popular só o DataPool

```powershell
python -m src.dispatcher
```

---

## Subir no BotCity Maestro

O Runner exige o arquivo **`bot.py`** na raiz do ZIP ([documentação](https://documentation.botcity.dev/tutorials/custom-automations/python-custom/)).

1. Gerar o pacote:

```powershell
python pack_botcity.py
```

Saída: `dist/conferencia-lotes-botcity.zip` (sem `.env`, sem `.venv`, sem planilha).

2. No Maestro: **Easy Deploy** → enviar o ZIP → tecnologia **Python**.
3. Entry point: `bot.py`.

O `.env` **não** vai no ZIP (contém segredos). Para o bot funcionar no Runner, a configuração vem em três níveis, do menor para o maior prioridade:

1. `.env.botcity` — embarcado no ZIP, sem segredos (define `WEB_AUTOMATION_ENABLED=true`, DataPool, driver, HTML)
2. `.env` — se existir na máquina do Runner
3. **Parâmetros da task** no Orchestrator — sobrepõem tudo

Ou seja, para trocar de driver sem novo deploy, basta criar um parâmetro na task:

| Parâmetro | Valor |
|-----------|-------|
| `WEB_AUTOMATION_DRIVER` | `selenium` |
| `PLAYWRIGHT_HEADLESS` | `true` |
| `DATA_POOL_NAME` | outro DataPool |

As páginas de `html/` vão dentro do ZIP, então `WEB_AUTOMATION_URL=html/login(1).html` funciona no Runner sem ajuste.

No Runner, a autenticação usa `BotMaestroSDK.from_sys_args()`. Localmente, usa `MAESTRO_SERVER_URL` + `MAESTRO_LOGIN` + `MAESTRO_API_KEY`.

---

## Fluxo de execução (detalhe)

1. `Config.carregar()` lê o `.env`
2. Conecta no Maestro (Runner ou login local)
3. Se `VAULT_ENABLED=true`, busca credencial
4. Se `RUN_DISPATCHER=true`, popula o DataPool a partir de `INPUT_FILE`
5. Consome `DATA_POOL_NAME` e valida cada item
6. Se `WEB_AUTOMATION_ENABLED=true`, executa Playwright ou Selenium
7. Grava `logs/resumo_execucao.json`, publica artefato e finaliza a task

Códigos de saída: `0` sucesso · `1` erro crítico.

---

## Saídas

| Arquivo | Conteúdo |
|---------|----------|
| `logs/execucao.log` | Log da execução |
| `logs/resumo_execucao.json` | Resumo (aprovados, reprovados, web) |
| `logs/screenshots/*.png` | Screenshots de login / sucesso / erro |

### Result Files (Maestro Artifacts)

Com `SCREENSHOT_ENABLED=true` e `UPLOAD_ARTIFACTS=true`, ao rodar **via Runner** (com `task_id`), o bot envia:

- `resumo_execucao.json`
- cada PNG de `logs/screenshots/`

via `maestro.post_artifact(...)` — visíveis em **Result Files** no Orchestrator:

https://documentation.botcity.dev/maestro/maestro-sdk/result-files/

```env
SCREENSHOT_ENABLED=true
UPLOAD_ARTIFACTS=true
```

Em execução local sem `task_id`, os PNGs ficam só em disco.

---

## Segurança e Vault

Com `VAULT_ENABLED=true`, `vault_client.py` busca a credencial `CREDENTIAL_LABEL` no Maestro (chaves `usuario`/`senha` ou `login`/`password`). Com Vault desligado, usa `WEB_USUARIO` / `WEB_SENHA`.

- `.env` fora do Git e do ZIP
- Logs nunca devem imprimir a senha

---

## Docker

```bash
docker compose up --build
# ou
docker build -t conferencia-lotes .
docker run --env-file .env -v ./dados_entrada:/app/dados_entrada:ro conferencia-lotes
```

O container executa `python bot.py`.

---

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11+ | Runtime |
| BotCity Maestro SDK | DataPool, tasks, artefatos |
| Playwright / Selenium | Automação web (escolha via `.env`) |
| pandas / openpyxl | Planilhas |
| python-dotenv | Configuração |
| Docker / GitHub Actions | Empacotamento e CI |

---

## Repositório

**https://github.com/VictorFLimax/conferencia-lotes-qualidade**

Desenvolvido por: **Victor**, **André**, **Gustavo** e **Mouriem**.
