# Changelog

Todas as mudanças relevantes deste repositório são documentadas neste arquivo.

## [1.1.0] — 2026-08-19

### Adicionado (Aula 24)

- Camada `src/operational_indicators.py` com os 10 indicadores operacionais e `_percentual()` protegida contra divisão por zero.
- Campo `regra_aplicada` em `RegistroValidado` (fonte única do indicador 6 e da aba Ranking de Regras).
- Excel `relatorio_conferencia_lotes.xlsx` expandido para 8 abas essenciais: Resumo (dashboard com 10 indicadores + gráficos nativos), Todos, Válidos, Divergências, Ambíguos, Erros de Entrada, Ranking de Regras e Dicionário.
- `resumo_executivo.md` gerado a partir do mesmo objeto `OperationalIndicators`.
- Entrypoint `main.py` do Pipeline B (não confundir com `src/main.py` do Maestro).
- Testes `tests/unit/test_operational_indicators.py` e `tests/integration/test_relatorio_consolidado.py`.
- `PDD.md` com o fluxo de indicadores e resumo executivo.

### Corrigido

- Teste `test_main_block` do dispatcher (reexecução via `runpy` ignorava o mock).
- Referências a `html/login(1).html` na documentação; arquivos reais: `html/login.html` e `html/lote-teste.html`.
