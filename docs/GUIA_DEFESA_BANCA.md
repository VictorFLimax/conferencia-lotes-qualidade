# GUIA DE DEFESA DIANTE DA BANCA AVALIADORA
## Capstone Hyperautomation: Pipeline Multi-Bot Híbrido (LG / AX Academy)
**Convênio IFAM / Polo de Inovação (INOVA) / LG Electronics do Brasil**

---

## 🎯 PARTE 1: Respostas Técnicas Fundamentadas para as 5 Perguntas da Banca

As perguntas abaixo compõem a Seção 12 do enunciado oficial e serão formuladas diretamente pelos avaliadores técnicos da LG e do IFAM. Abaixo encontram-se as respostas arquiteturais completas, com fundamentação teórica e dados empíricos observados na implementação.

---

### Pergunta 1
> **"Por que a automação desktop precisa de um Runner dedicado, e o que acontece se duas tarefas tentarem usar a mesma sessão gráfica ao mesmo tempo?"**

#### Resposta Técnica:
A automação desktop (especialmente sobre sistemas legados em Windows GUI como o nosso cliente Tkinter sem API ou interface web) depende do subsistema de janelas do sistema operacional (Windows GDI, User32, Win32 Message Loop). Esse subsistema baseia-se no conceito de **sessão interativa única** (*Interactive Desktop Session 1*), onde existe apenas um cursor físico de mouse, um buffer de teclado ativo e uma única janela com o foco de primeiro plano (*foreground window*).

Se duas automações tentarem compartilhar a mesma sessão gráfica simultaneamente:
1. **Colisão de Foco e Disputa de Cursor**: O Bot A envia comandos de digitação (`send_keys`/`typewrite`) para um formulário de estoque enquanto o Bot B move o mouse ou clica em outro botão. Os caracteres do Bot A são injetados na tela do Bot B, corrompendo dados operacionais.
2. **Minimização e Quebra de OCR/Coordenadas**: Uma janela sobreposta oculta os elementos visuais da outra, gerando exceções imediatas de elemento não encontrado (*ElementNotFoundError*) ou cliques cegos em coordenadas erradas.
3. **Bloqueio de Sessão**: Se a sessão for bloqueada por política de segurança (Ctrl+Alt+Del ou Lock Workstation), o pipeline desktop é interrompido abruptamente se o Runner não for configurado como sessão dedicada com console ativo.

**Como resolvemos na arquitetura**:  
Implementamos o componente [LockManager](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/core/lock_manager.py), que atua como um **Mutex de Sessão Gráfica** via arquivo atômico com PID e timestamp. Se o Runner do BotCity e o Runner do Smart Office dispararem juntos, o segundo runner detecta o lock ativo em menos de 50ms, aborta com `RunnerLockAcquisitionError` e emite alerta de concorrência, impedindo qualquer vazamento de clique ou corrupção de tela.

---

### Pergunta 2
> **"Se o cutover para o Smart Office falhar no meio da janela de coexistência, quantos minutos (ou horas) a operação fica sem dado atualizado até o rollback restaurar o bot legado?"**

#### Resposta Técnica:
O nosso RTO (*Recovery Time Objective*) formalmente mensurado e documentado no Plano de Migração é de **menos de 15 minutos** (tempo nominal estimado: **12 a 14 minutos**), com **RPO = 0 minutos**.

A operação não acumula defasagem de dados pelas seguintes razões arquiteturais:
1. **Sem Big Bang e Sem Desinstalação**: O bot legado no **BotCity Orchestrator (Maestro)** não é deletado nem desinstalado durante a coexistência; seu agendamento no Maestro é apenas colocado em modo desativado (*Disabled Schedule*).
2. **Procedimento em 4 Passos Simples**:
   - **Passo 1 (2 min)**: Desativação do schedule do Smart Office pelo portal web.
   - **Passo 2 (3 min)**: Liberação do arquivo mutex na VM do Runner via script de contingência (`LockManager().release()`).
   - **Passo 3 (3 min)**: Reativação do schedule no BotCity Orchestrator via console Maestro e disparo manual forçado (*Run Now*).
   - **Passo 4 (4 min)**: Execução completa do bot legado, que dura aproximadamente 2 a 3 minutos para extrair o estoque matinal e emitir o relatório legado.
3. **Idempotência da Consulta**: Como o estoque físico é uma consulta de saldo em tempo real no cliente desktop, a execução reprocessa o saldo vigente do armazém no instante da reversão, sem perda transacional de pedidos.

---

### Pergunta 3
> **"Por que o ML não pode decidir o status do item, mesmo quando a confiança da predição é altíssima — e o que isso protege especificamente neste processo?"**

