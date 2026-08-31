FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pydantic>=2.7.0 kafka-python-ng>=2.2.3

COPY schema/ /app/schema/
COPY ingestion/kafka_producer.py /app/ingestion/kafka_producer.py
COPY ingestion/__init__.py /app/ingestion/__init__.py
COPY engines/ /app/engines/

ENV PYTHONPATH=/app

CMD ["python", "-m", "engines.ddos.main"]
