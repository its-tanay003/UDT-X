FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    fastapi \
    "uvicorn[standard]" \
    pydantic>=2.7.0 \
    kafka-python-ng>=2.2.3 \
    redis>=5.0.0 \
    asyncpg>=0.29.0

COPY schema/         /app/schema/
COPY ingestion/      /app/ingestion/
COPY correlation/    /app/correlation/
COPY baseline/       /app/baseline/
COPY risk_engine/    /app/risk_engine/
COPY alert_manager/  /app/alert_manager/
COPY services/api/   /app/services/api/

ENV PYTHONPATH=/app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
