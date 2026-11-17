# ─── Structify — Backend Dockerfile ───
# Works with Render, Railway, Fly.io, and any Docker-based host.

FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
# PyMuPDF, bcrypt, psycopg ship binary wheels, so no compiler is needed.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 APP_ENV=production
WORKDIR /app

RUN useradd --create-home --uid 10001 appuser
COPY --from=builder /install /usr/local
COPY --chown=appuser:appuser app ./app

# Uploads/outputs live in /tmp in production (see app/config.py).
USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health' % os.environ.get('PORT','8000'))"

# $PORT is injected by most PaaS providers. Secrets (JWT_SECRET_KEY, GEMINI_API_KEY,
# DATABASE_URL, CORS_ORIGINS) must be provided as environment variables.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips='*'"]
