# ARQUITETURA TÉCNICA DO PIPELINE MULTI-BOT HÍBRIDO
## Diagramas Mermaid: Sequência, Decisão RPA+ML, Resiliência e Concorrência
**LG Electronics do Brasil — AX Academy | Governança The DX Way**

---

## 1. Diagrama de Sequência do Pipeline Multi-Bot Híbrido

O diagrama abaixo ilustra o ciclo de vida completo de uma execução regular, demonstrando as chamadas entre o Orquestrador, o LockManager, os 5 bots especializados e os sistemas legados/mocks.

```mermaid
sequenceDiagram
    autonumber
    participant OE as Orchestrator Engine (Smart Office)
    participant LM as LockManager (Mutex Sessao)
    participant B1 as Bot 01: Desktop Collector
    participant GUI as App Desktop Legado (Tkinter)
    participant B2 as Bot 02: Web Collector
    participant B2B as Portal Web Fornecedores
    participant B3 as Bot 03: Consolidator RN
    participant DLQ as Dead Letter Queue
    participant B4 as Bot 04: ML Classifier
    participant MLS as Servico Mock ML (FastAPI)
    participant B5 as Bot 05: Notifier & Reporter

    Note over OE: Disparo do Pipeline Diário (Prioridades Definidas)
    
    %% Coleta Desktop
    OE->>B1: Iniciar Coleta Desktop (Prioridade: HIGH)
    B1->>LM: acquire() - Solicitar Mutex de Sessão Gráfica
    LM-->>B1: Lock Concedido (Grava PID + Runner ID)
    B1->>GUI: Disparar GUI e Exportar Dados de Estoque
    GUI-->>B1: Dados de Estoque Físico Exportados
    B1->>LM: release() - Liberar Sessão Gráfica
    B1-->>OE: Retorno: 7 Itens de Estoque Coletados

    %% Coleta Web
    OE->>B2: Iniciar Coleta Web (Prioridade: MEDIUM)
    B2->>B2B: GET /pedidos (com Timeout de 5s e Retry)
    B2B-->>B2: Lista de Pedidos de Compra B2B
    B2-->>OE: Retorno: Pedidos de Compra Coletados

    %% Consolidação e Regras de Negócio
    OE->>B3: Executar Consolidação (Verifica Deadline dos Predecessores)
    loop Para cada Item
        B3->>B3: Validar Integridade do Dado (RN04)
        alt Dado Corrompido / NaN
            B3->>DLQ: enqueue(Item Corrompido) [Isolado]
        else Dado Sadio
            B3->>B3: Aplicar RN01 (OK), RN02 (Insuficiente) ou RN03 (Sem Pedido)
        end
    end
    B3-->>OE: Itens Consolidados + Total DLQ

    %% Enriquecimento ML
    OE->>B4: Enriquecer Divergências com Causa Provável
    loop Para cada Item com Divergência
        alt ML_ENABLED == true
            B4->>MLS: POST /predict/divergencia
            alt Sucesso e Confiança >= 0.75
                MLS-->>B4: Categoria + Confiança
                B4->>B4: Origem: ML_HYBRID
            else Falha / Timeout / Confiança < 0.75
                B4->>B4: Origem: FALLBACK_DETERMINISTICO
            end
        else ML Desativado via Feature Flag
            B4->>B4: Origem: FALLBACK_DETERMINISTICO
        end
    end
    B4-->>OE: Itens Enriquecidos

    %% Relatório e Alerta
    OE->>B5: Gerar Relatórios e Despachar Notificação
    B5->>B5: Gerar relatorio_auditoria.csv e .xlsx
    alt Canal Primário Telegram Disponível
        B5->>B5: Disparar Mensagem Telegram
    else Falha no Telegram (Token Inválido / Rede)
        B5->>B5: Acionar Fallback para Canal Secundário (Email/Log)
    end
    B5-->>OE: Pipeline Finalizado com Rastreabilidade Total
```

---

## 2. Diagrama de Fluxo de Decisão RPA + ML

Ilustra o **Princípio Cardeal**: o status de negócio é 100% determinístico; o Machine Learning enriquece exclusivamente a causa provável, com degradação elegante e sem jamais interromper o processo.

