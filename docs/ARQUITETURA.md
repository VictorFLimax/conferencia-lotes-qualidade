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
    rect rgb(240, 245, 255)
        Note over OE,GUI: Fase 1: Coleta Desktop com Exclusão Mútua
        OE->>B1: Iniciar Coleta Desktop (Prioridade: HIGH)
        B1->>LM: acquire() - Solicitar Mutex de Sessão Gráfica
        LM-->>B1: Lock Concedido (Grava PID + Runner ID)
        B1->>GUI: Disparar GUI e Exportar Dados de Estoque
        GUI-->>B1: Dados de Estoque Físico Exportados
        B1->>LM: release() - Liberar Sessão Gráfica
        B1-->>OE: Retorno: 7 Itens de Estoque Coletados
    end

    %% Coleta Web
    rect rgb(245, 250, 245)
        Note over OE,B2B: Fase 2: Coleta Web Resiliente
        OE->>B2: Iniciar Coleta Web (Prioridade: MEDIUM)
        B2->>B2B: GET /pedidos (com Timeout de 5s e Retry)
        B2B-->>B2: Lista de Pedidos de Compra B2B
        B2-->>OE: Retorno: Pedidos de Compra Coletados
    end

    %% Consolidação e Regras de Negócio
    rect rgb(255, 250, 240)
        Note over OE,DLQ: Fase 3: Consolidação e Triagem DLQ
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
    end

    %% Enriquecimento ML
    rect rgb(250, 245, 255)
        Note over OE,MLS: Fase 4: Classificação Híbrida RPA + ML
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
    end

    %% Relatório e Alerta
    rect rgb(245, 245, 250)
        Note over OE,B5: Fase 5: Notificação e Auditoria
        OE->>B5: Gerar Relatórios e Despachar Notificação
        B5->>B5: Gerar relatorio_auditoria.csv e .xlsx
        alt Canal Primário Telegram Disponível
            B5->>B5: Disparar Mensagem Telegram
        else Falha no Telegram (Token Inválido / Rede)
            B5->>B5: Acionar Fallback para Canal Secundário (Email/Log)
        end
        B5-->>OE: Pipeline Finalizado com Rastreabilidade Total
    end
