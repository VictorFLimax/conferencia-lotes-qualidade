FROM python:3.11-slim

LABEL maintainer="victor@axacademy"
LABEL description="Bot Auditor de Acessos v1.0"

WORKDIR /app

# Copiar requirements primeiro (cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o projeto
COPY . .

# Criar usuário não-root (segurança)
RUN adduser --disabled-password --gecos '' botuser && \
    chown -R botuser:botuser /app
USER botuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Rodar como módulo Python (funciona com src/)
CMD ["python", "-m", "src.main"]
