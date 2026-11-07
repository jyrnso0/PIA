FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./

FROM base AS tests
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY . .
CMD ["pytest", "--cov=src", "--cov-fail-under=80", "--cov-report=term-missing"]

FROM base AS app
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
EXPOSE 8000
CMD ["sh", "-c", "uvicorn --factory src.api.main:app_factory --host 0.0.0.0 --port ${PORT:-8000}"]