```mermaid
flowchart TD
    Start([Item de Estoque + Pedido Recebidos]) --> Validacao{Dado Íntegro?\n(Código não-nulo, Qtd >= 0)}
    
    %% Validação de Dados
    Validacao -->|Não: NaN / Corrompido| DisparaDLQ[Lança ItemDataFailure]
    DisparaDLQ --> EnfileiraDLQ[Encaminhar para Dead Letter Queue\nIsolamento Seguro sem Quebra]
    EnfileiraDLQ --> EndItem([Próximo Item])

    %% Regras Determinísticas
    Validacao -->|Sim| ComparaQtd{Estoque Físico vs\nQtd Solicitada}
    ComparaQtd -->|Estoque == Solicitado| RN01[RN01: STATUS = OK\nSem divergência]
    ComparaQtd -->|Estoque < Solicitado| RN02[RN02: STATUS = DIVERGENCIA_ESTOQUE_INSUFICIENTE]
    ComparaQtd -->|Sem Pedido B2B| RN03[RN03: STATUS = DIVERGENCIA_SEM_PEDIDO]

    %% Ramificação de Decisão
    RN01 --> SemML[origem_decisao = REGRA_DETERMINISTICA\nconfianca_ml = 1.0\ncausa = CONFORME_SEM_DIVERGENCIA]
    SemML --> GeraLinhaAudit[Grava Linha no Relatório de Auditoria]

    RN02 --> AvaliaML{ML_ENABLED == true?}
    RN03 --> AvaliaML

    %% Decisão Híbrida RPA+ML
    AvaliaML -->|False| FallbackFlag[origem_decisao = FALLBACK_DETERMINISTICO\nconfianca_ml = 0.0\ncausa = REVISAO_MANUAL_REGRA_PADRAO]
    AvaliaML -->|True| ChamaML[Chamar API /predict/divergencia\nTimeout Estrito: 3.0s]

    ChamaML --> RespostaML{Status HTTP 200 e\nConfiança >= 0.75?}
    RespostaML -->|Sim| MLSucesso[origem_decisao = ML_HYBRID\nconfianca_ml = valor_inferido\ncausa = categoria_modelo]
    RespostaML -->|Não: 503 / Timeout / Baixa Conf| FallbackML[origem_decisao = FALLBACK_DETERMINISTICO\nconfianca_ml = 0.0\ncausa = REVISAO_MANUAL_REGRA_PADRAO]

    FallbackFlag --> GeraLinhaAudit
    MLSucesso --> GeraLinhaAudit
    FallbackML --> GeraLinhaAudit
    GeraLinhaAudit --> EndItem
```

---

## 3. Diagrama de Estados da Resiliência (Retry → Fallback → Dead Letter)

Demonstra a separação estrita de falhas de infraestrutura transitórias versus falhas de dados irrecuperáveis.

```mermaid
stateDiagram-v2
    [*] --> OperacaoIniciada: Executar Etapa

    state "Execução de Infraestrutura" as Infra {
        OperacaoIniciada --> TentativaExecucao
        TentativaExecucao --> SucessoInfra: Resposta 200 / GUI OK
        TentativaExecucao --> FalhaInfra: Crash GUI / Timeout HTTP / 503
        
        FalhaInfra --> VerificaRetry: Falha Transitória?
        VerificaRetry --> EsperaBackoff: Tentativas < MaxRetries
        EsperaBackoff --> TentativaExecucao: Backoff Exponencial
        
        VerificaRetry --> AtivaFallback: Tentativas Esgotadas
        AtivaFallback --> ModoDegradado: Marca Lote DEGRADED / Alerta WARN
    }

    state "Validação de Dados do Item" as Dados {
        SucessoInfra --> ValidaItem: Item Processado
        ValidaItem --> ItemValido: Atende RN01-RN03
        ItemValido --> FinalizadoSucesso: Relatório Final
        
        ValidaItem --> ItemInvalido: RN04 (NaN / Corrompido)
        ItemInvalido --> DeadLetterQueue: Isolado na DLQ com Auditoria
        DeadLetterQueue --> AlertaCritico: Emite Alerta CRITICAL
        DeadLetterQueue --> ProximoItem: Pipeline Não Trava
    }

    ModoDegradado --> FinalizadoSucesso: Continua com Dados Parciais
    ProximoItem --> FinalizadoSucesso
    FinalizadoSucesso --> [*]
```

---

## 4. Diagrama de Coexistência de Runners na Migração (BotCity vs Smart Office)

Demonstra como o mecanismo de `LockManager` impede fisicamente a colisão de sessão de tela durante a fase de transição de orquestradores.

```mermaid
flowchart TD
    subgraph Orquestradores["Camada de Agendamento"]
        OrqA["BotCity Orchestrator (Legado)\nDisparo: 06:00 AM"]
        OrqB["Smart Office (Novo Pipeline)\nDisparo: 06:45 AM (ou acionamento concorrente)"]
    end

    subgraph MaquinaExecucao["Estação / VM com Sessão Gráfica Dedicada"]
        RunnerA["BotCity Runner"]
        RunnerB["Smart Office Runner"]
        
        subgraph MutexFile["LockManager (runner_desktop_session.lock)"]
            LockState[("Arquivo de Lock\nPID | Runner ID | Timestamp")]
        end
    end

    OrqA -->|Trigger| RunnerA
    OrqB -->|Trigger| RunnerB

    RunnerA -->|1. Solicita Lock| MutexFile
    MutexFile -->|Lock Livre| AdquireA[RunnerA Adquire Mutex\nGrava PID e Runner ID]
    AdquireA --> AbreTelaA[Abre e Controla 'LG Estoque Legado v4.2']

    RunnerB -->|2. Solicita Lock Simultâneo| MutexFile
    MutexFile -->|Lock em Uso por RunnerA| NegadoB{Idade do Lock < 60s?}
    
    NegadoB -->|Sim: Lock Ativo| ErroConcorrencia[Lança RunnerLockAcquisitionError\nRunnerB Aborta Preventivamente\nNenhum Clique Vaza na Tela]
    NegadoB -->|Não: Lock Órfão / Stale| LimpaOrfao[Limpa Arquivo Expirado e Adquire]

    AbreTelaA --> FechaTelaA[Finaliza Coleta e Fecha Janela]
    FechaTelaA --> LiberaLock[RunnerA Libera Mutex]
    LiberaLock -.->|Arquivo Livre| RunnerB
```
