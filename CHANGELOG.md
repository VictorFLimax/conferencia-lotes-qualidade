# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-07-08

### Adicionado

- Estrutura inicial do projeto (boilerplate).
- Módulo `src/config.py` para carregamento de variáveis de ambiente.
- Módulo `src/validacao.py` com assinaturas das regras RN01–RN07.
- Módulo `src/base_referencia.py` com mock de consulta à base de lotes.
- Módulo `src/relatorio.py` para geração de `divergencias.xlsx`.
- Entry point `poc.py`.
- Testes unitários iniciais em `tests/test_validacao.py`.
- Template de Pull Request em `.github/pull_request_template.md`.
- Documentação de instalação e execução no `README.md`.

[0.1.0]: https://github.com/org/conferencia-lotes-qualidade/releases/tag/v0.1.0
