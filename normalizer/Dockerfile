FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY normalizer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/
COPY normalizer/ /app/normalizer/

ENTRYPOINT ["python", "-m", "normalizer.main"]
CMD ["--kafka-brokers", "redpanda:9092", "--input-topic", "raw-events", "--output-topic", "flow-events", "--dlq-topic", "raw-events-dlq"]
