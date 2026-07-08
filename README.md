# Bot de Conferência de Lotes

Bot em Python para conferência automatizada de lotes de qualidade, com arquitetura modular preparada para regras de negócio (RN01–RN07), geração de relatórios e cobertura de testes.

## Funcionalidades implementadas

### Issue #1 — Validação de estrutura e campos obrigatórios

O módulo `src/validacao.py` expõe as funções abaixo:

| Função | Descrição |
|--------|-----------|
| `valida_estrutura(dados)` | Verifica se a planilha possui as colunas esperadas. **Não interrompe o fluxo** se alguma coluna estiver ausente — retorna um `ResultadoEstrutura` com o diagnóstico. |
| `valida_campos_obrigatorios(registro)` | Valida se os campos obrigatórios de um registro estão preenchidos. Lança `CamposObrigatoriosVaziosError` quando detecta valores vazios. |

**Colunas esperadas na planilha de entrada:**

- `lote_id`
- `produto`
- `linha`
- `turno`
- `status`
- `responsavel`

**Exceções customizadas:**

- `ErroValidacao` — base para erros de validação
- `CamposObrigatoriosVaziosError` — lista os campos vazios em `campos_vazios`

**Exemplo de uso:**

```python
import pandas as pd
from src.validacao import valida_estrutura, valida_campos_obrigatorios

df = pd.read_excel("data/samples/planilha_lotes.xlsx")

# Verifica estrutura sem falhar se faltar coluna
resultado = valida_estrutura(df)
print(resultado.colunas_ausentes)  # ex.: ['turno'] se a coluna não existir

# Valida campos obrigatórios de cada linha
for _, linha in df.iterrows():
    valida_campos_obrigatorios(linha)  # levanta erro se algum campo estiver vazio
```

### Em desenvolvimento

- Regras de negócio RN01–RN07 (assinaturas prontas, lógica pendente)
- Integração completa no fluxo do `poc.py`
- Geração automática de `divergencias.xlsx` a partir das validações da Issue #1

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

5. Coloque a planilha de amostra (25 registros) em `data/samples/planilha_lotes.xlsx`, contendo as colunas listadas acima.

## Execução

Com o ambiente virtual ativo e o `.env` configurado:

```bash
python poc.py
```

O bot lê a planilha definida em `CAMINHO_PLANILHA_ENTRADA`, executa as validações e, se houver divergências, gera `data/output/divergencias.xlsx`.

## Testes

Execute a suíte completa:

```bash
pytest
```

Execute apenas os testes da Issue #1 (estrutura e campos obrigatórios):

```bash
pytest tests/test_validacao.py::TestValidaEstrutura tests/test_validacao.py::TestValidaCamposObrigatorios -v
```

Com relatório de cobertura (meta futura: 80%):

```bash
pytest --cov=src --cov-report=term-missing --cov-report=html
```

O relatório HTML ficará em `htmlcov/index.html`.

### Cenários cobertos pelos testes

- Estrutura completa da planilha
- Colunas ausentes (sem exceção)
- DataFrame vazio
- Cada campo obrigatório vazio ou ausente (parametrizado)
- Valores considerados vazios: `None`, `""`, espaços em branco e `NaN`
- Múltiplos campos vazios simultaneamente

## Estrutura do projeto

```
conferencia-lotes-qualidade/
├── poc.py                  # Entry point
├── src/
│   ├── config.py           # Configuração via dotenv
│   ├── validacao.py        # Validação (Issue #1) + regras RN01–RN07
│   ├── base_referencia.py  # Consulta à base de lotes
│   └── relatorio.py        # Geração de divergencias.xlsx
├── tests/
│   └── test_validacao.py   # Testes da Issue #1 e do boilerplate
├── data/
│   ├── samples/            # Planilhas de entrada
│   └── output/             # Relatórios gerados (ignorado no git)
└── .github/
    └── pull_request_template.md
```

## Histórico de versões

Consulte o [CHANGELOG.md](CHANGELOG.md) para o registro detalhado de mudanças.

| Versão | Destaques |
|--------|-----------|
| v0.1.0 | Boilerplate inicial do projeto |
| v0.2.0 | Issue #1: `valida_estrutura()`, `valida_campos_obrigatorios()` e testes |

## Licença

Uso interno — conferência de lotes de qualidade.
