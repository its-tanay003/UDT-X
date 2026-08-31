FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pydantic>=2.7.0 kafka-python-ng>=2.2.3

COPY schema/    /app/schema/
COPY ingestion/ /app/ingestion/
COPY intel/     /app/intel/

ENV PYTHONPATH=/app

CMD ["python", "-m", "intel.main"]
