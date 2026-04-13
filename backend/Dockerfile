# Stage 1: Builder — install Python dependencies
FROM python:3.12-slim AS builder

WORKDIR /build

COPY pyproject.toml .

RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime — copy installed packages and application code
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /install /usr/local

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