```

---

## 2. Diagrama de Fluxo de Decisão RPA + ML

Ilustra o **Princípio Cardeal**: o status de negócio é 100% determinístico; o Machine Learning enriquece exclusivamente a causa provável, com degradação elegante e sem jamais interromper o processo.

```mermaid
flowchart TD
    %% Nós do Fluxo
    Start(["Item de Estoque + Pedido Recebidos"]) --> Validacao{"Dado Íntegro?<br/>(Código não-nulo, Qtd >= 0)"}
    
    %% Validação de Dados e DLQ
    Validacao -->|Não: NaN / Corrompido| DisparaDLQ["Lança ItemDataFailure"]
    DisparaDLQ --> EnfileiraDLQ["Encaminhar para Dead Letter Queue<br/>(Isolamento Seguro sem Quebra)"]
    EnfileiraDLQ --> EndItem(["Próximo Item"])

    %% Regras Determinísticas
    Validacao -->|Sim| ComparaQtd{"Estoque Físico vs<br/>Qtd Solicitada"}
    ComparaQtd -->|Estoque == Solicitado| RN01["RN01: STATUS = OK<br/>(Sem divergência)"]
    ComparaQtd -->|Estoque < Solicitado| RN02["RN02: STATUS = DIVERGENCIA_ESTOQUE_INSUFICIENTE"]
    ComparaQtd -->|Sem Pedido B2B| RN03["RN03: STATUS = DIVERGENCIA_SEM_PEDIDO"]

    %% Ramificação Sem Divergência
    RN01 --> SemML["origem_decisao = REGRA_DETERMINISTICA<br/>confianca_ml = 1.0<br/>causa = CONFORME_SEM_DIVERGENCIA"]
    SemML --> GeraLinhaAudit["Grava Linha no Relatório de Auditoria"]

    %% Ramificação com Divergência
    RN02 --> AvaliaML{"ML_ENABLED == true?"}
    RN03 --> AvaliaML

    %% Decisão Híbrida RPA + ML
    AvaliaML -->|False| FallbackFlag["origem_decisao = FALLBACK_DETERMINISTICO<br/>confianca_ml = 0.0<br/>causa = REVISAO_MANUAL_REGRA_PADRAO"]
    AvaliaML -->|True| ChamaML["Chamar API /predict/divergencia<br/>(Timeout Estrito: 3.0s)"]

    ChamaML --> RespostaML{"Status HTTP 200 e<br/>Confiança >= 0.75?"}
    RespostaML -->|Sim| MLSucesso["origem_decisao = ML_HYBRID<br/>confianca_ml = valor_inferido<br/>causa = categoria_modelo"]
    RespostaML -->|Não: 503 / Timeout / Baixa Conf| FallbackML["origem_decisao = FALLBACK_DETERMINISTICO<br/>confianca_ml = 0.0<br/>causa = REVISAO_MANUAL_REGRA_PADRAO"]

    FallbackFlag --> GeraLinhaAudit
    MLSucesso --> GeraLinhaAudit
    FallbackML --> GeraLinhaAudit
    GeraLinhaAudit --> EndItem

    %% Estilos de Destaque
    classDef startEnd fill:#2d3748,stroke:#1a202c,stroke-width:2px,color:#ffffff;
    classDef decision fill:#ebf8ff,stroke:#3182ce,stroke-width:2px,color:#2b6cb0;
    classDef success fill:#f0fff4,stroke:#38a169,stroke-width:2px,color:#22543d;
    classDef warning fill:#fffaf0,stroke:#dd6b20,stroke-width:2px,color:#7b341e;
    classDef danger fill:#fff5f5,stroke:#e53e3e,stroke-width:2px,color:#742a2a;
    classDef ml fill:#faf5ff,stroke:#805ad5,stroke-width:2px,color:#44337a;

    class Start,EndItem startEnd;
    class Validacao,ComparaQtd,AvaliaML,RespostaML decision;
    class RN01,SemML success;
    class RN02,RN03,FallbackFlag,FallbackML warning;
    class DisparaDLQ,EnfileiraDLQ danger;
    class ChamaML,MLSucesso ml;
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
        OrqA["BotCity Orchestrator (Legado)<br/>Disparo: 06:00 AM"]
        OrqB["Smart Office (Novo Pipeline)<br/>Disparo: 06:45 AM (ou acionamento concorrente)"]
    end

    subgraph MaquinaExecucao["Estação / VM com Sessão Gráfica Dedicada"]
        RunnerA["BotCity Runner"]
        RunnerB["Smart Office Runner"]
        
        subgraph MutexFile["LockManager (runner_desktop_session.lock)"]
            LockState[("Arquivo de Lock<br/>PID | Runner ID | Timestamp")]
        end
    end

    OrqA -->|Trigger| RunnerA
    OrqB -->|Trigger| RunnerB

    RunnerA -->|1. Solicita Lock| MutexFile
    MutexFile -->|Lock Livre| AdquireA["RunnerA Adquire Mutex<br/>(Grava PID e Runner ID)"]
    AdquireA --> AbreTelaA["Abre e Controla 'LG Estoque Legado v4.2'"]

    RunnerB -->|2. Solicita Lock Simultâneo| MutexFile
    MutexFile -->|Lock em Uso por RunnerA| NegadoB{"Idade do Lock < 60s?"}
    
    NegadoB -->|Sim: Lock Ativo| ErroConcorrencia["Lança RunnerLockAcquisitionError<br/>RunnerB Aborta Preventivamente<br/>(Nenhum clique vaza na tela)"]
    NegadoB -->|Não: Lock Órfão / Stale| LimpaOrfao["Limpa Arquivo Expirado e Adquire"]

    AbreTelaA --> FechaTelaA["Finaliza Coleta e Fecha Janela"]
    FechaTelaA --> LiberaLock["RunnerA Libera Mutex"]
    LiberaLock -.->|Arquivo Liberado| RunnerB

    %% Estilos
    classDef orq fill:#edf2f7,stroke:#4a5568,stroke-width:2px,color:#2d3748;
    classDef runner fill:#ebf8ff,stroke:#3182ce,stroke-width:2px,color:#2b6cb0;
    classDef lockBox fill:#fffaf0,stroke:#dd6b20,stroke-width:2px,color:#7b341e;
    classDef errorNode fill:#fff5f5,stroke:#e53e3e,stroke-width:2px,color:#742a2a;
    classDef successNode fill:#f0fff4,stroke:#38a169,stroke-width:2px,color:#22543d;

    class OrqA,OrqB orq;
    class RunnerA,RunnerB runner;
    class LockState,MutexFile lockBox;
    class ErroConcorrencia errorNode;
    class AdquireA,LiberaLock,LimpaOrfao successNode;
```
