# Multi-stage Dockerfile: build frontend then run backend

# Stage 1: frontend build
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --production=false --no-audit --silent
COPY frontend/ ./
RUN npm run build --silent || true

# Stage 2: backend runtime
FROM python:3.11-slim
LABEL maintainer="Botong"
WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . /app

# Copy frontend build
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

ENV BOTO_PORT=5053 PYTHONUNBUFFERED=1
EXPOSE 5053

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${BOTO_PORT}/api/v1/health || exit 1

CMD ["gunicorn", "-c", "gunicorn_config.py", "web.app_factory:create_app"]
