# Backend image — Python 3.12 (host Python 3.14 is intentionally unused; see docs/01)
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy source then install (hatchling needs the `app` package present to build)
COPY . .
RUN pip install --no-cache-dir .

EXPOSE 8000

# Phase 1: run the API directly. Phase 2 will switch this to an entrypoint that
# runs `alembic upgrade head` before starting uvicorn (once migrations exist).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