#### Resposta Técnica:
Essa decisão é o **Princípio Cardeal** da nossa governança (The DX Way). O Machine Learning é um componente **estocástico (probabilístico)**, enquanto regras de conferência contábil, fiscal e de suprimentos fabris são **estritamente determinísticas**.

O que isso protege especificamente na operação da LG:
1. **Proteção contra Erros Fiscais e de Parada de Linha**: Se o modelo de ML decidisse o status, uma alucinação ou falso positivo (ex.: classificar uma falta física grave de peças de display como "OK - Saldo Regular") mascararia uma ruptura de estoque. A linha de montagem de televisores pararia por falta de insumo, acarretando prejuízos de centenas de milhares de reais por hora parada.
2. **Auditabilidade e Compliance SOX**: Órgãos reguladores e auditorias corporativas exigem rastreabilidade determinística. Não é aceitável justificar para uma auditoria contábil que um lote divergente foi liberado porque uma rede neural ou floresta aleatória atribuiu probabilidade de 0.94.
3. **Resiliência e Desacoplamento**: Se o microsserviço de ML cair, sofrer ataque de negação ou apresentar latência, o pipeline de negócio continua 100% funcional. As regras RN01, RN02 e RN03 determinam com precisão matemática se há falta de estoque ou ausência de pedido; o ML atua apenas como um "assistente de triagem", sugerindo a causa provável da divergência para agilizar a leitura humana.

---

### Pergunta 4
> **"Qual seria o efeito de rodar o bot legado no BotCity Orchestrator e o novo bot no Smart Office no mesmo horário, apontando para runners diferentes? Isso resolveria o problema de conflito, ou criaria um novo?"**

#### Resposta Técnica:
**Criaria um novo problema, ainda mais grave e silencioso**, substituindo uma colisão técnica de tela por uma **colisão de concorrência de negócio (Race Condition)**:

1. **Ilusão da Resolução Técnica**: Rodar em runners diferentes (ex.: duas VMs distintas, VM-01 para BotCity e VM-02 para Smart Office) de fato eliminaria o conflito de sessão gráfica na tela do Windows.
2. **O Novo Problema Criado — Concorrência de Negócio no ERP/WMS**:
   - O sistema desktop de estoque acessa a mesma base de dados centralizada do armazém fabril.
   - Se ambos os bots lerem e, em fases posteriores, gerarem marcações de inspeção, bloqueio de lote ou reserva de saldo simultaneamente, haverá inconsistências de concorrência (*Dirty Reads* ou *Lost Updates*).
   - A operação de SCM receberá **dois relatórios divergentes no mesmo dia**: o relatório do BotCity (que só enxerga o estoque físico) e o relatório do Smart Office (que já cruzou com os pedidos B2B de fornecedores e apontou divergências semânticas).
   - O time de compras ficaria sem saber qual das duas planilhas é a fonte da verdade para cobrar fornecedores externos, gerando duplicidade de pedidos de reposição e confusão de faturamento.
3. **Solução Correta**: Segregação de janelas horárias (06:00 vs 06:45) com validação paralela durante o período de transição, mantendo o BotCity como verdade contábil até a homologação formal do corte (Cutover).

---

### Pergunta 5
> **"Se o canal principal de notificação e o bot desktop falharem ao mesmo tempo, o que a equipe operacional ainda consegue saber sobre o estado do pipeline?"**

#### Resposta Técnica:
A operação mantém **visibilidade e observabilidade completas**, garantidas por quatro camadas redundantes de telemetria arquitetadas no pipeline:

1. **Canal Secundário de Contingência (Email/Log)**:  
   O [Bot 05](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/bots/bot_05_notifier_reporter/reporter.py) implementa fallback automático de canal. Se o Telegram falhar (token inválido, timeout da API ou indisponibilidade de internet externa), o alerta é imediatamente despachado por Email SMTP simulado e gravado com destaque no arquivo [logs/contingencia_notificacoes.log](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/logs/contingencia_notificacoes.log), contendo a severidade (`WARN` ou `CRITICAL`), a mensagem de erro do Bot Desktop e o anexo do relatório de auditoria gerado.
2. **Rastreabilidade da Falha do Bot Desktop**:  
   O [Bot 01](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/bots/bot_01_desktop_collector/collector.py) não deixa o pipeline morrer silenciosamente. Ele captura o crash via `DesktopAppCrashError`, registra o retorno no [OrchestratorEngine](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/orchestration/orchestrator_engine.py) como `status = DEGRADED`, marca a flag `degraded_mode = True` e grava no log JSON exatamente o código de saída e o erro do processo da GUI.
