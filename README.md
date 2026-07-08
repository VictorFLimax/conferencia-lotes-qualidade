# Bot de Conferência de Lotes

Bot em Python para conferência automatizada de lotes de qualidade, com arquitetura modular preparada para regras de negócio (RN01–RN07), geração de relatórios e cobertura de testes.

## Pré-requisitos

- Python 3.11 ou superior
- pip

## Instalação

1. Clone o repositório:

   ```bash
   git clone <url-do-repositorio>
   cd conferencia-lotes-qualidade
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # ou: venv\Scripts\activate  (Windows)
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:

   ```bash
   cp .env.example .env
   ```

   Edite o arquivo `.env` conforme necessário.

5. Coloque a planilha de amostra (25 registros) em `data/samples/planilha_lotes.xlsx`.

## Execução

Com o ambiente virtual ativo e o `.env` configurado:

```bash
python poc.py
```

O bot lê a planilha definida em `CAMINHO_PLANILHA_ENTRADA`, executa as validações e, se houver divergências, gera `data/output/divergencias.xlsx`.

## Testes

Execute a suíte de testes:

```bash
pytest
```

Com relatório de cobertura (meta futura: 80%):

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

O relatório HTML ficará em `htmlcov/index.html`.

## Estrutura do projeto

```
conferencia-lotes-qualidade/
├── poc.py                  # Entry point
├── src/
│   ├── config.py           # Configuração via dotenv
│   ├── validacao.py        # Regras de negócio RN01–RN07
│   ├── base_referencia.py  # Consulta à base de lotes
│   └── relatorio.py        # Geração de divergencias.xlsx
├── tests/
│   └── test_validacao.py
├── data/
│   ├── samples/            # Planilhas de entrada
│   └── output/             # Relatórios gerados (ignorado no git)
└── .github/
    └── pull_request_template.md
```

## Licença

Uso interno — conferência de lotes de qualidade.
