FROM python:3.12-slim

WORKDIR /app

COPY features/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schema/ /app/schema/
COPY ingestion/ /app/ingestion/
COPY features/ /app/features/

ENV PYTHONPATH=/app

RUN groupadd -r udtx && useradd -r -g udtx -u 10001 -d /app -s /sbin/nologin udtx \
    && chown -R udtx:udtx /app

USER udtx

CMD ["python", "-m", "features.main"]

