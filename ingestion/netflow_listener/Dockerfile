FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY ingestion/netflow_listener/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/

EXPOSE 2055/udp
EXPOSE 4739/udp

ENTRYPOINT ["python", "-m", "ingestion.netflow_listener.server"]
CMD ["--host", "0.0.0.0", "--port", "2055", "--kafka-brokers", "redpanda:9092"]
