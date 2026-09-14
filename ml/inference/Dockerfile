FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pydantic>=2.7.0 kafka-python-ng>=2.2.3 numpy>=1.26.0

COPY schema/    /app/schema/
COPY ingestion/ /app/ingestion/
COPY ml/        /app/ml/

ENV PYTHONPATH=/app

RUN groupadd -r udtx && useradd -r -g udtx -u 10001 -d /app -s /sbin/nologin udtx \
    && chown -R udtx:udtx /app

USER udtx

CMD ["python", "-m", "ml.inference.main"]

