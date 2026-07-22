# Conferência de Lotes — Qualidade

Bot de automação em Python para **conferência e auditoria de lotes de qualidade**, integrado ao [BotCity Maestro](https://botcity.dev/).

O fluxo lê uma planilha Excel, alimenta uma fila (DataPool), valida cada lote contra regras de negócio e gera relatórios de divergências e de execução.

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

Este projeto automatiza a conferência de lotes industriais/qualidade: compara dados de entrada com uma base de referência, aplica regras de negócio (RN01–RN07) e orquestra tudo no Maestro no padrão **Dispatcher → DataPool → Performer**.

### O que o bot faz

1. Lê a planilha de entrada em `dados_entrada/`
2. Envia cada linha para o DataPool do Maestro (**Dispatcher**)
3. Consome a fila item a item (**Performer**)
4. Valida o lote na base de referência com as regras RN01–RN07
5. Atualiza o status de cada item (`SUCCESS` / `ERROR`)
6. Gera relatório Excel de divergências (quando houver reprovações)
7. Grava resumo JSON da execução e publica artefato no Maestro
8. Finaliza a task com status e métricas

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
│ Relatório Excel │◀────│    Performer     │◀────│  Consumo fila   │
│ + JSON execução │     │  (valida lotes)  │     │                 │
└─────────────────┘     └────────┬─────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ Base Referência  │
                        │ + Regras RN01-07 │
                        └──────────────────┘
```

---

## Estrutura do projeto

```
conferencia-lotes-qualidade/
├── src/
│   ├── __init__.py          # Pacote do bot
│   ├── main.py              # Ponto de entrada — Maestro, fila e relatório
│   ├── config.py            # Variáveis de ambiente (.env)
│   ├── dispatcher.py        # Lê Excel e popula o DataPool
│   ├── bot.py               # Performer — processa cada item da fila
│   ├── validacao.py         # Regras de negócio (RN01–RN07) e modelos
│   ├── base_referencia.py   # Consulta à base de referência (mock)
│   ├── relatorio.py         # Geração do Excel de divergências
│   ├── vault_client.py      # Credenciais via Vault do Maestro
│   └── logger.py            # Logger estruturado em JSON
├── dados_entrada/           # Planilhas de entrada (.xlsx)
├── data/samples/            # Amostras / dados de exemplo
├── logs/                    # Logs, JSON e Excel de saída
├── .github/
│   ├── workflows/ci.yml     # CI (Python 3.11)
│   └── pull_request_template.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Regras de negócio

| Código | Descrição | Status |
|--------|-----------|--------|
| **RN01** | Lote deve existir na base de referência | Implementada |
| **RN02** | Código do produto deve corresponder à base | Implementada |
| **RN03** | Quantidade deve ser igual à da base | Implementada |
| **RN04** | Datas de fabricação/validade válidas | Preparada (stub) |
| **RN05** | Status permitido: `APROVADO`, `REPROVADO` ou `EM_ANALISE` | Implementada |
| **RN06** | Lote não pode estar vencido | Preparada (stub) |
| **RN07** | Campos obrigatórios preenchidos | Preparada (stub) |

Há também validação auxiliar de **estrutura da planilha** e **campos obrigatórios** (`valida_estrutura`, `valida_campos_obrigatorios`) para colunas como `lote_id`, `produto`, `linha`, `turno`, `status`, `responsavel`.

---

## Pré-requisitos

- **Python** 3.11+
- Conta e **API Key** no BotCity Maestro (quando `MAESTRO_ENABLED=true`)
- DataPool criado no Maestro (ex.: `FilaAuditoriaLotes` / `FilaConferenciaLotes`)
- Planilha de entrada no formato esperado (ver seção abaixo)

---

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/VictorFLimax/conferencia-lotes-qualidade.git
cd conferencia-lotes-qualidade

# Criar ambiente virtual (recomendado)
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### Dependências (`requirements.txt`)

| Pacote | Uso |
|--------|-----|
| `python-dotenv` | Carregar variáveis do `.env` |
| `botcity-maestro-sdk` | Maestro, DataPool, alertas, artefatos |
| `python-json-logger` | Logs estruturados em JSON |

O código também utiliza **pandas** e **openpyxl** para ler/escrever Excel (dispatcher e relatório). Instale-os se ainda não estiverem no ambiente:

```bash
pip install pandas openpyxl
```

---

## Configuração

1. Copie o exemplo de ambiente:

```bash
cp .env.example .env
```

No Windows (PowerShell):

```powershell
Copy-Item .env.example .env
```

2. Preencha o `.env`:

| Variável | Descrição | Exemplo / padrão |
|----------|-----------|------------------|
| `MAESTRO_ENABLED` | Liga integração com o Maestro | `true` |
| `VAULT_ENABLED` | Usa Vault para credenciais | `true` |
| `MAESTRO_SERVER_URL` | URL do servidor Maestro | `https://maestro.botcity.dev` |
| `MAESTRO_API_KEY` | Chave de API | *(sua key)* |
| `DATA_POOL_NAME` | Nome da fila no Maestro | `FilaAuditoriaLotes_Eq_AGMV` |
| `CREDENTIAL_LABEL` | Label da credencial no Vault | `credencial_erp_Eq_AGMV` |
| `INPUT_FOLDER` | Pasta de entrada (Compose) | `dados_entrada` |
| `LOG_FILE` | Caminho do log | `logs/execucao.log` |
| `CAMINHO_PLANILHA_ENTRADA` | Planilha de entrada | `dados_entrada/planilha_lotes.xlsx` |
| `CAMINHO_SAIDA_RELATORIO` | Excel de divergências | `logs/divergencias.xlsx` |
| `CAMINHO_BASE_REFERENCIA` | Base externa (opcional) | *(vazio = mock)* |
| `LOG_LEVEL` | Nível de log | `INFO` |
| `EXECUTION_ID` / `BOT_ID` | Contexto do logger JSON | `local-dev` / `bot-test` |

> **Nunca** versione o arquivo `.env` com credenciais reais (já está no `.gitignore`).

---

## Formato da planilha de entrada

Coloque o arquivo Excel em `dados_entrada/` (padrão: `planilha_lotes.xlsx`, ou o caminho de `CAMINHO_PLANILHA_ENTRADA`).

Colunas usadas pelo **Dispatcher** ao popular a fila:

| Coluna | Descrição |
|--------|-----------|
| `numero_lote` | Identificador do lote |
| `codigo_produto` | Código do produto |
| `quantidade` | Quantidade do lote |
| `data_fabricacao` | Data de fabricação |
| `data_validade` | Data de validade |
| `status` | Status do lote |

Cada item também recebe `linha_original` (número da linha na planilha).

---

## Como executar

### Localmente

```bash
python -m src.main
```

### Com Docker Compose

```bash
# Configure o .env antes
docker compose up --build
```

O Compose monta `dados_entrada/` (somente leitura) e persiste logs no volume `auditor-bot-logs`.

### Somente Docker

```bash
docker build -t conferencia-lotes .
docker run --env-file .env -v ./dados_entrada:/app/dados_entrada:ro conferencia-lotes
```

---

## Fluxo de execução

1. **Config** — `Config.carregar()` lê o `.env`
2. **Login Maestro** — autentica se `MAESTRO_ENABLED=true`
3. **Dispatcher** — lê o Excel e cria itens no DataPool
4. **Loop Performer** — para cada item:
   - Converte `fields` → `RegistroLote`
   - Consulta `BaseReferencia`
   - Aplica RN01–RN07
   - Atualiza o item no DataPool (`APROVADO` / `REPROVADO` ou erro)
5. **Relatório** — se houver erros, gera `logs/divergencias.xlsx`
6. **Finalização** — grava `logs/relatorio_execucao.json`, publica artefato e finaliza a task

Códigos de saída:

- `0` — execução sem erro crítico
- `1` — planilha ausente ou erro crítico

---

## Saídas geradas

| Arquivo | Conteúdo |
|---------|----------|
| `logs/execucao.log` | Log detalhado da execução |
| `logs/relatorio_execucao.json` | Resumo (início/fim, sucessos, erros) |
| `logs/divergencias.xlsx` | Divergências por lote/regra (se houver reprovações) |

No Maestro, o JSON também é enviado como artefato `Relatorio_Execucao.json`.

Colunas do Excel de divergências: `numero_lote`, `codigo_produto`, `regra`, `mensagem`, `valor_esperado`, `valor_encontrado`.

---

## Base de referência

Por padrão, `BaseReferencia` usa um **mock em memória**:

| Lote | Produto | Quantidade | Status |
|------|---------|------------|--------|
| `LOTE-001` | `PROD-A` | 100.0 | `APROVADO` |
| `LOTE-002` | `PROD-B` | 250.0 | `APROVADO` |

Se `CAMINHO_BASE_REFERENCIA` for definido, a consulta via arquivo está prevista, mas ainda **não implementada** (`NotImplementedError`).

---

## Segurança e Vault

O módulo `vault_client.py` obtém credenciais do Vault do Maestro quando `VAULT_ENABLED=true`. Com Vault desligado, usa credenciais fictícias para teste local.

Boas práticas do projeto:

- Usuário **não-root** no container Docker
- `.env` e credenciais no `.gitignore` / `.dockerignore`
- Logs devem expor apenas o usuário — **nunca a senha**

---

## Logging

- Em `main.py`: log em arquivo (`logs/execucao.log`) + console
- Em `logger.py`: logger estruturado JSON (`python-json-logger`) com `execution_id` e `bot_id`

---

## CI / Contribuição

O workflow GitHub Actions (`.github/workflows/ci.yml`) roda em push/PR para `master` e `develop`:

1. Checkout do código  
2. Setup Python 3.11  
3. Instalação de `requirements.txt`

Use o template de Pull Request (`.github/pull_request_template.md`). Checklist inclui tipagem, regras RN01–RN07, testes, cobertura (meta **80%** em `src/`) e atualização do README quando necessário.

Branches principais observadas no repositório: `main` / `master`, `develop`.

---

## Stack

| Tecnologia | Uso |
|------------|-----|
| Python 3.11 | Runtime |
| BotCity Maestro SDK | Orquestração, DataPool, alertas, artefatos |
| pandas / openpyxl | Planilhas de entrada e relatório |
| python-dotenv | Configuração |
| python-json-logger | Logs JSON |
| Docker / Compose | Empacotamento e execução |
| GitHub Actions | CI |

---

## Repositório

Todo o código deste projeto está em:

**https://github.com/VictorFLimax/conferencia-lotes-qualidade**

Desenvolvido pela equipe: **Victor**, **André**, **Gustavo** e **Mouriem**.

Para dúvidas, issues ou melhorias, abra uma issue ou pull request nesse repositório.
