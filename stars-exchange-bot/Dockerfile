FROM python:3.12-slim

WORKDIR /app

RUN mkdir -p /app/data

COPY pyproject.toml README.md ./
COPY app ./app
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./

RUN pip install --no-cache-dir .

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
