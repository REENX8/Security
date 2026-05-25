# Build context MUST be the repository root (see docker-compose.yml) so the
# shared phish_features package can be copied into the image.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# --- install the shared feature package + backend deps ---
COPY pyproject.toml README.md ./
COPY phish_features ./phish_features
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -e . \
 && pip install --no-cache-dir -r backend/requirements.txt

# --- application code ---
COPY backend ./backend

# Models are mounted read-only at runtime: ./models -> /app/models
WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=5 \
    CMD python -c "import urllib.request,sys; \
sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
