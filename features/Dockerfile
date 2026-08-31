FROM python:3.12-slim

WORKDIR /app

COPY features/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/
COPY features/ /app/features/

ENV PYTHONPATH=/app

CMD ["python", "-m", "features.main"]
