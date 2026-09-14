FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir pydantic>=2.7.0 kafka-python-ng>=2.2.3 redis>=5.0.0 psycopg2-binary>=2.9.9

COPY schema/    /app/schema/
COPY baseline/  /app/baseline/

ENV PYTHONPATH=/app

RUN groupadd -r udtx && useradd -r -g udtx -u 10001 -d /app -s /sbin/nologin udtx \
    && chown -R udtx:udtx /app

USER udtx

CMD ["python", "-m", "baseline.main"]

