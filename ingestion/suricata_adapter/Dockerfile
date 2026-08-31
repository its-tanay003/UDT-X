FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY ingestion/suricata_adapter/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/

CMD ["python", "-m", "ingestion.suricata_adapter.adapter"]
