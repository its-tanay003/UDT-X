FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY ingestion/pcap_reader/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/

ENTRYPOINT ["python", "-m", "ingestion.pcap_reader.main"]
CMD ["--watch-dir", "/data/pcaps", "--kafka-brokers", "redpanda:9092"]
