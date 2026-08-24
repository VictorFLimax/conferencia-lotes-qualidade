FROM python:3.11-slim

WORKDIR /app

COPY api_ml/requirements.txt /app/api_ml/requirements.txt
RUN pip install --no-cache-dir -r /app/api_ml/requirements.txt

COPY api_ml /app/api_ml
COPY models /app/models

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV ML_MODEL_PATH=/app/models/classificador_lotes.pkl

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "api_ml.main:app", "--host", "0.0.0.0", "--port", "8000"]