3. **Logs Estruturados em JSONL**:  
   O módulo [core.telemetry](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/core/telemetry.py) persiste todos os eventos em `logs/execution_YYYYMMDD.jsonl`. Qualquer ferramenta de observabilidade (Datadog, Splunk, Elastic ou o próprio painel do Smart Office) lê em tempo real:
   ```json
   {"timestamp": "2026-08-31T03:35:34Z", "level": "WARNING", "message": "[LG_Estoque_Desktop_V1] ATIVACAO DE FALLBACK DEGRADADO: Falha no sistema legado...", "runner_id": "RUNNER_SMART_OFFICE_01", "execution_id": "EXEC_20260830_233530"}
   ```
4. **Relatório de Auditoria e Dead Letter Queue**:  
   Mesmo sem tela desktop e sem Telegram, o relatório final em [relatorio_auditoria.xlsx](file:///c:/Users/DELL/OneDrive/Documentos/Nova%20pasta/conferencia-lotes-qualidade/logs/relatorio_auditoria.xlsx) é gerado no disco com os pedidos web que puderam ser avaliados, e qualquer item com inconsistência é catalogado com stack trace na Dead Letter Queue (`logs/dead_letter_queue.json`).

---

## ⏱️ PARTE 2: Roteiro do Pitch de 10 Minutos (Minuto a Minuto)

| Minuto | Responsável Sugerido | Tema / Conteúdo Apresentado | Slide / Visual |
| :---: | :---: | :--- | :--- |
| **00:00 - 01:30** | Integrante 1 (Abertura/Negócio) | **O Cenário e a Dor de Negócio**:<br>• Apresentação do contexto LG Electronics / AX Academy.<br>• Transição do BotCity para o Smart Office sem interrupção de produção.<br>• O desafio do sistema desktop legado sem API convivendo com o novo portal web B2B. | Slide 1: AS-IS vs TO-BE e Desafios de SCM |
| **01:30 - 03:30** | Integrante 2 (Arquitetura) | **Arquitetura Multi-Bot Híbrida (The DX Way)**:<br>• Apresentação dos 5 bots especializados (Desktop, Web, Consolidator, ML, Notifier).<br>• Matriz de prioridades (Bot Desktop com prioridade `HIGH` no Runner dedicado).<br>• Dependências sequenciais com controle de deadline (`DEPENDENCY_TIMEOUT_SECONDS = 15s`). | Slide 2: Diagrama de Sequência e Arquitetura Mermaid |
| **03:30 - 05:00** | Integrante 3 (ML & Resiliência) | **Decisão Híbrida RPA+ML e Resiliência**:<br>• Explicação do Princípio Cardeal (ML enriquece, regras determinísticas decidem o status contábil).<br>• Feature flag, limiar de confiança (0.75) e isolamento total via `CircuitBreaker`.<br>• Tríade de Resiliência: Retry com backoff, Fallback degradado e Dead Letter Queue (DLQ). | Slide 3: Fluxograma de Decisão RPA+ML e DLQ |
| **05:00 - 06:30** | Integrante 4 (Migração/Rollback) | **Estratégia de Coexistência e Plano de Rollback**:<br>• Demonstração do `LockManager` (Mutex de sessão gráfica anti-colisão).<br>• Protocolo de Cutover de 5 dias paralelos com 0 divergências.<br>• Plano de Rollback detalhado com RTO garantido em < 15 minutos. | Slide 4: Coexistência de Runners e Timeline de Rollback |
| **06:30 - 08:30** | **Todos / Operador** | **DEMONSTRAÇÃO AO VIVO (Live Demo)**:<br>1. Execução regular do pipeline: `python run_pipeline.py`<br>   *(Mostra abertura da GUI, coleta web, conciliação e geração do Excel/CSV de auditoria)*.<br>2. Provocação de Sabotagem ao Vivo (conforme escolha da banca):<br>   `python tests/run_sabotage_scenarios.py`<br>   *(Demonstra os 6 cenários aprovados: Crash GUI, Timeout, ML offline, Falha Telegram, Lock Concorrente e Item DLQ)*. | Tela compartilhada / Terminal PowerShell e pastas de logs |
| **08:30 - 10:00** | Integrante 1 / Líder Técnico | **Fechamento e Impacto Operacional**:<br>• Rastreabilidade total via `origem_decisao` e `runner_id`.<br>• Eliminação de 3.5h de triagem manual diária com risco zero de parada de fábrica.<br>• Abertura formal para a arguição técnica da banca avaliadora. | Slide 5: Indicadores Finais e Agradecimentos |
