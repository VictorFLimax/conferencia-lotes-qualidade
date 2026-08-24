# Cobertura Aula 24 (19/08/2026)

Comando:

```powershell
$env:PYTHONPATH = (Get-Location).Path
python -m pytest -m "unit or integration" --cov=src --cov-report=term-missing --cov-fail-under=80 --ignore=tests/e2e
```

Resultado: **46 passed**, 1 skipped, 1 xfailed, cobertura **89.73%** (≥ 80%).

| Módulo | Cover |
|--------|-------|
| src/artifacts.py | 100% |
| src/base_referencia.py | 100% |
| src/config.py | 54% |
| src/dispatcher.py | 94% |
| src/operational_indicators.py | **100%** (incluído, não omitido) |
| src/relatorio.py | 100% |
| src/validacao.py | 96% |

E2E (`tests/e2e`) exige servidor HTML local e não entra nesta evidência. `htmlcov/` é gerado localmente e permanece fora do Git.
