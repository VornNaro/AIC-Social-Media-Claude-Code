# Backend image — Python 3.12 (host Python 3.14 is intentionally unused; see docs/01)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy source then install (hatchling needs the `app` package present to build).
# Dev extras (pytest, ruff, httpx) are included so the same image runs the tests.
COPY . .
RUN pip install --no-cache-dir ".[dev]" \
    && chmod +x docker-entrypoint.sh

EXPOSE 8000

# Entrypoint runs `alembic upgrade head` before the command, so the schema is
# always current on container start.
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
